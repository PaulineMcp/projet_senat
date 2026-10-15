""" Mise à jour des avis gouv et com, via un CRON toutes les 15 min """

###############     IMPORTS     ###############

# Import des librairies
import pandas as pd
from pathlib import Path
import sys

# Chemin de la racine
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from utils import get_conn
from fonctions.fonctions_scrapping import get_avis_com
from fonctions.fonctions_scrapping import get_avis_gouv

#############       FONCTION       ##############

def maj_avis():

    # Récupère l'ensemble des discussions à mettre à jour
    conn = get_conn()        
    ids_disc = pd.read_sql("SELECT * FROM discussion", conn)
    ids_disc = ids_disc["id_disc"].tolist()
    conn.close()

    for id_disc in ids_disc :   
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
        conn.executemany(
            """
            UPDATE avis
            SET avis_gouv = ?, avis_com = ?
            WHERE id_amdt = ?
            """,
            df[["avis_gouv", "avis_com", "id_amdt"]].values.tolist(),
        )
        conn.commit()
        conn.close()

#############       APPELS       ##############

maj_avis()
print("Avis com et avis gouv de toutes les discussions maj !")