""" Afficher le tableau des amdts SANS possibilité d'éditer """
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

# Import des fonctions
from fonctions.get_tab_to_aff import retrieve_tab
from fonctions.fonctions_cleaning import abrev_article
from fonctions.fonctions_affichage import couleur_sort
from fonctions.fonctions_affichage import get_row_height
from utils import get_conn

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
df_global = retrieve_tab(search)
df_global["abrev_article"] = df_global["article"].apply(abrev_article)
print("Récupération du tableau global : OK !")

conn = get_conn()

# Infos de la discussion
df_infos_disc = pd.read_sql(
    """
    SELECT *
    FROM discussion
    WHERE id_disc = ?
    """,
    conn,
    params=(search,),
)

titre_discussion = df_infos_disc["titre_disc_long"].iloc[0]
lien_dossier_discussion = df_infos_disc["lien_dossier"].iloc[0]
lien_note_discussion = df_infos_disc["lien_note"].iloc[0]
url = df_infos_disc["url_disc"].iloc[0]
print("Récupération des infos de la disc : OK !")

# Votes et résumés existants des articles
df_votes_articles = pd.read_sql(
    """
    SELECT remplissage_ap_article.id_article,
           remplissage_ap_article.resume_article,
           remplissage_ap_article.proposition_vote_article
    FROM remplissage_ap_article
    JOIN articles
        ON articles.id_article = remplissage_ap_article.id_article
    WHERE articles.id_disc = ?
    """,
    conn,
    params=(search,),
)

dict_votes_articles = dict(zip(
    df_votes_articles["id_article"].astype(str),
    df_votes_articles["proposition_vote_article"],
))
dict_resumes = dict(zip(
    df_votes_articles["id_article"].astype(str),
    df_votes_articles["resume_article"],
))
conn.close()
print("Récupération des infos sur les votes et résumés : OK !")


##############################     PAGE       ############################
# Titre
with st.container():
    st.markdown(
        f"<h1 style='text-align:center;'>Amendements liés au {titre_discussion}</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<h2 style='text-align:center;'>Vue seule</h2>",
        unsafe_allow_html=True,
    )


# Boutons
col_vide, col_buttons = st.columns([4, 1])
with col_buttons:
    st.link_button("Lien vers la note du groupe", lien_note_discussion)
    st.link_button("Lien vers le dossier législatif", lien_dossier_discussion)
st.space("medium")


# Injection des données dans un tableau par article
for article in df_global["id_article"].unique():
    with st.container(border=True):

        # df filtré par article
        df_by_article = df_global[df_global["id_article"] == article].reset_index(drop=True)
        row_height = get_row_height(df_by_article, {"objet": 200, "com": 200})
        hauteur_tab = (len(df_by_article) + 1) * row_height + 3
        est_additionnel = True if "add" in article else False
        libelle = df_by_article["article"].iloc[0].replace("(nouveau)","").replace("(supprimé)","").replace("(Supprimé)","")

        # AFFICHAGE DU N° DE L'ARTICLE ET DU RESUME
        col_gauche, col_centre, col_droite = st.columns([1, 2, 1])
        with col_centre:
            with st.container(horizontal=True, horizontal_alignment="center", vertical_alignment="center"):
                st.markdown(
                    f"<div style='font-size:24px; font-weight:600; margin:0; padding:0;'>{libelle}</div>", unsafe_allow_html=True,)

                # Récupère le résumé pour cette clé "article"
                resume_actuel = dict_resumes.get(str(article))
                if resume_actuel is None or pd.isna(resume_actuel):
                    resume_actuel = ""
                st.write(resume_actuel)

        # AFFICHAGE DU TABLEAU
        df_style = df_by_article.style.map(couleur_sort, subset=["sort"])

        if pd.isna(df_by_article["amdt"].iloc[0]):
            st.write("Pas d'amendement sur cet article")

        else:
            st.dataframe(
                df_style,
                row_height = row_height,
                column_order=["abrev_article", "lien_article", "amdt", "lien_amdt", "nom_groupe","objet", "com", "avis_com", "avis_gouv", "proposition_vote_amdt", "sort"],
                column_config={
                    "abrev_article": st.column_config.TextColumn("Article", width=100),
                    "lien_article": st.column_config.LinkColumn("", display_text="🔗", width=30),
                    "amdt": st.column_config.TextColumn("Amdt", width=100),
                    "lien_amdt": st.column_config.LinkColumn("", display_text="🔗", width=30),
                    "nom_groupe": st.column_config.TextColumn("Auteur·rice", width=150),
                    "objet": st.column_config.TextColumn("Objet", width=200),
                    "avis_gouv": st.column_config.TextColumn("Avis gouv", width=110),
                    "avis_com": st.column_config.TextColumn("Avis com", width=110),
                    "proposition_vote_amdt": st.column_config.SelectboxColumn("Prop. vote", options=OPTIONS, width=110),
                    "sort": st.column_config.TextColumn("Sort", width=100),
                },
                hide_index=True,
                height = hauteur_tab,
                width="stretch",
            )

        # AFFICHAGE DU VOTE (pas pour les articles additionnels)
        if not est_additionnel:
            col_vote, col_droite = st.columns(2)
            with col_vote:
                with st.container(horizontal=True):
                    st.write(f"Vote sur l'{libelle}")
                    col, _ = st.columns([1, 1])
                    with col:
                        vote_actuel = dict_votes_articles.get(str(article))
                        if vote_actuel is None or pd.isna(vote_actuel):
                            vote_actuel = "Non-défini"
                        st.write(vote_actuel)

    st.space("xlarge")