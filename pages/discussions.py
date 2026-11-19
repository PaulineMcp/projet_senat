""" Page de la liste des discussions """
# Import des librairies
import streamlit as st 
import pandas as pd
from pathlib import Path
import sys

# Constantes
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from utils import *

###############     PAGE        ###############

# Bouton de retour recherche
col_side, col_button = st.columns([5,1])
with col_button:
        if st.button("Retourner à la recherche"):
            st.switch_page("pages/recherche.py")

# Liste des tableaux
col_gauche, col_centre, col_droite = st.columns([1,3,1])
with col_centre :
    st.write("Liste de tous les tableaux déjà créés")
        
    with get_db() as conn:
        df = pd.read_sql("SELECT * FROM discussion", conn)

    for _, ligne in df.iterrows():
        if st.button(ligne["titre_disc_long"], key=f"{ligne["id_disc"]}"):
            st.query_params["discussion_choisie"] = ligne["id_disc"]
            st.switch_page("pages/afficher_tab_amdts.py",
                           query_params={"discussion_choisie": str(ligne["id_disc"])})                                      