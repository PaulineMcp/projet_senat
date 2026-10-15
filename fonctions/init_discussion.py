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

 # Chemin de la racine pour trouver les autres fichiers
import sys
from pathlib import Path
import pandas as pd

# Constantes
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Imports des fonctions
from fonctions.fonctions_cleaning import commission_ou_sceance
from fonctions.fonctions_cleaning import get_id_disc
from fonctions.fonctions_scrapping import get_content_page
from fonctions.fonctions_scrapping import get_lecture
from fonctions.fonctions_cleaning import get_session
from fonctions.fonctions_cleaning import get_id_article
from fonctions.fonctions_cleaning import get_id_bloc_article
from fonctions.fonctions_scrapping import get_tab
from fonctions.fonctions_scrapping import clean_tab_ordre
from fonctions.fonctions_cleaning import get_id_amdt
from fonctions.fonctions_cleaning import is_ss_amdt
from fonctions.fonctions_scrapping import clean_amdt_info
from fonctions.fonctions_scrapping import get_avis_com
from fonctions.fonctions_scrapping import get_avis_gouv
from utils import get_conn

###############     DISCUSSION      ###############

# Récupérer les infos principales de la discussion
def get_disc_info(url): # URL de la discussion                 
    com_seance = commission_ou_sceance(url)
    id_disc = get_id_disc(url)
    lecture = get_lecture(get_content_page(url))
    session = get_session(url)
    

    raw_com_seance = "COM" if com_seance == "Commission" else "SCE"
    id_disc = session + "-" + raw_com_seance + "-" + id_disc
    return{
            "com_seance" : com_seance,
            "id_disc" : id_disc,
            "lecture" : lecture,
            "session" : session 
    }

# Initialiser la discussion
def fetch_disc(url, inputs) :
        # Récupère les infos principales du ppl/pjl
        infos = get_disc_info(url)

        id_disc = infos["id_disc"]
        com_seance = infos["com_seance"]
        lecture = infos["lecture"]
        session = infos["session"]

        # Récupère les infos sur le ppj/ppl qui viennent des inputs
        titre_disc = inputs["titre"]
        url_disc = inputs["url"]
        lien_note = inputs["lien_note"]
        lien_dossier = inputs["lien_dossier"]
        url_articles = inputs["url_articles"]

        titre_disc_long = titre_disc + " - " + com_seance + " - " + lecture + " - " + session

        # rajoute la discussion aux discussions existantes
        conn = get_conn()
        conn.execute(
                """
                INSERT INTO discussion
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                id_disc,
                url_disc,
                titre_disc,
                titre_disc_long,
                com_seance,
                lecture,
                lien_note.strip(),
                lien_dossier.strip(),
                url_articles,
                ),
        )
        conn.commit()
        conn.close()

###############     ARTICLES        ###############

def fetch_articles(id_disc) :

    # On récupère l'url du texte
    conn = get_conn()
    # On récupère l'url du texte de la disc
    df = pd.read_sql("""
                    SELECT url_articles
                    FROM discussion
                    WHERE id_disc = ?
                    """,
                    conn,
                    params=(id_disc,))

    url_articles = df.iloc[0, 0]
    soup = get_content_page(url_articles)
    articles = soup.find_all("p", {"class": "TCNumArticle"})

    df_articles = []
    for article in articles :
        article = article.text.strip()
        id_bloc_article = get_id_bloc_article(article, id_disc)
        id_article = get_id_article(article, id_disc)
        row = {
            "id_article" : id_article,
            "id_bloc_article" : id_bloc_article,
            "id_disc" : id_disc,
            "article" : article
        }
        df_articles.append(row)
    
    df_articles = pd.DataFrame(df_articles)
    df_articles["ordre_article"] = df_articles.index
    print(df_articles)

    # Renvoyer le résultat en base de données
    df_articles.to_sql("articles", conn, if_exists="append", index = False)
    conn.commit()
    conn.close()

## Fonction pour intialiser l'ordre d'examen des amendements d'un seul pjl
def fetch_ordre_amdts(url) : # on lui passe l'url d'un unique pjl
    tab = get_tab(url)
    df = clean_tab_ordre(tab)
    df["session"] = get_session(url)    
    df["id_disc"] = get_id_disc(url)
    df["com_seance"] = commission_ou_sceance(url)
    df["id_amdt"] = df["amdt"].apply(lambda x : get_id_amdt(x))
    df["raw_com_seance"] = "COM" if df["com_seance"][0] == "Commission" else "SCE"

    df["id_disc"] = df["session"] + "-" + df["raw_com_seance"] + "-" + df["id_disc"]
    df["id_article"] = df.apply(lambda x: get_id_article(x.article, x.id_disc), axis=1)
    df["id_amdt"] = df["id_article"] + "-"+ df["id_amdt"]
    df["ordre_amdt"] = df.index
    df = df[["ordre_amdt","id_amdt"]]

    # Renvoyer les nouvelles données dans la table ordre_examen       
    conn = get_conn()
    df.to_sql("ordre_examen", conn, if_exists="append", index = False)
    conn.commit()
    conn.close()  

## Fonction pour intialiser le contenu des amendements d'un seul pjl
def fetch_content_amdts(url) :
        
        # Récupère la liste des amdts dans ordre_examen
        tab = get_tab(url)
        df = clean_amdt_info(tab)
        df["session"] = get_session(url)
        df["id_disc"] = get_id_disc(url)
        df["com_seance"] = commission_ou_sceance(url)
        racine_lien = "https://www.senat.fr/amendements/commissions/" if df["com_seance"][0] == "Commission" else "https://www.senat.fr/amendements/"
        df["lien_amdt"] = racine_lien + df["session"] + "/" + df["id_disc"] + "/" + df["lien_amdt"]
        df["raw_com_seance"] = "COM" if df["com_seance"][0] == "Commission" else "SCE"
        df["id_disc"] = df["session"] + "-" + df["raw_com_seance"] + "-" + df["id_disc"]

        # Génération de la clé
        df["id_article"] = df.apply(lambda x: get_id_article(x.article, x.id_disc), axis=1)
        df["id_bloc_article"] = df.apply(lambda x: get_id_bloc_article(x.article, x.id_disc), axis=1)
        df["id_amdt"] = df["amdt"].apply(lambda x : get_id_amdt(x))
        df["id_amdt"] = df["id_article"] + "-"+ df["id_amdt"]

        df["is_ss_amdt"] = df["amdt"].apply(lambda x: is_ss_amdt(x))

        df = df[["id_amdt","id_article","id_bloc_article","amdt","is_ss_amdt","lien_amdt","url_senateur","sort"]]
        # Renvoyer les nouvelles données dans la table ordre_examen       
        conn = get_conn()
        df.to_sql("amdts", conn, if_exists="append", index = False)
        conn.commit()
        conn.close()


############        AVIS        ##############

def fetch_avis(id_disc): # on initialise les avis pour un ppl / pjl
    
    conn = get_conn()

    # On récupère la liste de tous les amdts pour une disc
    df = pd.read_sql("""
                    SELECT *
                    FROM amdts 
                    LEFT JOIN articles
                    ON amdts.id_bloc_article = articles.id_bloc_article
                    LEFT JOIN discussion
                    ON articles.id_disc = discussion.id_disc
                    WHERE discussion.id_disc = ?
                    """,
                    conn,
                    params = (id_disc,))

    com_ou_seance = df["com_seance"].iloc[0] == "Commission"

    # Récupérer les avis gouv et com   
    df["avis_com"] = "Pas d'avis" if com_ou_seance == True else df["lien_amdt"].apply(lambda x : get_avis_com(x))
    df["avis_gouv"] = "Pas d'avis" if com_ou_seance == True else df["lien_amdt"].apply(lambda x : get_avis_gouv(x))
    
    df = df[["id_amdt","avis_gouv", "avis_com"]]
    df.to_sql("avis", conn, if_exists="append", index = False)
    conn.commit()
    conn.close()

###############     REMPLISSAGE AP DES AMDTS        ###############

def init_remplissage_amdts(id_disc) : 
    conn = get_conn()
    # On récupère la liste de tous les amdts pour une disc
    df = pd.read_sql("""
                    SELECT amdts.id_amdt         
                    FROM amdts 
                    LEFT JOIN articles
                    ON amdts.id_bloc_article = articles.id_bloc_article
                    LEFT JOIN discussion
                    ON articles.id_disc = discussion.id_disc
                    WHERE discussion.id_disc = ?
                    """,
                    conn,
                    params=(id_disc,))

    # Rajouter les objets et commentaires actuellement vide
    df["objet"] = "A compléter"
    df["com"] = ""
    df["proposition_vote_amdt"] = "A définir"            
    df.to_sql("remplissage_ap_amdt", conn, if_exists="append", index = False)
    conn.commit()
    conn.close() 

###############     REMPLISSAGE AP DES ARTICLES     ###############

def init_remplissage_articles(id_disc) : 
    conn = get_conn()

    # On récupère la liste de tous les articles pour une disc
    df = pd.read_sql("""
                    SELECT articles.id_article
                    FROM articles
                    LEFT JOIN discussion
                    ON discussion.id_disc = articles.id_disc
                    WHERE discussion.id_disc = ?
                    """,
                    conn,
                    params=(id_disc,))
    
    # Rajouter les propositions de vote
    df["resume_article"] = None
    df["proposition_vote_article"] = None
    df.to_sql("remplissage_ap_article", conn, if_exists="append", index = False)
    conn.commit()
    conn.close()