import pandas as pd
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from utils import get_db


def upsert_df(table, df, cle_pk, conn=None) -> None:
    """Insère les nouvelles lignes et met à jour les existantes."""
    if df.empty:
        return

    cols = list(df.columns)
    maj = ", ".join(f"{c} = excluded.{c}" for c in cols if c != cle_pk)
    
    request = f"""INSERT INTO {table} ({', '.join(cols)})
                    VALUES ({', '.join('?' * len(cols))})
                    ON CONFLICT({cle_pk}) DO UPDATE SET {maj}"""
    
    if conn is None:
        with get_db() as conn:
            conn.executemany(request, df.itertuples(index=False, name=None))      
    else:
        conn.executemany(request, df.itertuples(index=False, name=None))
    print("Envoi des données en BDD")