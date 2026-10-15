"""
    Fonctions pour valider les inputs du formulaire de création de discussion :

        - url_valide : teste si un lien est bien une URL d'amendements
        - disc_already_exist : teste si la discussion est déjà surveillée
        - is_not_google_doc : teste si un lien est un Google Doc
"""
#############       IMPORTS       ##############
import re
import pandas as pd
import sys
from pathlib import Path

# Chemin de la racine
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from utils import get_conn

#############       FONCTIONS       ##############
def url_valide(url):
    pattern_seance = re.compile(r"^https://www\.senat\.fr/amendements/\d{4}-\d{4}/\d+/liste_discussion\.html$")
    pattern_com = re.compile(r"^https://www\.senat\.fr/amendements/commissions/\d{4}-\d{4}/\d+/liste_discussion\.html$")
    if pattern_seance.match(url) :
        return True
    else :
        if pattern_com.match(url):
            return True
        else :
            return False 

def disc_already_exist(url):
    conn = get_conn()
    urls = pd.read_sql("""SELECT url_disc FROM discussion""", conn,)["url_disc"].tolist()
    conn.close()
    if urls == []:
        return False
    else :
        return url in urls # retourne un bool

def is_not_google_doc(url) :
    if url.startswith("https://docs.google.com") or url == "":
        return False
    else : 
        return True