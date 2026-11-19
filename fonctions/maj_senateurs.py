"""
Script de mise à jour des données sur les sénateurs
Mis à jour avec un cron tous les jours
"""
###############     IMPORTS     ###############
# Import des librairies
import sys
from pathlib import Path
import pandas as pd

# Chemin de la racine
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from utils import *
from fonctions.fonctions_scrapping_cleaning.fonctions_cleaning import abrev_groupe

###############     FONCTION     ###############       
def maj_senateurs():
    try :
        # Mise à jour des sénateurs
        df = pd.read_csv('https://www.senat.fr/vos-senateurs/recherche-de-senateurs/recherche-avancee-de-senateurs.csv', sep=';')
        df = df[["URL", "Civilité", "Nom", "Prénom", "Groupe politique"]]
        df = df.rename(columns = {
            "URL" : "url",
            "Civilité" : "civilite",
            "Nom" : "nom",
            "Prénom" : "prenom",
            "Groupe politique" : "groupe"
        })
        df["groupe"] = df["groupe"].apply(lambda x : abrev_groupe(x))
        df["nom_groupe"] = df["civilite"] + " " + df["nom"] + " (" + df["groupe"] + ")"

        # Envoyer les données dans la base
        with get_db() as conn :
            df.to_sql("senateurs", conn, if_exists="replace", index = False)
    except Exception as e :
            print(f"Error : {e}")

###############     APPEL     ############### 
maj_senateurs()
print("Données sénateurs maj !")