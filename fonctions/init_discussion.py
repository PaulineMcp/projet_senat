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

from fonctions.fonctions_scrapping_cleaning.fonctions_cleaning import get_id_disc, get_session, get_id_article, get_id_bloc_article, get_id_amdt, is_ss_amdt, get_info_from_id, turn_into_content, turn_into_ordre, get_url_article, get_bloc_article
from fonctions.fonctions_scrapping_cleaning.fonctions_scrapping import get_content_page, get_hash, get_tab_list, get_disc_info, parsing_line, get_avis_gouv, get_avis_com
from fonctions.upsert_bdd import upsert_df
from utils import get_db

###############     DISCUSSION      ###############
# Récupérer les infos principales de la discussion

# Initialiser la discussion
def fetch_disc(url : str, inputs : dict) -> pd.DataFrame :
        """Récupère les infos d'une discussion et l'ajoute à la BDD"""

        # Récupère les infos principales du ppl/pjl
        infos = get_disc_info(url)
        titre_disc_long = inputs["titre"] + " - " + infos["com_seance"] + " - " + infos["lecture"] + " - " + infos["session"]
        nb_parties = len(get_tab_list(url))
        last_hash = get_hash(url)
        is_archived = 0
        disc = [{"id_disc" : infos["id_disc"],
         "url_disc" : inputs["url"],
         "titre_disc" : inputs["titre"],
         "titre_disc_long" : titre_disc_long,
         "nb_parties" : nb_parties,
         "com_seance" : infos["com_seance"],
         "lecture" : infos["lecture"],
         "last_hash" : last_hash,
         "lien_note" : inputs["lien_note"].strip(),
         "lien_dossier" : inputs["lien_dossier"].strip(),
         "url_txt" : inputs["url_txt"],
         "is_archived" : is_archived
         }]
        df = pd.DataFrame(disc)
        print("Infos de la discussion récupérés")
        return(df)

def init_disc(url : str, inputs : str) -> None :
    """Récupère les infos d'une discussion et l'ajoute à la BDD"""
    df = fetch_disc(url, inputs)
    upsert_df("discussion", df, "id_disc")
    print("Infos de la discussion ajoutées à la BDD")

###################


# Fonction pour récupérer les infos dans la page
def fetch_content(id_disc : str) -> list :
    """Récupère le contenu d'une page. Renvoie une liste de DataFrame"""
    df_list = []
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
            if titre is None :
                titre = "Première partie"
            else :
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
    df_list.append(df_parties)
    df_list.append(df_ordre)
    df_list.append(df_content)
    print("Contenu, parties et ordre récupérés")
    return(df_list)

#def send_content_to_bdd(df_list : list) -> None :
#    """Prend une liste de DataFrame. Les initialise en BDD"""
#    df_parties, df_ordre, df_content = df_list
#    with get_db() as conn:
#        df_parties.to_sql("parties", conn, if_exists="append", index=False)
#        df_content.to_sql("amdts", conn, if_exists="append", index=False)
#        df_ordre.to_sql("ordre_examen", conn, if_exists="append", index=False)
#        print("Contenu, ordre et parties initialisés")

def init_content(id_disc : str ) -> None : 
    """Récupère le contenu d'une page et l'envoie en BDD"""
    df_parties, df_ordre, df_content = fetch_content(id_disc)

    # Ordre imposé par les clés étrangères : parties → amdts → ordre_examen
    a_inserer = [
        ("parties", df_parties, "id_partie"),
        ("amdts", df_content, "id_amdt"),
        ("ordre_examen", df_ordre, "id_amdt"),
    ]

    #with get_db() as conn:
    for table, df, cle in a_inserer:
        upsert_df(table, df, cle)
    #send_content_to_bdd(df_list)
    print("Contenu, ordre et parties ajoutés")

#fetch_content("2024-2025-SCE-62")
#fetch_content("2025-2026-SCE-138")
#fetch_content("2025-2026-COM-689")
#fetch_content("2026-2027-SCE-138")


###############     ARTICLES        ###############

def fetch_articles_from_texte(id_disc : str) -> pd.DataFrame :
    """Récupère tous les articles identifiés grâce aux URL des textes de loi. Renvoie un df""" 
    # Récupère l'url du texte
    url_articles = get_info_from_id(id_disc, "url_txt")
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
    return(df)

#fetch_articles_from_texte("2024-2025-SCE-62")
#fetch_articles_from_texte("2025-2026-SCE-138")
#fetch_articles_from_texte("2025-2026-COM-689")
#fetch_articles_from_texte("2026-2027-SCE-138")



def fetch_articles_from_amdts(id_disc : str) -> pd.DataFrame :
    """Récupère tous les articles identifiés grâce aux amendements récupérés. Renvoie un df"""
    with get_db() as conn:
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
    return(df)

#fetch_articles_from_amdts("2024-2025-SCE-62")
#fetch_articles_from_amdts("2025-2026-SCE-138")
#fetch_articles_from_amdts("2025-2026-COM-689")
#fetch_articles_from_amdts("2026-2027-SCE-138")  

#def send_article_to_bdd(df : pd.DataFrame) -> None:
#    """Envoies les articles en BDD"""
#    with get_db() as conn:
#        df.to_sql("articles", conn, if_exists="append", index = False)
#    print("Articles ajoutés dans la bdd")

def init_articles(id_disc : str) -> None:
    """Récupère tous les articles et les envoies en BDD"""
    df_art_from_amdts = fetch_articles_from_amdts(id_disc)
    df_art_from_txt = fetch_articles_from_texte(id_disc)
    df = pd.concat([df_art_from_amdts,df_art_from_txt])
    df["article"] = df["article"].map(lambda s: " ".join(unicodedata.normalize("NFKC", s).split()))
    df = df.drop_duplicates(subset=["id_bloc_article","bloc_article","bloc","id_article","id_disc"], keep="first")
    #send_article_to_bdd(df)
    upsert_df("articles", df, "id_article")
    print("Articles ajoutés")

#fetch_all_articles("2024-2025-SCE-62")
#fetch_all_articles("2025-2026-SCE-138")
#fetch_all_articles("2025-2026-COM-689")
#fetch_all_articles("2026-2027-SCE-138")   

############        AVIS        ##############

def fetch_avis(id_disc) -> pd.DataFrame: # on initialise les avis pour un ppl / pjl
    """Récupère les avis gouv et com pour chaque amendement. Renvoie un df"""
    # On récupère la liste de tous les amdts pour une disc
    with get_db() as conn:
        
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
    print("Avis gouv et com récupérés")
    return(df)

#def send_avis_to_bdd(df : pd.DataFrame) -> None:
#    """Envoi en bdd les avis gouv et com"""
#    with get_db() as conn:
#        df.to_sql("avis", conn, if_exists="append", index = False)
#    print("Avis gouv et com ajoutés à la BDD")

def init_avis(id_disc : str) -> None:
    """Récupère les avis et les initialise en BDD"""
    df = fetch_avis(id_disc)
    #send_avis_to_bdd(df)
    upsert_df("avis", df, "id_amdt")

#fetch_avis("2024-2025-SCE-62")
#fetch_avis("2025-2026-SCE-138")
#fetch_avis("2025-2026-COM-689")
#fetch_avis("2026-2027-SCE-138")  

###############     REMPLISSAGE AP DES AMDTS        ###############

def init_remplissage_amdts(id_disc : str) -> None :
    """Initialise un objet vide, un com vide et une proposition de vote vide pour chaque amdt""" 
    with get_db() as conn:

    # On récupère la liste de tous les amdts pour une disc
        df = pd.read_sql("""
            SELECT DISTINCT amdts.id_amdt
            FROM amdts
            LEFT JOIN parties
                ON parties.id_partie = amdts.id_partie
            LEFT JOIN discussion
                ON discussion.id_disc = parties.id_disc
            WHERE discussion.id_disc = ?
            AND NOT EXISTS (
                SELECT 1
                FROM remplissage_ap_amdt r
                WHERE r.id_amdt = amdts.id_amdt
            )
                        """,
                        conn,
                        params=(id_disc,))
        # Rajouter les objets et commentaires actuellement vide
        df["objet"] = "À compléter"
        df["com"] = ""
        df["proposition_vote_amdt"] = "À définir"            
        df.to_sql("remplissage_ap_amdt", conn, if_exists="append", index = False)
    print("Initialisation des objets, commentaires et prop.vote amdt") 

#init_remplissage_amdts("2024-2025-SCE-62")
#init_remplissage_amdts("2025-2026-SCE-138")
#init_remplissage_amdts("2025-2026-COM-689")
#init_remplissage_amdts("2026-2027-SCE-138")

###############     REMPLISSAGE AP DES ARTICLES     ###############

def init_remplissage_articles(id_disc : str) -> None : 
    """Initialise un résumé et une proposition de vote vide pour chaque article"""
    with get_db() as conn:
        # On récupère la liste de tous les articles pour une disc
        df = pd.read_sql("""
           SELECT DISTINCT articles.id_article
            FROM articles
            WHERE articles.id_disc = ?
            AND NOT EXISTS (
                SELECT 1
                FROM remplissage_ap_article r
                WHERE r.id_article = articles.id_article
                        """,
                        conn,
                        params=(id_disc,))
        # Rajouter les propositions de vote
        df["resume_article"] = None
        df["proposition_vote_article"] = None
        df.to_sql("remplissage_ap_article", conn, if_exists="append", index = False)
    print("Initialisation des résumés et prop.vote articles")


#init_remplissage_articles("2024-2025-SCE-62")
#init_remplissage_articles("2025-2026-SCE-138")
#init_remplissage_articles("2025-2026-COM-689")
#init_remplissage_articles("2026-2027-SCE-138")

def vide(x):
    return None if pd.isna(x) else x