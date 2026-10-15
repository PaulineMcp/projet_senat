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

from utils import get_conn

###############     FONCTIONS     ###############
def retrieve_tab(id_disc):
    conn = get_conn()
    df = pd.read_sql("""
                    WITH liste_articles AS (
                        -- Tous les articles connus
                        SELECT
                            articles.id_article,
                            articles.id_bloc_article,
                            articles.article,
                            articles.ordre_article,
                            CASE WHEN articles.id_article LIKE '%addav%' THEN -1
                                WHEN articles.id_article LIKE '%addap%' THEN 1
                                ELSE 0
                            END AS pos
                        FROM articles
                        WHERE articles.id_disc = ?

                        UNION

                        -- Articles additionnels connus seulement via amdts
                        SELECT DISTINCT
                            amdts.id_article,
                            amdts.id_bloc_article,
                            CASE WHEN amdts.id_article LIKE '%addav%'
                                THEN 'Article additionnel avant ' || articles.article
                                ELSE 'Article additionnel après ' || articles.article
                            END,
                            articles.ordre_article,
                            CASE WHEN amdts.id_article LIKE '%addav%' THEN -1 ELSE 1 END
                        FROM amdts
                        JOIN articles
                            ON articles.id_article = amdts.id_bloc_article
                        WHERE articles.id_disc = ?
                        AND amdts.id_article NOT IN (SELECT id_article FROM articles)
                    )
                    SELECT
                        liste_articles.id_bloc_article,
                        liste_articles.id_article,
                        liste_articles.article,
                        liste_articles.ordre_article,
                        discussion.url_articles AS lien_article,
                        ordre_examen.ordre_amdt,
                        amdts.id_amdt,
                        amdts.amdt,
                        amdts.is_ss_amdt,
                        amdts.lien_amdt,
                        amdts.url_senateur,
                        senateurs.nom_groupe,
                        remplissage_ap_amdt.objet,
                        remplissage_ap_amdt.com,
                        avis.avis_gouv,
                        avis.avis_com,
                        remplissage_ap_amdt.proposition_vote_amdt,
                        amdts.sort
                    FROM liste_articles
                    JOIN discussion
                        ON discussion.id_disc = ?
                    LEFT JOIN amdts
                        ON amdts.id_article = liste_articles.id_article
                    LEFT JOIN ordre_examen
                        ON ordre_examen.id_amdt = amdts.id_amdt
                    LEFT JOIN avis
                        ON avis.id_amdt = amdts.id_amdt
                    LEFT JOIN remplissage_ap_amdt
                        ON remplissage_ap_amdt.id_amdt = amdts.id_amdt
                    LEFT JOIN senateurs
                        ON senateurs.url = amdts.url_senateur
                    ORDER BY liste_articles.ordre_article,
                            liste_articles.pos,
                            ordre_examen.ordre_amdt IS NULL,
                            ordre_examen.ordre_amdt;
                                        """,
                conn,
                params = (id_disc, id_disc, id_disc,))
    conn.close()
    return(df)