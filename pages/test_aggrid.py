from st_aggrid import AgGrid, GridOptionsBuilder

""" Afficher le tableau des amdts avec la possibilité d'éditer """

###############     IMPORTS     ###############
# Import des librairies
import streamlit as st
import sys
from pathlib import Path
import pandas as pd

# CONSTANTES
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

OPTIONS = ["🟢 Pour", "🟡 Plutôt pour", "🟠 Plutôt contre", "🔴 Contre", "⚪️ Abstention", "🔵 Selon débat"]

COLS = ["objet", "com", "proposition_vote_amdt"]

# Import des fonctions
from fonctions.fonctions_tableau.get_tab_to_aff import retrieve_tab, retrieve_first_tab, retrieve_infos_disc, retrieve_info_articles
from fonctions.fonctions_tableau.display_tab import display_titre_resume_article, display_tab, display_vote
from fonctions.fonctions_scrapping_cleaning.fonctions_cleaning import abrev_article, ffill_df
from fonctions.init_discussion import vide
#from fonctions.fonctions_tableau.fonctions_affichage import couleur_parti
#from fonctions.fonctions_tableau.fonctions_affichage import get_row_height
from utils import *

###############     STYLE     ###############
st.markdown(
    """
    <style>
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-color: rgba(250, 250, 250, 0.1) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

###############     RECUPERATION DES DONNEES    ###############
search = st.query_params.get("discussion_choisie")  # id de la discussion choisie

# Tableau global
df_first_partie = retrieve_first_tab(search)
df_all_partie = retrieve_tab(search)

df_all_partie["abrev_article"] = df_all_partie["article"].apply(abrev_article)
df_first_partie["abrev_article"] = df_first_partie["article"].apply(abrev_article)
# fonction pour afficher gouv ou groupe

print("Récupération du tableau global : OK !")

# Infos de la discussion
df_infos_disc = retrieve_infos_disc(search)

titre_discussion = df_infos_disc["titre_disc_long"].iloc[0]
lien_dossier_discussion = df_infos_disc["lien_dossier"].iloc[0]
lien_note_discussion = df_infos_disc["lien_note"].iloc[0]
url = df_infos_disc["url_disc"].iloc[0]

print("Récupération des infos de la disc : OK !")

# Votes et résumés existants des articles
df_votes_articles = retrieve_info_articles(search)

dict_votes_articles = dict(zip(
    df_votes_articles["id_article"].astype(str),
    df_votes_articles["proposition_vote_article"],
))

dict_resumes = dict(zip(
    df_votes_articles["id_article"].astype(str),
    df_votes_articles["resume_article"],
))

print("Récupération des infos sur les votes et résumés : OK !")

# Variable pour envoyer les modifs vers la BDD
editeurs = []   # couples 
votes = {}      # votes saisis par article
resumes = {}    # résumés saisis par article

###############     PAGE     ###############

# Titre
with st.container():
    st.markdown(
        f"<h1 style='text-align:center;'>Amendements liés au {titre_discussion}</h1>",
        unsafe_allow_html=True,
    )

# Boutons
col_vide, col_buttons = st.columns([4, 1])
with col_buttons:
    st.link_button("Lien vers la note du groupe", lien_note_discussion)
    st.link_button("Lien vers le dossier législatif", lien_dossier_discussion)
    if st.button("Lien vers la version «sans édition possible»", width="stretch"):
                        st.query_params["discussion_choisie"] = search
                        st.switch_page("pages/vue_seule_tab_amdts.py",
                                       query_params={"discussion_choisie": search})
st.space("medium")

###############     TABLEAU     ###############