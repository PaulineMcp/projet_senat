
"""
Mise à jour automatique des discussions actives.
Exécution prévue par un CRON.

Les avis gouvernementaux et de commission sont gérés
séparément par le script maj_avis.py.
"""

############### IMPORTS ###############

import pandas as pd
from pathlib import Path
import sys
import unicodedata
import traceback

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from utils import get_db
from fonctions.fonctions_scrapping_cleaning.fonctions_scrapping import get_hash
from fonctions.upsert_bdd import upsert_df

from fonctions.init_discussion import (
    fetch_content,
    fetch_articles_from_texte,
    fetch_articles_from_amdts,
    fetch_disc
)


############### RÉCUPÉRATION DES DISCUSSIONS ACTIVES ###############

with get_db() as conn:

    df_active_disc = pd.read_sql("""
        SELECT
            id_disc,
            last_hash,
            url_disc,
            titre_disc,
            lien_note,
            lien_dossier,
            url_txt,
            com_seance
        FROM discussion
        WHERE is_archived = 0
    """, conn)


############### MISE À JOUR DES DISCUSSIONS ###############

for (
    id_disc,
    last_hash,
    url_disc,
    titre,
    lien_note,
    lien_dossier,
    url_txt,
    com_seance
) in df_active_disc.itertuples(index=False, name=None):

    print(f"\n########## Discussion : {id_disc} ##########")

    try:

        ############### VÉRIFICATION DU HASH ###############

        actual_hash = get_hash(url_disc)

        if actual_hash == last_hash:
            print("Discussion à jour")
            continue

        print("## Actualisation de la discussion")

        ############### RÉCUPÉRATION DES INFORMATIONS ###############

        inputs = {
            "titre": titre,
            "url": url_disc,
            "lien_note": lien_note,
            "lien_dossier": lien_dossier,
            "url_txt": url_txt
        }

        updated_disc = fetch_disc(url_disc, inputs)

        # Récupération du contenu depuis le site du Sénat.
        # Cette opération ne nécessite pas de transaction SQLite.

        print("# Récupération des parties, ordre et amendements")

        updated_parties, updated_ordre, updated_content = fetch_content(
            id_disc
        )

        # Récupération des articles depuis le texte.
        print("# Récupération des articles")

        updated_art_from_txt = fetch_articles_from_texte(id_disc)

        ############### TRANSACTION DE MISE À JOUR ###############

        # Toutes les modifications d'une discussion sont validées
        # ensemble. En cas d'erreur, elles sont annulées.

        with get_db() as conn:

            ############### ACTUALISATION DES PARTIES ###############

            print("# Actualisation des parties")

            if not updated_parties.empty:

                upsert_df(
                    "parties",
                    updated_parties,
                    "id_partie",
                    conn=conn
                )

            ############### ACTUALISATION DES AMENDEMENTS ###############

            print("# Actualisation des amendements")

            # Désactiver les amendements précédemment enregistrés.
            conn.execute("""
                UPDATE amdts
                SET is_active = 0
                WHERE id_partie IN (
                    SELECT id_partie
                    FROM parties
                    WHERE id_disc = ?
                )
            """, (id_disc,))

            # Réactiver les amendements toujours présents.
            if not updated_content.empty:

                updated_content["is_active"] = 1

                upsert_df(
                    "amdts",
                    updated_content,
                    "id_amdt",
                    conn=conn
                )

            print(
                f"{len(updated_content)} amendements récupérés."
            )

            ############### ACTUALISATION DE L'ORDRE ###############

            print("# Actualisation de l'ordre")

            if not updated_ordre.empty:

                upsert_df(
                    "ordre_examen",
                    updated_ordre,
                    "id_amdt",
                    conn=conn
                )

            ############### ACTUALISATION DES ARTICLES ###############

            print("# Actualisation des articles")

            # Cette fonction lit les amendements en BDD :
            # on lui transmet donc la connexion existante.

            updated_art_from_amdts = fetch_articles_from_amdts(
                id_disc,
                conn=conn
            )

            updated_art = pd.concat(
                [
                    updated_art_from_amdts,
                    updated_art_from_txt
                ],
                ignore_index=True
            )

            if not updated_art.empty:

                # Normalisation des textes.
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

                upsert_df(
                    "articles",
                    updated_art,
                    "id_article",
                    conn=conn
                )

            print(f"{len(updated_art)} articles récupérés.")

            ############### INITIALISATION DES AVIS DES NOUVEAUX AMENDEMENTS ###############

            print("# Initialisation des avis des nouveaux amendements")

            # En commission, il n'y a rien à récupérer : pas besoin d'attendre le script d'avis
            defaut_avis = "Pas d'avis" if com_seance == "Commission" else "En cours de récupération"

            df_new_avis = pd.read_sql("""
                SELECT DISTINCT a.id_amdt
                FROM amdts a
                JOIN parties p ON p.id_partie = a.id_partie
                WHERE p.id_disc = ?
                AND a.is_active = 1
                AND NOT EXISTS (SELECT 1 FROM avis v WHERE v.id_amdt = a.id_amdt)
            """, conn, params=(id_disc,))

            if not df_new_avis.empty:
                df_new_avis["avis_gouv"] = defaut_avis
                df_new_avis["avis_com"] = defaut_avis
                upsert_df("avis", df_new_avis, "id_amdt", conn=conn)
                print(f"{len(df_new_avis)} avis initialisés ({defaut_avis}).")

            ############### INITIALISATION DES NOUVEAUX REMPLISSAGES AMDT ###############

            print("# Initialisation des nouveaux remplissages amendements")

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
                    "id_amdt",
                    conn=conn
                )

                print(
                    f"{len(df_new_amdts)} nouveaux amendements initialisés."
                )

            else:
                print("Aucun nouvel amendement à initialiser.")

            ############### INITIALISATION DES NOUVEAUX REMPLISSAGES ARTICLES ###############

            print("# Initialisation des nouveaux remplissages articles")

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
                    "id_article",
                    conn=conn
                )

                print(
                    f"{len(df_new_articles)} nouveaux articles initialisés."
                )

            else:
                print("Aucun nouvel article à initialiser.")

            ############### MISE À JOUR DU HASH ###############

            # Cette opération intervient en dernier.
            # Le hash n'est actualisé que si tout le reste a réussi.

            print("# Mise à jour du hash de la discussion")

            upsert_df(
                "discussion",
                updated_disc,
                "id_disc",
                conn=conn
            )

        # La transaction est validée en sortant du get_db().
        print(f"Discussion {id_disc} actualisée avec succès.")

    except Exception as e:

        print(
            f"ERREUR lors de la mise à jour de {id_disc} : {e}"
        )

        traceback.print_exc()

        print(
            "Les modifications de cette discussion "
            "ont été annulées si l'erreur est survenue "
            "pendant la transaction."
        )


print("\n########## FIN DES MISES À JOUR ##########")