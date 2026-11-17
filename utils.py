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

# Constantes
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DB_PATH = Path(__file__).parent / "bdd.db" # remonte de pages à app_senat
print(DB_PATH)

###############     CONNEXION BD     ###############
def get_conn():
    try :
        return sqlite3.connect(DB_PATH, timeout=30)
    except Exception as e :
        print(f"Erreur de connexion à la base de données : {e}")


###############     STYLE     ###############
def charger_css():
    css = ("style.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
