""" Mise à jour de :
        - l'ordre d'examen des amendement
        - le contenu des amendements
        - les articles
        - des remplissages des amdts
        - des remplissages des articles
Via un CRON toutes les 1 min

"""
###############     IMPORTS     ###############

# Import des librairies
import pandas as pd
import sys
from pathlib import Path

# Chemin de la racine pour trouver les autres fichiers
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Import des fonctions des autres fichiers
from utils import get_conn
from fonctions.fonctions_cleaning import get_session
from fonctions.fonctions_cleaning import get_id_disc
from fonctions.fonctions_cleaning import get_id_amdt
from fonctions.fonctions_cleaning import is_ss_amdt
from fonctions.fonctions_cleaning import get_id_bloc_article
from fonctions.fonctions_cleaning import commission_ou_sceance

from fonctions.fonctions_cleaning import get_id_article
from fonctions.fonctions_scrapping import get_tab
from fonctions.fonctions_scrapping import clean_tab_ordre
from fonctions.fonctions_scrapping import clean_amdt_info
from fonctions.fonctions_scrapping import get_content_page


def maj_ordre_examen() :

    # Récupère la liste des PJL / PPL à mettre à jour
    conn = get_conn()        
    urls = pd.read_sql("SELECT * FROM discussion", conn)
    urls = urls["url_disc"].tolist()
    conn.close()

    # Récupérer l'ordre des amendements de ces PJL / PPL sous forme d'un df
    for url in urls :
        tab = get_tab(url)
        df = clean_tab_ordre(tab)
        session = get_session(url)
        raw_com_seance = "COM" if commission_ou_sceance(url) == "Commission" else "SCE"
        id_disc = session + "-" + raw_com_seance + "-" + get_id_disc(url)
        df["id_article"] = df.apply(lambda x: get_id_article(x.article, id_disc), axis=1)
        df["id_amdt"] = df["id_article"] + "-" + df["amdt"].apply(get_id_amdt)
        df["ordre_amdt"] = df.index
        df = df[["ordre_amdt","id_amdt"]]

    # Renvoyer les nouvelles données dans la table ordre_examen       
        conn = get_conn()
        conn.executemany(
        """
        UPDATE ordre_examen
        SET ordre_amdt = ?
        WHERE id_amdt = ?
        """,
        df[["ordre_amdt","id_amdt"]].values.tolist(),)
        conn.executemany(
        """
        INSERT OR IGNORE INTO ordre_examen (ordre_amdt, id_amdt)
        VALUES (?, ?)
        """,
        df[["ordre_amdt","id_amdt"]].values.tolist(),)
        conn.commit()
        conn.close()



def maj_content_amdts()  : 
    
    # Récupère la liste des PJL / PPL à mettre à jour
    conn = get_conn()        
    urls = pd.read_sql("SELECT * FROM discussion", conn)
    urls = urls["url_disc"].tolist()
    conn.close()

    for url in urls :
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
        # Corrigerles nouvelles données dans la table ordre_examen       
        conn = get_conn()
        conn.executemany(
        """
        UPDATE amdts
        SET "id_article" = ?,
                "id_bloc_article" = ?,
                "amdt" = ?,
                "is_ss_amdt" = ?,
                "lien_amdt" = ?,
                "url_senateur" = ?,
                "sort" = ?
        WHERE id_amdt = ?
        """,
        df[["id_article","id_bloc_article","amdt","is_ss_amdt","lien_amdt","url_senateur","sort","id_amdt"]].values.tolist(),)
        # Envoyer les nouvelles données dans la table
        conn.executemany(
        """
        INSERT OR IGNORE INTO amdts
        (id_amdt, id_article, id_bloc_article, amdt, is_ss_amdt, lien_amdt, url_senateur, sort)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        df[["id_amdt", "id_article", "id_bloc_article", "amdt","is_ss_amdt", "lien_amdt", "url_senateur", "sort"]].values.tolist(),)
        conn.commit()
        conn.close()

def maj_articles():
    
    # Récupère la liste des PJL / PPL à mettre à jour
    conn = get_conn()        
    df = pd.read_sql("SELECT * FROM discussion", conn)
    ids_disc = df["id_disc"].tolist()
    conn.close()

    for id_disc in ids_disc :

        # On récupère l'url du texte
        conn = get_conn()
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

        # Récupérer les infos sur les articles
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

        # Renvoyer le résultat en base de données
        conn.executemany(
        """
        UPDATE articles
        SET "id_bloc_article" = ?,
                "id_disc" = ?,
                "article" = ?,
                "ordre_article" = ?
        WHERE id_article = ?
        """,
        df_articles[["id_bloc_article","id_disc","article","ordre_article","id_article"]].values.tolist(),)
        # Insère les nouvelles données
        conn.executemany(
        """
        INSERT OR IGNORE INTO articles
        (id_article, id_bloc_article, id_disc, article, ordre_article)
        VALUES (?, ?, ?, ?, ?)
        """,
        df_articles[["id_article", "id_bloc_article", "id_disc", "article", "ordre_article"]].values.tolist(),
        )
        conn.commit()
        conn.close()

def maj_remplissage_ap_amdts():

    # Récupère la liste des amdts
    conn = get_conn()
    amdts = pd.read_sql("SELECT id_amdt FROM amdts", conn)
    
    # Récupère la liste des remplissages existants
    remplissage = pd.read_sql("SELECT id_amdt FROM remplissage_ap_amdt", conn)
    
    # Les nouveaux amdts sont dans la table amdts mais pas dans remplissage_ap_amdt
    new_amdts = list(set(amdts["id_amdt"]) - set(remplissage["id_amdt"]))
    
    if not new_amdts:
            print("Aucun nouvel amendement à ajouter")
            conn.close()
    else : 
        df = pd.DataFrame({"id_amdt": new_amdts})
        df["objet"] = "A compléter"
        df["com"] = ""
        df["proposition_vote_amdt"] = "A définir"

        df.to_sql("remplissage_ap_amdt", conn, if_exists="append", index=False)
        conn.commit()
        print(f"De nouveaux amendements ont été ajoutés !")
        conn.close() 

def maj_remplissage_ap_articles():

    # Récupère la liste des amdts
    conn = get_conn()
    articles = pd.read_sql("SELECT id_article FROM articles", conn)
    
    # Récupère la liste des remplissages existants
    remplissage = pd.read_sql("SELECT id_article FROM remplissage_ap_article", conn)
    
    # Les nouveaux amdts sont dans la table amdts mais pas dans remplissage_ap_amdt
    new_articles = list(set(articles["id_article"]) - set(remplissage["id_article"]))
    
    if not new_articles:
            print("Aucun nouvel article à ajouter")
            conn.close()
    else : 
        df = pd.DataFrame({"id_article": new_articles})
        df["resume_article"] = ""
        df["proposition_vote_article"] = ""
        df.to_sql("remplissage_ap_article", conn, if_exists="append", index=False)
        conn.commit()
        print(f"De nouveaux articles ont été ajoutés !")
        conn.close()    

#############       APPELS       ##############
import sqlite3
import traceback

DB_PATH = ROOT / "bdd.db"   # à vérifier : le chemin de votre base

class ConnexionUnique(sqlite3.Connection):
    """Connexion partagée : les commit() et close() des fonctions ne font rien."""
    def commit(self):
        pass

    def close(self):
        pass


connexion = sqlite3.connect(DB_PATH, factory=ConnexionUnique, timeout=30)
get_conn = lambda: connexion   # les fonctions utilisent maintenant cette connexion

try:
    maj_ordre_examen()
    print("Ordre d'examen des amdts maj !")
    maj_content_amdts()
    print("Contenu des amdts maj !")
    maj_articles()
    print("Contenu des articles maj !")
    maj_remplissage_ap_amdts()
    print("Remplissage des amdts maj !")
    maj_remplissage_ap_articles()
    print("Remplissage des articles maj !")

    sqlite3.Connection.commit(connexion)
    print("Tout est enregistré")

except Exception:
    connexion.rollback()
    print("Erreur : aucune modification enregistrée")
    traceback.print_exc()

finally:
    sqlite3.Connection.close(connexion)