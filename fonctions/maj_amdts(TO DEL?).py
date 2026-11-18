""" Mise à jour de :
        - l'ordre d'examen des amendement
        - le contenu des amendements
        - les articles
        - des remplissages des amdts
        - des remplissages des articles
Via un CRON toutes les 1 min


###############     IMPORTS     ###############

# Import des librairies
import pandas as pd
import sys
from pathlib import Path
import sqlite3

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
from fonctions.init_discussion import fetch_content

DB_PATH = ROOT / "bdd.db"

def update_content(3 df) :
    return()


def maj_content(id_disc):
    try:
        actual_content = fetch_content(id_disc)
        update_content(actual_content)

def maj_remplissage(id_disc):
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





        sqlite3.Connection.commit(connexion)
        print("Tout est enregistré")

    except Exception:
        connexion.rollback()
        print("Erreur : aucune modification enregistrée")
        traceback.print_exc()

    finally:
        sqlite3.Connection.close(connexion)"""