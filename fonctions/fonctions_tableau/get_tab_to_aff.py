""" Fonction pour récupérer en SQL le tableau à afficher par discussion"""

###############     IMPORTS     ###############
# Import des librairies
import pandas as pd
from pathlib import Path
import sys
import math
from fonctions.fonctions_scrapping_cleaning.fonctions_cleaning import abrev_article

# Chemin de la racine
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from utils import *

###############     FONCTIONS     ###############
def retrieve_1_partie(id_disc : str) :
    with get_db() as conn :
        df = pd.read_sql("""
                            SELECT
                                articles.id_disc, 
                                articles.id_bloc_article,
                                articles.bloc,
                                articles.id_article,
                                articles.article,
                                amdts_disc.id_amdt,
                                amdts_disc.amdt,
                                parties.id_partie,
                                parties.titre_partie,
                                parties.ordre_partie,
                                ordre_examen.ordre_examen_in_partie,
                                amdts_disc.sort,
                                amdts_disc.auteur,
                                amdts_disc.url_senateur,
                                amdts_disc.is_ss_amdt,
                                amdts_disc.lien_amdt,
                                amdts_disc.lien_article,
                                amdts_disc.is_active,
                                senateurs.nom_groupe,
                                avis.avis_com,
                                avis.avis_gouv,
                                remplissage_ap_amdt.objet,
                                remplissage_ap_amdt.com,
                                remplissage_ap_amdt.proposition_vote_amdt
                            FROM articles
                            LEFT JOIN (
                                SELECT 
                                    amdts.id_amdt,
                                    amdts.id_article,
                                    amdts.id_partie,
                                    amdts.amdt,
                                    amdts.sort,
                                    amdts.auteur,
                                    amdts.url_senateur,
                                    amdts.is_ss_amdt,
                                    amdts.lien_amdt,
                                    amdts.lien_article,
                                    amdts.is_active
                                FROM amdts
                                LEFT JOIN articles
                                    ON articles.id_article = amdts.id_article
                                LEFT JOIN discussion
                                    ON discussion.id_disc = articles.id_disc
                                WHERE amdts.id_partie LIKE '%p1'
                            ) AS amdts_disc
                                ON amdts_disc.id_article = articles.id_article
                            LEFT JOIN parties
                                ON parties.id_partie = amdts_disc.id_partie
                            LEFT JOIN ordre_examen
                                ON ordre_examen.id_amdt = amdts_disc.id_amdt
                            LEFT JOIN senateurs
                                ON senateurs.url = amdts_disc.url_senateur
                            LEFT JOIN avis
                                ON avis.id_amdt = amdts_disc.id_amdt
                            LEFT JOIN remplissage_ap_amdt
                                ON amdts_disc.id_amdt = remplissage_ap_amdt.id_amdt
                            WHERE articles.id_disc = ?
                            ORDER BY CAST(articles.bloc AS INTEGER) ASC
                        """,
                        conn,
                        params=(id_disc,))
    df["nom_groupe"] = (df["nom_groupe"].fillna(df["auteur"]))
    df["bloc"] = pd.to_numeric(df["bloc"],errors="coerce").astype("Int64")  # ça il faut que ce soit géré en BDD
    df["ordre_partie"] = pd.to_numeric(df["ordre_partie"],errors="coerce").astype("Int64")
    df = df.sort_values("bloc")
    df["abrev_article"] = (df["article"].apply(abrev_article))
    return(df)

###############     FONCTIONS     ###############
def retrieve_tab_autres_parties(id_disc : str) :
    with get_db() as conn :
        df = pd.read_sql("""SELECT
                                discussion.id_disc,
                                articles.id_bloc_article,
                                articles.bloc,
                                articles.id_article,
                                articles.article,
                                amdts.id_amdt,
                                amdts.amdt,
                                parties.id_partie,
                                parties.titre_partie,
                                parties.ordre_partie,
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
                            WHERE discussion.id_disc = ? AND amdts.id_partie NOT LIKE '%p1'
                        """,
                        conn,
                        params = (id_disc,))
    df["nom_groupe"] = (df["nom_groupe"].fillna(df["auteur"]))
    df["bloc"] = pd.to_numeric(df["bloc"],errors="coerce").astype("Int64")  # ça il faut que ce soit géré en BDD
    df["ordre_partie"] = pd.to_numeric(df["ordre_partie"],errors="coerce").astype("Int64")
    df = df.sort_values("bloc")
    df["abrev_article"] = (df["article"].apply(abrev_article))
    return(df)

@st.cache_data(ttl=300, show_spinner=False)
def retrieve_tab(id_disc : str) -> pd.DataFrame :
   df1 = retrieve_1_partie(id_disc)
   df2 = retrieve_tab_autres_parties(id_disc)
   return pd.concat([df1,df2],ignore_index=True) 


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
