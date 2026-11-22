""" Fonction pour récupérer en SQL le tableau à afficher par discussion"""

###############     IMPORTS     ###############
# Import des librairies
import pandas as pd
from pathlib import Path
import sys
import math

# Chemin de la racine
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from utils import *

###############     FONCTIONS     ###############
def retrieve_tab(id_disc : str) :
    with get_db() as conn :
        df = pd.read_sql("""SELECT articles.id_bloc_article,
                                articles.bloc,
                                articles.id_article,
                                    articles.article,
                                    amdts.id_amdt,
                                    amdts.amdt,
                                    parties.id_partie,
                                    parties.titre_partie,
                                    ordre_examen.ordre_examen_in_partie,
                                    amdts.sort,
                                    amdts.auteur,
                                    amdts.url_senateur,
                                    amdts.is_ss_amdt,
                                    amdts.lien_amdt,
                                    amdts.lien_article,
                                    amdts.is_active,
                                    senateurs.nom_groupe,
                                    avis.avis_com,
                                    avis.avis_gouv,
                                    remplissage_ap_amdt.objet,
                                    remplissage_ap_amdt.com,
                                    remplissage_ap_amdt.proposition_vote_amdt
                            FROM articles
                            LEFT JOIN discussion
                                ON discussion.id_disc = articles.id_disc
                            LEFT JOIN amdts
                                ON amdts.id_article = articles.id_article
                            LEFT JOIN parties
                                ON amdts.id_partie = parties.id_partie
                            LEFT JOIN ordre_examen
                                ON ordre_examen.id_amdt = amdts.id_amdt
                            LEFT JOIN senateurs
                                ON senateurs.url = amdts.url_senateur
                            LEFT JOIN avis
                                ON avis.id_amdt = amdts.id_amdt
                            LEFT JOIN remplissage_ap_amdt
                                ON amdts.id_amdt = remplissage_ap_amdt.id_amdt
                            WHERE discussion.id_disc = ? AND amdts.is_active = 1
                            ORDER BY parties.ordre_partie
                        """,
                        conn,
                        params = (id_disc,))
    return(df)

## conservation
def retrieve_first_tab(id_disc : str) :
    with get_db() as conn :
        df = pd.read_sql("""SELECT articles.id_bloc_article,
                                articles.bloc,
                                articles.id_article,
                                articles.article,
                                amdts.id_amdt,
                                amdts.amdt,
                                ordre_examen.ordre_examen_in_partie,
                                amdts.sort,
                                amdts.auteur,
                                amdts.url_senateur,
                                amdts.is_ss_amdt,
                                amdts.lien_amdt,
                                amdts.lien_article,
                                senateurs.nom_groupe,
                                avis.avis_com,
                                avis.avis_gouv,
                                remplissage_ap_amdt.objet,
                                remplissage_ap_amdt.com,
                               remplissage_ap_amdt.proposition_vote_amdt,
                               amdts.is_active
                            FROM articles
                            LEFT JOIN amdts
                                ON amdts.id_article = articles.id_article
                            AND amdts.id_partie = ?
                            LEFT JOIN ordre_examen
                                ON ordre_examen.id_amdt = amdts.id_amdt
                            LEFT JOIN avis
                                ON avis.id_amdt = amdts.id_amdt
                            LEFT JOIN senateurs
                                ON senateurs.url = amdts.url_senateur
                            LEFT JOIN remplissage_ap_amdt
                                ON amdts.id_amdt = remplissage_ap_amdt.id_amdt
                            LEFT JOIN parties
                                ON amdts.id_partie = parties.id_partie
                            WHERE articles.id_disc = ?
                        """,
                        conn,
                        params=(f"{id_disc}-p1", id_disc))
    return(df)


#def retrieve_first_tab_test(id_disc : str) :
#    with get_db() as conn :
#        df = pd.read_sql("""SELECT articles.id_bloc_article,
#                                articles.bloc,
#                                articles.id_article,
#                                articles.article,
#                                ordre_examen.ordre_examen_in_partie
#                            FROM articles
#                            LEFT JOIN amdts
#                            ON amdts.id_article = articles.id_article
#                            LEFT JOIN ordre_examen
#                           ON ordre_examen.id_amdt = amdts.id_amdt
#                            WHERE id_disc = ?
#                        """,
#                        conn,
#                        params=(id_disc,))
#    return(df)

def retrieve_infos_disc(id_disc : str):
    with get_db() as conn :
        df_infos_disc = pd.read_sql(
        """
        SELECT *
        FROM discussion
        WHERE id_disc = ?
        """,
        conn,
        params=(id_disc,),
        )
    return(df_infos_disc)

def retrieve_info_articles(id_disc : str) -> pd.DataFrame :
    with get_db() as conn :
        df_votes_articles = pd.read_sql("""
        SELECT remplissage_ap_article.id_article,
            remplissage_ap_article.resume_article,
            remplissage_ap_article.proposition_vote_article
        FROM remplissage_ap_article
        JOIN articles
            ON articles.id_article = remplissage_ap_article.id_article
        WHERE articles.id_disc = ?
        """,
        conn,
        params=(id_disc,),)
    return(df_votes_articles)
