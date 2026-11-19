
# Déclenchement des mises à jour
# Fait l'objet d'un cron

############### IMPORTS ###############

import pandas as pd
from pathlib import Path
import sys
import math
import unicodedata

# Chemin de la racine
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from utils import *
from fonctions.fonctions_scrapping_cleaning.fonctions_scrapping import get_hash
from fonctions.upsert_bdd import upsert_df
from init_discussion import (
    fetch_content,
    fetch_articles_from_texte,
    fetch_articles_from_amdts,
    fetch_avis,
    fetch_disc
)


############### RÉCUPÉRATION DES DISCUSSIONS ACTIVES ###############

with get_db() as conn:
    df_active_disc = pd.read_sql("""
        SELECT *
        FROM discussion
        WHERE is_archived = 0
    """, conn)


############### MISE À JOUR DES DISCUSSIONS ###############

for id_disc, last_hash, url_disc, titre, lien_note, lien_dossier, url_txt in df_active_disc[
    ["id_disc", "last_hash", "url_disc", "titre_disc", "lien_note", "lien_dossier", "url_txt"]
].itertuples(index=False, name=None):

    print(f"\n########## Discussion : {id_disc} ##########")

    # Vérifier le hash actuel
    actual_hash = get_hash(url_disc)

    if actual_hash == last_hash:
        print("Discussion à jour")

    else:

        print("## Actualisation de la discussion")

        ############### ACTUALISATION DES PARTIES ###############

        print("# Actualisation des parties")

        updated_parties, updated_ordre, updated_content = fetch_content(id_disc)

        upsert_df("parties", updated_parties, "id_partie")


        ############### ACTUALISATION DES AMENDEMENTS ###############

        print("# Actualisation des amendements")

        # Désactiver tous les amendements de la discussion
        with get_db() as conn:
            conn.execute("""
                UPDATE amdts
                SET is_active = 0
                WHERE id_partie IN (
                    SELECT id_partie
                    FROM parties
                    WHERE id_disc = ?
                )
            """, (id_disc,))

        # Réactiver les amendements toujours présents
        if not updated_content.empty:

            updated_content["is_active"] = 1

            upsert_df("amdts", updated_content, "id_amdt")

        print(f"{len(updated_content)} amendements récupérés.")


        ############### ACTUALISATION DE L'ORDRE ###############

        print("# Actualisation de l'ordre")

        if not updated_ordre.empty:
            upsert_df("ordre_examen", updated_ordre, "id_amdt")


        ############### ACTUALISATION DES ARTICLES ###############

        print("# Actualisation des articles")

        updated_art_from_amdts = fetch_articles_from_amdts(id_disc)
        updated_art_from_txt = fetch_articles_from_texte(id_disc)

        updated_art = pd.concat(
            [updated_art_from_amdts, updated_art_from_txt],
            ignore_index=True
        )

        # Normalisation des textes, en gérant les valeurs nulles
        updated_art["article"] = updated_art["article"].map(
            lambda s: " ".join(
                unicodedata.normalize("NFKC", s).split()
            ) if isinstance(s, str) else s
        )

        updated_art = updated_art.drop_duplicates(
            subset=[
                "id_bloc_article",
                "bloc_article",
                "bloc",
                "id_article",
                "id_disc"
            ],
            keep="first"
        )

        if not updated_art.empty:
            upsert_df("articles", updated_art, "id_article")

        print(f"{len(updated_art)} articles récupérés.")


        ############### INITIALISATION DES NOUVEAUX REMPLISSAGES AMDT ###############

        print("# Initialisation des nouveaux remplissages amendements")

        with get_db() as conn:
            df_new_amdts = pd.read_sql("""
                SELECT DISTINCT a.id_amdt
                FROM amdts a
                JOIN parties p
                    ON p.id_partie = a.id_partie
                WHERE p.id_disc = ?
                AND NOT EXISTS (
                    SELECT 1
                    FROM remplissage_ap_amdt r
                    WHERE r.id_amdt = a.id_amdt
                )
            """, conn, params=(id_disc,))

        if not df_new_amdts.empty:

            df_new_amdts["objet"] = "À compléter"
            df_new_amdts["com"] = ""
            df_new_amdts["proposition_vote_amdt"] = "À définir"

            upsert_df(
                "remplissage_ap_amdt",
                df_new_amdts,
                "id_amdt"
            )

            print(f"{len(df_new_amdts)} nouveaux amendements initialisés.")

        else:
            print("Aucun nouvel amendement à initialiser.")


        ############### INITIALISATION DES NOUVEAUX REMPLISSAGES ARTICLES ###############

        print("# Initialisation des nouveaux remplissages articles")

        with get_db() as conn:
            df_new_articles = pd.read_sql("""
                SELECT DISTINCT a.id_article
                FROM articles a
                WHERE a.id_disc = ?
                AND NOT EXISTS (
                    SELECT 1
                    FROM remplissage_ap_article r
                    WHERE r.id_article = a.id_article
                )
            """, conn, params=(id_disc,))

        if not df_new_articles.empty:

            df_new_articles["resume_article"] = None
            df_new_articles["proposition_vote_article"] = None

            upsert_df(
                "remplissage_ap_article",
                df_new_articles,
                "id_article"
            )

            print(f"{len(df_new_articles)} nouveaux articles initialisés.")

        else:
            print("Aucun nouvel article à initialiser.")


        ############### MISE À JOUR DES AVIS ###############

        print("# Actualisation des avis")

        df_avis = fetch_avis(id_disc)

        if not df_avis.empty:
            upsert_df("avis", df_avis, "id_amdt")


        ############### MISE À JOUR DU HASH DE LA DISCUSSION ###############

        # Cette étape intervient uniquement si toutes les opérations précédentes
        # se sont terminées sans erreur.

        print("# Mise à jour du hash de la discussion")

        inputs = {
            "titre": titre,
            "url": url_disc,
            "lien_note": lien_note,
            "lien_dossier": lien_dossier,
            "url_txt": url_txt
        }

        updated_disc = fetch_disc(url_disc, inputs)

        upsert_df("discussion", updated_disc, "id_disc")

        print(f"Discussion {id_disc} actualisée avec succès.")


print("\n########## FIN DES MISES À JOUR ##########")