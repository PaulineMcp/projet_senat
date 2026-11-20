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

def editeur_stable(df, base, **kwargs):
    """data_editor qui garde les saisies par id_amdt, même si le tableau change entre deux reruns.
    df doit contenir les colonnes id_amdt et version ; base identifie le tableau (ex. f"{id_partie}_{id_article}")."""
    ss = st.session_state
    pending = ss.setdefault(f"pending_{base}", {})     # {id_amdt: {"com": "...", "_version": 3}}
    prev = ss.get(f"prev_{base}")                      # (ids, versions) du tableau passé au rerun précédent
    ver = ss.get(f"ver_{base}", 0)
    key = f"editeur_{base}_{ss.get('epoch', 0)}_{ver}"

    # 1. Traduire les saisies "par position" du widget en saisies "par id_amdt"
    state = ss.get(key)
    if state and prev:
        ids_prev, versions_prev = prev
        for pos, changes in state.get("edited_rows", {}).items():
            i = int(pos)
            entree = pending.setdefault(ids_prev[i], {"_version": versions_prev[i]})
            entree.update(changes)

    # 2. Lignes différentes d'un rerun à l'autre : widget vierge, tout est déjà dans pending
    ids = list(df["id_amdt"])
    if prev and prev[0] != ids:
        ver += 1
        ss[f"ver_{base}"] = ver
        key = f"editeur_{base}_{ss.get('epoch', 0)}_{ver}"

    # 3. Réappliquer les saisies sur le tableau frais, par id_amdt
    affiche = df.copy()
    for id_amdt, entree in pending.items():
        masque = affiche["id_amdt"] == id_amdt
        if masque.any():
            for col, val in entree.items():
                if col != "_version":
                    affiche.loc[masque, col] = val

    ss[f"prev_{base}"] = (ids, list(df["version"]))
    return st.data_editor(affiche, key=key, **kwargs)