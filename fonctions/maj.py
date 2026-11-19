# Déclenchement des mises à jour
## fait l'objet d'un cron
# Chemin de la racine
import pandas as pd
from pathlib import Path
import sys
import math
import unicodedata

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from utils import *
from fonctions.fonctions_scrapping_cleaning.fonctions_scrapping import get_hash
from fonctions.upsert_bdd import upsert_df
from init_discussion import fetch_content, fetch_articles_from_texte, fetch_articles_from_amdts, fetch_avis, fetch_disc

# Récupérer la liste des discussion non-archivées
with get_db() as conn :
    df_active_disc = pd.read_sql("""SELECT *
                        FROM discussion
                        WHERE discussion.is_archived = 0
                    """,
                    conn,)

for id_disc, last_hash, url_disc, titre, lien_note, lien_dossier, url_txt in df_active_disc[["id_disc","last_hash","url_disc","titre_disc","lien_note","lien_dossier","url_txt"]].itertuples(index=False, name=None):
    # Check le hash actuel
    actual_hash = get_hash(url_disc)

    if actual_hash == last_hash :
        print("Discussion à jour")
    else :

        print("## Actualisation de la discussion")

        print("# Actualisation des parties")
        updated_parties, updated_ordre, updated_content = fetch_content(id_disc)
        upsert_df("parties", updated_parties, "id_partie")
        
        print("# Actualisation des amdts")
        with get_db() as conn :
            # Changer tous les amdts pour inactif
            conn.execute("""UPDATE amdts
                            SET is_active = 0
                            WHERE id_partie IN (SELECT id_partie FROM parties WHERE id_disc = ?)
                        """,
                        (id_disc,))
        upsert_df("amdts", updated_content, "id_amdt")

        print("# Actualisation de l'ordre")
        upsert_df("ordre_examen", updated_ordre, "id_amdt")

        print("# Actualisation des articles")
        updated_art_from_amdts = fetch_articles_from_amdts(id_disc)
        updated_art_from_txt = fetch_articles_from_texte(id_disc)
        updated_art = pd.concat([updated_art_from_amdts,updated_art_from_txt])
        updated_art["article"] = updated_art["article"].map(lambda s: " ".join(unicodedata.normalize("NFKC", s).split()))
        updated_art = updated_art.drop_duplicates(subset=["id_bloc_article","bloc_article","bloc","id_article","id_disc"], keep="first")
        upsert_df("articles", updated_art, "id_article")

        print("# Initialisation des nouveaux remplissages amdt")
        with get_db() as conn :
            lignes = conn.execute("SELECT id_amdt FROM amdts WHERE id_amdt NOT IN (SELECT id_amdt FROM remplissage_ap_amdt)")
            df_new_amdts = pd.DataFrame(lignes, columns=["id_amdt"])
        df_new_amdts["objet"] = "À compléter"
        df_new_amdts["com"] = ""
        df_new_amdts["proposition_vote_amdt"] = "À définir"
        upsert_df("remplissage_ap_amdt", df_new_amdts, "id_amdt")   

        print("# Initialisation des nouveaux remplissages articles")
        with get_db() as conn :
            lignes = conn.execute("SELECT id_article FROM articles WHERE id_article NOT IN (SELECT id_article FROM remplissage_ap_article)")
            df_new_articles = pd.DataFrame(lignes, columns=["id_article"])
        df_new_articles["resume_article"] = None
        df_new_articles["proposition_vote_article"] = None
        upsert_df("remplissage_ap_article", df_new_articles, "id_article")

        # Si et seulement si toutes les modifs ont bien été réalisées on met à jour le hash
        inputs = {
            "titre" : titre,
            "url" : url_disc,
            "lien_note" : lien_note,
            "lien_dossier" : lien_dossier,
            "url_txt" : url_txt
            }
        
        updated_disc = fetch_disc(url_disc, inputs) # permet de re calculer un nouveau hash et nouveau nb de parties
        upsert_df("discussion", updated_disc, "id_disc")