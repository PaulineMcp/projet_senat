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

for id_partie, titre_partie in (df_all_partie[["id_partie", "titre_partie"]].dropna().drop_duplicates().itertuples(index=False, name=None)):

    st.header(titre_partie)

    # SI 1E PARTIE
    if id_partie[-2:] == "p1":

        # NETTOYAGE DU TABLEAU
        df_first_partie["bloc"] = pd.to_numeric(df_first_partie["bloc"], errors="coerce").astype("Int64")
        df_first_partie = ffill_df(df_first_partie)
        df_first_partie = df_first_partie.sort_values(["ordre_examen_in_partie", "bloc"]).reset_index(drop=True)

        for id_article, article in (df_first_partie[["id_article", "article"]].dropna().drop_duplicates().itertuples(index=False, name=None)):

            # DF PARTIE FILTRÉ PAR ARTICLE
            df_by_article = df_first_partie[df_first_partie["id_article"] == id_article].reset_index(drop=True)
            df_by_article["nom_groupe"] = df_by_article["nom_groupe"].fillna(df_by_article["auteur"])

            # AFFICHAGE DU N° DE L'ARTICLE ET DU RESUME
            display_titre_resume_article(id_article, article, dict_resumes, resumes)              

            # AFFICHAGE DU TABLEAU
            if pd.isna(df_by_article["id_amdt"].iloc[0]):
                st.write("Pas d'amendement sur cet article dans cette partie")
            else :
                df_edite = display_tab(df_by_article, article, id_partie)

            # AFFICHAGE DU VOTE
            est_additionnel = True if "add" in article else False
            # ici il faut quand même enregistrer les resumes des articles additionnels
            display_vote(est_additionnel, dict_votes_articles, id_article, article, votes)

            st.space("xlarge")

            editeurs.append((df_by_article, df_edite))

    # SI AUTRE
    else : 
        # DF FILTRÉ PAR PARTIE
        df_by_partie = df_all_partie[df_all_partie["id_partie"] == id_partie].reset_index(drop=True)
        # DF PARTIE FILTRÉ PAR ARTICLE
        for id_article, article in (df_by_partie[["id_article", "article"]].dropna().drop_duplicates().itertuples(index=False, name=None)):
            df_by_article = df_by_partie[df_by_partie["id_article"] == id_article].reset_index(drop=True).sort_values("ordre_examen_in_partie")

            # AFFICHAGE DU TITRE
        col_gauche, col_centre, col_droite = st.columns([1, 2, 1])
        with col_centre:
            with st.container(horizontal=True, horizontal_alignment="center", vertical_alignment="center"):
                st.markdown(f"<div style='font-size:24px; font-weight:600; margin:0; padding:0;'>{article}</div>", unsafe_allow_html=True,)             

        # AFFICHAGE DU TABLEAU
        if pd.isna(df_by_article["id_amdt"].iloc[0]):
            st.write("Pas d'amendement sur cet article dans cette partie")
        else :
            df_edite = display_tab(df_by_article, article, id_partie)

            st.space("xlarge")
            editeurs.append((df_by_article, df_edite))

###############     SAUVEGARDE DES MODIFS     ###############

if st.button("Sauvegarder les modifications"):

    try :
        with get_db() as conn:
            # Tableaux des amendements (objets et coms)
            for original, edite in editeurs:
                for i in range(len(original)):
                    if not original.loc[i, COLS].equals(edite.loc[i, COLS]):
                        ligne = edite.loc[i]
                        conn.execute(
                            """
                            UPDATE remplissage_ap_amdt
                            SET objet = ?, com = ?, proposition_vote_amdt = ?
                            WHERE id_amdt = ?
                        """,
                            (
                                None if pd.isna(ligne["objet"]) else ligne["objet"],
                                None if pd.isna(ligne["com"]) else ligne["com"],
                                None if pd.isna(ligne["proposition_vote_amdt"]) else ligne["proposition_vote_amdt"],
                                ligne["id_amdt"],
                            ),
                        )
            # Votes
            for id_article, vote in votes.items():
                if vote is None:             
                    continue
                conn.execute(
                    """
                    INSERT INTO remplissage_ap_article (id_article, proposition_vote_article)
                    VALUES (?, ?)
                    ON CONFLICT(id_article) DO UPDATE SET
                        proposition_vote_article = excluded.proposition_vote_article
                    """,
                    (id_article, vide(vote)),
                )

            # Résumés
            for id_article, resume in resumes.items():
                conn.execute(
                    """
                    INSERT INTO remplissage_ap_article (id_article, resume_article)
                    VALUES (?, ?)
                    ON CONFLICT(id_article) DO UPDATE SET
                        resume_article = excluded.resume_article
                    """,
                    (id_article, vide(resume) or None),
                )
    except Exception as e:
            st.error(f"Erreur d'enregistrement : {e}")
    st.success("Modifications enregistrées")