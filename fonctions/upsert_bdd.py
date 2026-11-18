import pandas as pd
from pathlib import Path
import sys
import math

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from utils import *
import streamlit as st


####### FONCTIONS ########

def upsert_df(table: str, df: pd.DataFrame, cle_pk: str) -> None:
    """Insère les nouvelles lignes, met à jour les existantes"""
    cols = list(df.columns)
    maj = ", ".join(f"{c} = excluded.{c}" for c in cols if c != cle_pk)
    request =  f"""INSERT INTO {table} ({', '.join(cols)})
                    VALUES ({', '.join('?' * len(cols))})
                    ON CONFLICT({cle_pk}) DO UPDATE SET {maj}"""
    with get_db() as conn :
            conn.executemany(request, df.itertuples(index=False, name=None))
             