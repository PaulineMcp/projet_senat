
""" Mise à jour des avis gouv et com, via un CRON toutes les 15 min """

###############     IMPORTS     ###############

import pandas as pd
from pathlib import Path
import sys

# Chemin de la racine
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from utils import get_db
from fonctions.init_discussion import fetch_avis
from fonctions.upsert_bdd import upsert_df


#############       APPELS       ##############

# Récupérer la liste des discussions non-archivées
with get_db() as conn:
    df_active_disc = pd.read_sql("""
        SELECT id_disc
        FROM discussion
        WHERE is_archived = 0
    """, conn)

# Mise à jour des avis
total = len(df_active_disc)
print(total)

for i, id_disc in enumerate(df_active_disc["id_disc"], start=1):

    print(f"\n[{i}/{total}] Mise à jour des avis : {id_disc}", flush=True)

    try:
        # Récupération des avis et mise à jour dans une seule transaction
        with get_db() as conn:

            updated_avis = fetch_avis(
                id_disc,
                conn=conn
            )

            if not updated_avis.empty:
                upsert_df(
                    "avis",
                    updated_avis,
                    "id_amdt",
                    conn=conn
                )

                print(f"   -> {len(updated_avis)} avis actualisés.", flush=True)

            else:
                print("   -> Aucun avis à actualiser.", flush=True)

    except Exception as e:
        print(f"   -> ERREUR lors de la mise à jour de {id_disc} : {e}", flush=True)
        print("   -> La discussion n'a pas été actualisée.", flush=True)

print("\nMise à jour terminée !", flush=True)