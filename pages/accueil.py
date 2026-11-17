""" Page d'accueil """

###############     IMPORTS     ###############

# Import des librairies
import streamlit as st 
import pandas as pd
import requests
from bs4 import BeautifulSoup
import sqlite3
from pathlib import Path

###############     PAGE     ###############

col_gauche, col_centre, col_droite = st.columns([1,3,1])
with col_centre :
    with st.container(width=800):
        st.space("xxlarge")

        st.title("Bienvenue sur le site de suivi des amendements GEST*")
        st.write("Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occ")

        st.space("large")

        with st.container(key="boutons_navigation"):
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Rechercher un tableau", width="stretch"):
                    st.switch_page("pages/recherche.py")

            with col2:   
                if st.button("Créer un tableau", width="stretch"):
                    st.switch_page("pages/creer_discussion.py")

            with col3:
                if st.button("Voir la liste complète des tableaux déjà créés",wrap = True):
                    st.switch_page("pages/discussions.py")

    st.space("large")
    with st.container():
        col1, col2,col3 = st.columns([1,1,1])
        with col2:
            with st.container(horizontal= True, vertical_alignment="center"):
                st.write("Besoin d'aide ?")
                if st.button("Voir le tutoriel", width="stretch") :
                                st.switch_page("pages/tutoriel.py")
            