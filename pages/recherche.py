""" Affichage des résultats de la recherche """
###############     IMPORTS        ###############
# Import des librairies
import streamlit as st
from pathlib import Path
import pandas as pd
import sys

# Constantes
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from utils import get_conn

###############     PAGE        ###############
        
col_gauche, col_centre, col_droite = st.columns([1,2,1])
with col_centre :
    with st.container(vertical_alignment = "center", border = True):
        
        st.title("Rechercher une discussion")

        col1, col2 = st.columns(2, vertical_alignment="bottom")

        with col1:
            recherche = st.text_input("Recherche un PJL mot clé", placeholder="Mot-clé : agriculture, finance, écologie...", label_visibility = "hidden")
        with col2:
            if st.button("Rechercher"):
                st.session_state["recherche_active"] = True
        
        if st.session_state.get("recherche_active") and recherche:
            conn = get_conn()
            result_recherche = pd.read_sql(
                """
                SELECT *
                FROM discussion
                WHERE titre_disc_long LIKE ?
                """,
                conn,
                params=(f"%{recherche}%",),
            )
            conn.close()

            if result_recherche.empty:
                st.info("Aucun résultat")

            for _, ligne in result_recherche.iterrows():
                if st.button(ligne["titre_disc_long"], key=f"{ligne["id_disc"]}"):
                    st.query_params["discussion_choisie"] = ligne["id_disc"]
                    st.switch_page("pages/afficher_tab_amdts.py",
                           query_params={"discussion_choisie": str(ligne["id_disc"])})  

        # Suite aux résultats de la recherche
        st.space("large")
        st.write("Vous n'avez pas trouvé le tableau que vous cherchez ?")
        col1, col2, col3 = st.columns([2, 1, 5], gap="small")
        with col1:
            if st.button("Créer le tableau"):
                st.switch_page("pages/creer_discussion.py")
        with col2:
            st.write("ou")
        with col3:
            if st.button("Voir tous les tableaux déjà ajoutés"):
                st.switch_page("pages/discussions.py")

