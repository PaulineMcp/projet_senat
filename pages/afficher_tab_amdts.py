############### IMPORTS ###############

import streamlit as st
import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fonctions.fonctions_tableau.get_tab_to_aff import retrieve_tab, retrieve_first_tab, retrieve_infos_disc, retrieve_info_articles
from fonctions.fonctions_tableau.display_tab import display_titre_resume_article, display_vote
from fonctions.fonctions_scrapping_cleaning.fonctions_cleaning import abrev_article, ffill_df, retrieve_article_list, valeurs_identiques
from fonctions.init_discussion import vide
from utils import *
from fonctions.fonctions_tableau.display_tab import display_tab

############### STYLE ###############

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

st.set_page_config(layout="wide")
st.markdown(
    """
    <style>
    /* Supprime la largeur maximale du conteneur principal */
    .stMainBlockContainer {
        max-width: 100% !important;
        width: 100% !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

search = st.query_params.get("discussion_choisie")


############### FONCTION DE SAUVEGARDE ###############

def sauvegarder_modifications(votes : dict, resumes: dict) -> bool:
    """Sauvegarde les modifications dans la bdd."""

    # Récupération de session_state s'il existe, création s'il n'existe pas
    pending = st.session_state.get("pending_amdt", {})
    
    try:
        with get_db() as conn:     
            conn.execute("PRAGMA busy_timeout = 5000")  # Attendre jusqu'à 5 secondes si un autre utilisateur est en train d'effectuer une écriture SQLite

            # Pour chaque amendement modifié
            for id_amdt, modifications in pending.items():

                # Seules les colonnes autorisées
                modifications = {col: modifications[col] for col in ["objet", "com", "proposition_vote_amdt"] if col in modifications}
                if not modifications:
                    continue

                # Liste des colonnes en SQL ("?,?,?,?...")
                colonnes = list(modifications.keys())
                set_sql = ", ".join(f"{col} = ?" for col in colonnes)

                valeurs = []

                # Pour chaque col de chaque amendement modifié
                for col in colonnes:
                    valeur = modifications[col]
                    if pd.isna(valeur):
                        valeur = None
                    valeurs.append(valeur)

                # Requête qui met à jour les nouvelles valeurs de l'amdt
                cursor = conn.execute(
                    f""" UPDATE remplissage_ap_amdt SET {set_sql} WHERE id_amdt = ?""",
                    (*valeurs, id_amdt))

                # Vérifier que l'amendement existe toujours. // ne faut pas un try except ???
                if cursor.rowcount == 0:
                    raise ValueError(
                        f"L'amendement {id_amdt} n'existe plus "
                        "dans la base de données."
                    )

            for id_article, vote in votes.items():

                ancien_vote_db = st.session_state.get(
                    f"dernier_vote_db_{id_article}"
                )

                if valeurs_identiques(vote, ancien_vote_db):
                    continue

                conn.execute("""
                    INSERT INTO remplissage_ap_article
                        (id_article, proposition_vote_article)
                    VALUES (?, ?)
                    ON CONFLICT(id_article) DO UPDATE SET
                        proposition_vote_article = excluded.proposition_vote_article
                    """,
                    (id_article, vide(vote)))

            
            for id_article, resume in resumes.items():
                ancien_resume_db = st.session_state.get(
                    f"dernier_resume_db_{id_article}"
                )

                if valeurs_identiques(resume, ancien_resume_db):
                    continue

                conn.execute("""
                    INSERT INTO remplissage_ap_article
                        (id_article, resume_article)
                    VALUES (?, ?)
                    ON CONFLICT(id_article) DO UPDATE SET
                        resume_article = excluded.resume_article
                    """,
                    (id_article, vide(resume) or None))

            conn.commit()

        # Si l'enregistrement ok, on vide la session
        st.session_state["pending_amdt"] = {}
        return True

    except Exception as e:
        st.error(f"Erreur d'enregistrement : {e}")
        return False


############### AFFICHAGE DE LA PAGE ###############

@st.fragment(run_every="180s")
def afficher_page(search):

    # Récupération des données
    df_first_partie = retrieve_first_tab(search)
    df_all_partie = retrieve_tab(search)
    articles = retrieve_article_list(search).dropna().drop_duplicates()

    df_all_partie["abrev_article"] = (df_all_partie["article"].apply(abrev_article))
    df_first_partie["abrev_article"] = (df_first_partie["article"].apply(abrev_article))

    # Informations de la discussion
    df_infos_disc = retrieve_infos_disc(search)
    titre_discussion = df_infos_disc["titre_disc_long"].iloc[0]
    lien_dossier_discussion = df_infos_disc["lien_dossier"].iloc[0]
    lien_note_discussion = df_infos_disc["lien_note"].iloc[0]

    # Récupérer les infos de votes et résumés déjà remplis
    df_votes_articles = retrieve_info_articles(search)

    dict_votes_articles = dict(zip(
        df_votes_articles["id_article"].astype(str),
        df_votes_articles["proposition_vote_article"]))

    dict_resumes = dict(zip(
        df_votes_articles["id_article"].astype(str),
        df_votes_articles["resume_article"]))

    # Dictionnaire vides qui seront remplis par les modifications du user
    votes = {}
    resumes = {}

    ############### TITRE ###############

    with st.container():
        st.markdown(
            f"<h1 style='text-align:center;'> Amendements liés au {titre_discussion}</h1>", unsafe_allow_html=True)

    ############### BOUTONS ###############

    col_vide, col_buttons = st.columns([4, 1])

    with col_buttons:
        st.link_button("Lien vers la note du groupe",lien_note_discussion)
        st.link_button("Lien vers le dossier législatif", lien_dossier_discussion)
        if st.button("Lien vers la version «sans édition possible»", width="stretch"):
            st.query_params["discussion_choisie"] = search
            st.switch_page("pages/vue_seule_tab_amdts.py", query_params={"discussion_choisie": search})
    st.space("medium")

    ############### TABLEAUX ###############

    # Liste des parties
    parties = (df_all_partie[["id_partie", "titre_partie"]].dropna().drop_duplicates())
    for id_partie, titre_partie in parties.itertuples(index=False,name=None):

        st.header(titre_partie, anchor = id_partie)

        # Si c'est la première partie
        if str(id_partie).endswith("p1"):
            

            # Conversion de la colonne "bloc" en Int64 pour permettre le tri // A terme faut supprimer cette col
            df_first_partie["bloc"] = (pd.to_numeric(df_first_partie["bloc"],errors="coerce").astype("Int64"))

            # Propagation des valeurs de l'ordre d'examen (pour les articles qui n'ont pas d'amendement donc pas d'ordre)
            df_first_partie = ffill_df(df_first_partie)
            df_first_partie = (df_first_partie.sort_values(["ordre_examen_in_partie", "bloc"]).reset_index(drop=True))

            # Liste des articles
            ###articles = (df_first_partie[["id_article", "article"]].dropna().drop_duplicates())
            for id_article, article in articles.itertuples(index=False,name=None):

                df_by_article = (df_first_partie[df_first_partie["id_article"] == id_article])
                df_by_article["nom_groupe"] = (df_by_article["nom_groupe"].fillna(df_by_article["auteur"]))

                # Titre et résumé de l'article
                display_titre_resume_article(id_article, article, dict_resumes, resumes)

                # Tableau des amdts de l'article

                if (df_by_article.empty or pd.isna(df_by_article["id_amdt"].iloc[0])):
                    st.write("Pas d'amendement sur cet article dans cette partie")
                else:
                    display_tab(df_by_article, article, id_partie)

                # Vote sur l'article
                est_additionnel = "add" in article

                display_vote(est_additionnel, dict_votes_articles, id_article, article, votes )
                st.space("xlarge")

        ############### AUTRES PARTIES ###############
        else:
            df_by_partie = (df_all_partie[df_all_partie["id_partie"] == id_partie])

            for id_article, article in articles.itertuples(index=False, name=None):

                df_by_article = (df_by_partie[df_by_partie["id_article"] == id_article])

                # Titre
                col_gauche, col_centre, col_droite = st.columns([1, 2, 1])
                with col_centre:
                    with st.container(horizontal=True, horizontal_alignment="center", vertical_alignment="center"):
                        st.markdown(f"<div style='font-size:24px; " f"font-weight:600; margin:0; padding:0;'>{article}</div>", unsafe_allow_html=True)

                # Tableau
                if (df_by_article.empty or pd.isna(df_by_article["id_amdt"].iloc[0])):  
                    st.write("Pas d'amendement sur cet article dans cette partie")
                else:
                    display_tab(df_by_article, article, id_partie)
                    
                st.space("xlarge")

    ############### SAUVEGARDE ###############

    st.divider()
    if st.button("Sauvegarder les modifications", type="primary"):
        succes = sauvegarder_modifications(votes, resumes)
        if succes:
            st.success( "Modifications enregistrées avec succès !")

############### LANCEMENT DE LA PAGE ###############

if search:
    afficher_page(search)
else:
    st.error("Aucune discussion sélectionnée.")

import sqlite3, tempfile, os

def exporter_bdd() -> bytes:
    with tempfile.TemporaryDirectory() as d:
        chemin = os.path.join(d, "backup.db")
        with get_db() as src:
            dst = sqlite3.connect(chemin)
            src.backup(dst)
            dst.close()
        with open(chemin, "rb") as f:
            return f.read()

st.download_button(
    "Télécharger une copie de la base",
    data=exporter_bdd(),
    file_name="ma_base_backup.db",
    mime="application/octet-stream",
)