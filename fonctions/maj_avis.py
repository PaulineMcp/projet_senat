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
from fonctions.init_discussion import fetch_avis
from fonctions.upsert_bdd import upsert_df
from utils import *

#############       APPELS       ##############
# Récupérer la liste des discussion non-archivées
with get_db() as conn :
    df_active_disc = pd.read_sql("""SELECT *
                        FROM discussion
                        WHERE discussion.is_archived = 0
                    """,
                    conn,)
for id_disc in df_active_disc["id_disc"] : 
    updated_avis = fetch_avis(id_disc)
    upsert_df("avis", updated_avis, "id_amdt")