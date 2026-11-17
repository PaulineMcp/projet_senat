""" 
    Initialiser une discussion 

    - get_disc_info : récupérer les infos principales d'une discussion (com ou seance, id, lecture, session etc...)
    - fetch_disc : récupérer l'ensemble des infos d'une discussion
    - fetch_articles : récupérer l'ensemble des infos des articles d'une discussion
    - fetch_ordre_amdts : récupérer l'ordre des amendements
    - fetch_content_amdts : récupérer le contenu des amendements
    - fetch_avis : récupérer le contenu des avis des amendements
    - init_remplissage_amdts : initialisation de l'objet, des commentaires et de la proposition de vote sur l'amendement rempli par l'AP
    - init_remplissage_ap : initialisation du résumé et de la proposition de vote sur l'article rempli par l'AP

    """

###############     IMPORTS     ###############
###############     IMPORTS LIBRAIRIES ET FONCTIONS     ###############
from pathlib import Path
import sqlite3
import streamlit as st 
import sys
import hashlib
import re
import requests
from bs4 import BeautifulSoup
import pandas as pd
import unicodedata

# Constantes
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fonctions.fonctions_cleaning import get_id_disc, get_session, get_id_article, get_id_bloc_article, get_id_amdt, is_ss_amdt, get_info_from_id, turn_into_content, turn_into_ordre, get_url_article, get_bloc_article
from fonctions.fonctions_scrapping import get_content_page, get_hash, get_tab_list, get_disc_info, parsing_line, get_avis_gouv, get_avis_com
#get_avis_com, get_avis_gouv, get_tab_content
from utils import get_conn

###############     DISCUSSION      ###############
# Récupérer les infos principales de la discussion

# Initialiser la discussion
def fetch_disc(url : str, inputs : dict) :

        # Récupère les infos principales du ppl/pjl
        infos = get_disc_info(url)

        titre_disc_long = inputs["titre"] + " - " + infos["com_seance"] + " - " + infos["lecture"] + " - " + infos["session"]
        nb_parties = len(get_tab_list(url))
        last_hash = get_hash(url)
        is_archived = 0
        
        # Rajoute la discussion aux discussions existantes
        conn = get_conn()

        
        conn.execute(
                """
                INSERT INTO discussion
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                infos["id_disc"],
                inputs["url"],
                inputs["titre"],
                titre_disc_long,
                nb_parties,
                infos["com_seance"],
                infos["lecture"],
                last_hash,
                inputs["lien_note"].strip(),
                inputs["lien_dossier"].strip(),
                inputs["url_txt"],
                is_archived
                ),
        )
        print("Discussion ajoutée à la BDD")
        conn.commit()
        conn.close()

###################

# Fonction pour récupérer les infos dans la page
def fetch_content(id_disc : str) :
    soup = get_content_page(get_info_from_id(id_disc, "url_disc"))
    nb_parties = get_info_from_id(id_disc, "nb_parties")
    df_parties = []

    if nb_parties == 1 :

        df_parties.append({
            "id_partie" : id_disc + "-p1", # pour "partie unique"
            "id_disc" : id_disc,
            "titre_partie" : "Première et unique partie",
            "ordre_partie" : 1
            })      

        tbody = soup.find("tbody")
        lines = tbody.find_all("tr")

        df = []
        for line in lines :
            parsed_line = parsing_line(line)
            df.append(parsed_line)
        df = pd.DataFrame(df)
        df_ordre = turn_into_ordre(df,id_disc,1)
        df_content = turn_into_content(df,id_disc,1)        
 
    else :
        tables = soup.find_all("table")

        df_ordre = pd.DataFrame(columns = ["id_amdt", "id_partie","ordre_examen_in_partie"])
        df_content = pd.DataFrame(columns = ["id_amdt","id_article","id_partie","amdt","is_ss_amdt","lien_amdt","auteur","url_senateur","sort"])
        ordre = 1

        for table in tables :
            df_tmp = []
            # Récupérer le titre de la partie
            titre = table.find_previous("h5")
            titre = titre.text.strip()
            df_parties.append({
                "id_partie" : id_disc + "-p" + str(ordre),
                "id_disc" : id_disc,
                "titre_partie" : titre.capitalize(),
                "ordre_partie" : ordre
                })
    
            # Récupérer les amendements et leur contenu par partie
            tbody = table.find("tbody")
            lines = tbody.find_all("tr")
            for line in lines :
                parsed_line = parsing_line(line)
                df_tmp.append(parsed_line)

            df_tmp = pd.DataFrame(df_tmp)

            df_ordre_tmp = turn_into_ordre(df_tmp, id_disc, ordre)
            df_content_tmp = turn_into_content(df_tmp, id_disc, ordre)

            df_ordre = pd.concat([df_ordre, df_ordre_tmp], ignore_index=True, sort=False)
            df_content = pd.concat([df_content, df_content_tmp], ignore_index=True, sort=False) 
             
            ordre += 1

    df_parties = pd.DataFrame(df_parties) 
    df_ordre["ordre_examen_abs"] = df_ordre.index
    # Renvoyer le résultat en base de données
    conn = get_conn()
    df_parties.to_sql("parties", conn, if_exists="append", index = False)
    df_ordre.to_sql("ordre_examen", conn, if_exists="append", index = False)
    df_content.to_sql("amdts", conn, if_exists="append", index = False)
    conn.commit()
    print("Contenu, ordre et parties ajoutés")
    conn.close()

#fetch_content("2024-2025-SCE-62")
#fetch_content("2025-2026-SCE-138")
#fetch_content("2025-2026-COM-689")
#fetch_content("2026-2027-SCE-138")


###############     ARTICLES        ###############

def fetch_articles_from_texte(id_disc : str) : 
    # Récupère l'url du texte
    url_articles = get_info_from_id(id_disc, "url_txt")
    #print(url_articles)
    soup = get_content_page(url_articles)
    articles = soup.find_all("p", {"class": "TCNumArticle"})

    # Parsing
    df = []
    for article in articles :
        try :
            lien_article = url_articles + "#" + article.find("a")["id"]
        except : 
            lien_article = "Pas de lien vers l'article"

        article_texte = re.sub(r"\([^()]*\)", "", article.text.strip()).strip()
        id_article = id_disc + "-" + get_id_article(article_texte)
        id_bloc_article = id_disc + "-" + get_id_bloc_article(article_texte)
        df.append({
            "id_bloc_article" : id_bloc_article,
            "bloc_article" : get_bloc_article(article_texte),
            "bloc" : get_id_bloc_article(article_texte),
            "id_article" : id_article,
            "article" : article_texte,
            "lien_article" : lien_article,
            "id_disc" : id_disc
        })
    df = pd.DataFrame(df).drop_duplicates()
    print(df)
    return(df)


#fetch_articles_from_texte("2024-2025-SCE-62")
#fetch_articles_from_texte("2025-2026-SCE-138")
#fetch_articles_from_texte("2025-2026-COM-689")
#fetch_articles_from_texte("2026-2027-SCE-138")

def fetch_articles_from_amdts(id_disc : str) :
    conn = get_conn()
    requete = f"""SELECT amdts.id_article, amdts.article, amdts.lien_article
                FROM amdts 
                LEFT JOIN parties
                ON parties.id_partie = amdts.id_partie
                LEFT JOIN discussion
                ON discussion.id_disc = parties.id_disc
                WHERE discussion.id_disc = '{id_disc}'"""
    df = pd.read_sql(requete, conn,).drop_duplicates()
    df["id_bloc_article"] = id_disc + "-" + df["article"].apply(lambda x : get_id_bloc_article(x)) 
    df["bloc_article"] = df["article"].apply(lambda x : get_bloc_article(x))
    df["id_disc"] = id_disc
    df["bloc"] = df["article"].apply(lambda x : get_id_bloc_article(x))
    df = df[["id_bloc_article", "bloc_article", "bloc","id_article", "article","lien_article","id_disc"]]
    print(df)
    return(df)

#fetch_articles_from_amdts("2024-2025-SCE-62")
#fetch_articles_from_amdts("2025-2026-SCE-138")
#fetch_articles_from_amdts("2025-2026-COM-689")
#fetch_articles_from_amdts("2026-2027-SCE-138")  

def fetch_all_articles(id_disc : str) :
    df_art_from_amdts = fetch_articles_from_amdts(id_disc)
    df_art_from_txt = fetch_articles_from_texte(id_disc)
    df = pd.concat([df_art_from_amdts,df_art_from_txt])
    df["article"] = df["article"].map(lambda s: " ".join(unicodedata.normalize("NFKC", s).split()))
    df = df.drop_duplicates(subset=["id_bloc_article","bloc_article","bloc","id_article","id_disc"], keep="first")

    # Renvoyer en bdd
    conn = get_conn()
    df.to_sql("articles", conn, if_exists="append", index = False)
    conn.commit()
    print("Articles ajoutés dans la bdd")
    conn.close()

fetch_all_articles("2024-2025-SCE-62")
fetch_all_articles("2025-2026-SCE-138")
fetch_all_articles("2025-2026-COM-689")
fetch_all_articles("2026-2027-SCE-138")   

############        AVIS        ##############

def fetch_avis(id_disc): # on initialise les avis pour un ppl / pjl
    
    conn = get_conn()

    # On récupère la liste de tous les amdts pour une disc
    df = pd.read_sql("""
                    SELECT amdts.id_amdt, amdts.lien_amdt
                    FROM amdts 
                    LEFT JOIN parties
                    ON parties.id_partie = amdts.id_partie
                    LEFT JOIN discussion
                    ON discussion.id_disc = parties.id_disc
                    WHERE discussion.id_disc = ?
                    """,
                    conn,
                    params = (id_disc,))

    com_ou_seance = get_info_from_id(id_disc, "com_seance")
    # Récupérer les avis gouv et com
    df["avis_com"] = "Pas d'avis" if com_ou_seance == "Commission" else df["lien_amdt"].apply(lambda x : get_avis_com(x))
    df["avis_gouv"] = "Pas d'avis" if com_ou_seance == "Commission" else df["lien_amdt"].apply(lambda x : get_avis_gouv(x))
    df = df[["id_amdt","avis_gouv", "avis_com"]]
    print(df)
    df.to_sql("avis", conn, if_exists="append", index = False)
    conn.commit()
    print("Avis ajoutés à la BDD")
    conn.close()

#fetch_avis("2024-2025-SCE-62")
#fetch_avis("2025-2026-SCE-138")
#fetch_avis("2025-2026-COM-689")
#fetch_avis("2026-2027-SCE-138")  

###############     REMPLISSAGE AP DES AMDTS        ###############

def init_remplissage_amdts(id_disc) : 
    conn = get_conn()
    # On récupère la liste de tous les amdts pour une disc
    df = pd.read_sql("""
                    SELECT amdts.id_amdt         
                    FROM amdts 
                    LEFT JOIN parties
                    ON parties.id_partie = amdts.id_partie
                    LEFT JOIN discussion
                    ON discussion.id_disc = parties.id_disc
                    WHERE discussion.id_disc = ?
                    """,
                    conn,
                    params=(id_disc,))
    # Rajouter les objets et commentaires actuellement vide
    df["objet"] = "À compléter"
    df["com"] = ""
    df["proposition_vote_amdt"] = "À définir"            
    df.to_sql("remplissage_ap_amdt", conn, if_exists="append", index = False)
    print("Initialisation des commentaires amdt")
    conn.commit()
    conn.close() 

#init_remplissage_amdts("2024-2025-SCE-62")
#init_remplissage_amdts("2025-2026-SCE-138")
#init_remplissage_amdts("2025-2026-COM-689")
#init_remplissage_amdts("2026-2027-SCE-138")

###############     REMPLISSAGE AP DES ARTICLES     ###############

def init_remplissage_articles(id_disc) : 
    conn = get_conn()

    # On récupère la liste de tous les articles pour une disc
    df = pd.read_sql("""
                    SELECT id_article
                    FROM articles
                    WHERE id_disc = ?
                    """,
                    conn,
                    params=(id_disc,))
    # Rajouter les propositions de vote
    df["resume_article"] = None
    df["proposition_vote_article"] = None
    df.to_sql("remplissage_ap_article", conn, if_exists="append", index = False)
    print("Initialisation des commentaires articles")
    conn.commit()
    conn.close()

#init_remplissage_articles("2024-2025-SCE-62")
#init_remplissage_articles("2025-2026-SCE-138")
#init_remplissage_articles("2025-2026-COM-689")
#init_remplissage_articles("2026-2027-SCE-138")
   