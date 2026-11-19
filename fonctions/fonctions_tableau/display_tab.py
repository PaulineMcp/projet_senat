import pandas as pd
import streamlit as st
from fonctions.fonctions_tableau.fonctions_affichage import couleur_sort
from fonctions.fonctions_tableau.fonctions_affichage import couleur_parti
from fonctions.fonctions_tableau.fonctions_affichage import get_row_height

OPTIONS = ["🟢 Pour", "🟡 Plutôt pour", "🟠 Plutôt contre", "🔴 Contre", "⚪️ Abstention", "🔵 Selon débat"]

def display_tab(df_by_article : pd.DataFrame, article : str, id_partie : str) -> pd.DataFrame :
    row_height = get_row_height(df_by_article, {"objet": 200, "com": 200})
    hauteur_tab = 35 + len(df_by_article) * row_height + 3

    df_stylise = (df_by_article.style
                            .map(couleur_sort, subset = ["sort"])
                            .map(couleur_parti, subset = ["nom_groupe"]))
                
    df_edite = st.data_editor(
        df_stylise,
        row_height = row_height,
        key=f"editeur_{id_partie}_{article}",
        column_order=["abrev_article","lien_article", "amdt", "lien_amdt", "nom_groupe","objet", "com", "avis_com", "avis_gouv", "proposition_vote_amdt", "sort"],
        column_config={
            "abrev_article": st.column_config.TextColumn("Article", width= 75),
            "lien_article": st.column_config.LinkColumn("", display_text="🔗", width=20),
            "amdt": st.column_config.TextColumn("Amdt", width=100),
            "lien_amdt": st.column_config.LinkColumn("", display_text="🔗", width=20),
            "nom_groupe": st.column_config.TextColumn("Auteur·rice", width=140),
            "objet": st.column_config.TextColumn("Objet", width=240),
            "avis_gouv": st.column_config.TextColumn("Avis gouv", width=110),
            "avis_com": st.column_config.TextColumn("Avis com", width=110),
            "proposition_vote_amdt": st.column_config.SelectboxColumn("Prop. vote", options=OPTIONS, width=110),
            "sort": st.column_config.TextColumn("Sort", width=100),
        },
        disabled=["article", "lien_article", "amdt", "lien_amdt", "nom_groupe","avis_gouv", "avis_com", "sort"],
        hide_index=True,
        height = hauteur_tab,
        width="stretch",
    )
    return(df_edite)

def display_vote(est_additionnel : bool, dict_votes_articles : dict, id_article : str, article : str, votes : dict):
    if not est_additionnel:
        col_vote, col_droite = st.columns(2)
        with col_vote:
            with st.container(horizontal=True):
                st.write(f"Vote sur {article}")
                col, _ = st.columns([1, 1])
                with col:
                    vote_actuel = dict_votes_articles.get(str(id_article))
                    votes[id_article] = st.selectbox(
                        f"vote-{id_article}",
                        OPTIONS,
                        index=OPTIONS.index(vote_actuel) if vote_actuel in OPTIONS else None,
                        placeholder="Sélectionner un vote",
                        key=f"vote_{id_article}",
                        label_visibility="collapsed",
                        )

def display_titre_resume_article(id_article : str, article : str, dict_resumes : dict, resumes : dict):
    col_gauche, col_centre, col_droite = st.columns([1, 2, 1])
    with col_centre:
        with st.container(horizontal=True, horizontal_alignment="center", vertical_alignment="center"):
            st.markdown(f"<div style='font-size:24px; font-weight:600; margin:0; padding:0;'>{article}</div>", unsafe_allow_html=True,)

                # Récupère le résumé pour cette clé "id_article"
            resume_actuel = dict_resumes.get(str(id_article))
            if resume_actuel is None or pd.isna(resume_actuel):
                resume_actuel = ""
            resumes[id_article] = st.text_input(
                        key=f"resum_{id_article}",
                        label="Résumé",
                        label_visibility="collapsed",
                        value=resume_actuel,
                        placeholder="Tapez ici le résumé de l'article",
                    ) 