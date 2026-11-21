###############     IMPORTS LIBRAIRIES ET FONCTIONS     ###############
from pathlib import Path
import sqlite3
import streamlit as st 
import sys
import sqlite3
from contextlib import contextmanager
from pathlib import Path

# Constantes
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DB_PATH = Path(__file__).parent / "bdd.db"



@contextmanager
def get_db():
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 30000")
        yield conn
        conn.commit()

    except Exception as e:
        if conn is not None:
            conn.rollback()
        print(f"Erreur SQLite dans get_db : {type(e).__name__}: {e}")
        raise

    finally:
        if conn is not None:
            conn.close()


print("Chemin de la base :", DB_PATH)
print("Base existe :", DB_PATH.exists())
print("Chemin absolu :", DB_PATH.resolve())


###############     STYLE     ###############
def charger_css():
    css = ("style.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
