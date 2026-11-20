###############     IMPORTS LIBRAIRIES ET FONCTIONS     ###############
from pathlib import Path
import sqlite3
import streamlit as st 
import sys
import hashlib
import re
import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3
from contextlib import contextmanager
from pathlib import Path

# Constantes
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DB_PATH = Path(__file__).parent / "bdd.db"
#DB_PATH = Path(__file__).resolve().parent / "bdd.db"

@contextmanager
def get_db():

    conn = sqlite3.connect(DB_PATH, timeout=30)

    try:
        conn.execute("PRAGMA foreign_keys = ON")

        yield conn

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


###############     STYLE     ###############
def charger_css():
    css = ("style.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
