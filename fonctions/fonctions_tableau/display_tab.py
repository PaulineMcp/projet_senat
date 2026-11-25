
import pandas as pd
import streamlit as st
#from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

from fonctions.fonctions_tableau.fonctions_affichage import couleur_sort, couleur_parti, couleur_completion, couleur_ss_amdt

OPTIONS = [
    "🟢 Pour",
    "🟡 Plutôt pour",
    "🟠 Plutôt contre",
    "🔴 Contre",
    "⚪️ Abstention",
    "🔵 Selon débat"
]


def put_modifications_into_session_state(base, data_editor_key, row_ids_amdt):
    """Récupère les modifications du data_editor et les stocke par id_amdt."""

    ss = st.session_state
    pending = ss.setdefault("pending_amdt", {})
    state = ss.get(data_editor_key, {})

    for position, modifications in state.get("edited_rows", {}).items():

        position = int(position)

        if position >= len(row_ids_amdt):
            continue

        id_amdt = row_ids_amdt[position]

        if id_amdt is None:
            continue

        entree = pending.setdefault(id_amdt, {})

        for colonne, valeur in modifications.items():
            if colonne in ["objet", "com", "proposition_vote_amdt"]:
                entree[colonne] = valeur


def editeur_stable(df, base, **kwargs) -> pd.DataFrame:
    """ Data editor qui conserve les modifications par id_amdt. Les modifications non sauvegardées restent propres à la session de chaque utilisateur."""

    ss = st.session_state
    pending = ss.setdefault("pending_amdt", {})  # Initialiser un dict "pending_amdt" ou le récupère s'il existe

    # Identifiants dans l'ordre du tableau actuel
    row_ids = [None if pd.isna(id_amdt) else str(id_amdt) for id_amdt in df["id_amdt"].tolist()]

    # Détection des changements de lignes ou de leur ordre
    ids_key = f"ids_{base}"
    version_key = f"version_{base}"
    anciens_ids = ss.get(ids_key)

    if anciens_ids is not None and anciens_ids != row_ids:
        ss[version_key] = ss.get(version_key, 0) + 1

    ss[ids_key] = row_ids

    version = ss.get(version_key, 0)
    widget_key = f"editeur_{base}_{version}"

    # Réapplication des modifications non sauvegardées
    affiche = df.copy()

    for id_amdt, modifications in pending.items():
        masque = affiche["id_amdt"].astype("string") == id_amdt
        for colonne, valeur in modifications.items():
            if colonne in ["objet", "com", "proposition_vote_amdt"]:
                affiche.loc[masque, colonne] = valeur

    # Style du tableau
    style_fn = kwargs.pop("style_fn", None)

    if style_fn is not None:
        affiche = style_fn(affiche)

    # Affichage
    return st.data_editor(
        affiche,
        key=widget_key,
        on_change= put_modifications_into_session_state,
        args=(base, widget_key, row_ids),
        **kwargs
    )

def appliquer_style(df):
        return (
            df.style
            .map(couleur_sort, subset=["sort"])
            .map(couleur_parti, subset=["nom_groupe"])
            .map(couleur_completion, subset=["objet"])
            .map(couleur_ss_amdt, subset=["amdt"])
        )

def display_tab(df_by_article: pd.DataFrame, article: str, id_partie: str) -> pd.DataFrame:

    st.markdown(
    """
    <style>
    div[data-testid="stDataEditor"] [role="gridcell"] {
        padding: 8px 5px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
    
    row_height = 75 #get_row_height(df_by_article,{"objet": 200, "com": 200})
    hauteur_tab = 35 + len(df_by_article) * row_height + 3
    df_edite = editeur_stable(df_by_article,
                            base=f"{id_partie}_{article}",
                            style_fn= appliquer_style,
                            row_height=row_height,
                            column_order=["abrev_article", "lien_article", "amdt","lien_amdt","nom_groupe","objet", "com", "avis_com","avis_gouv","proposition_vote_amdt","sort"],
                            column_config={
                                    "abrev_article": st.column_config.TextColumn("Article", width=80),
                                    "lien_article": st.column_config.LinkColumn("",display_text="🔗",width=30),
                                    "amdt": st.column_config.TextColumn("Amdt",width=60),
                                    "lien_amdt": st.column_config.LinkColumn("",display_text="🔗",width=30),
                                    "nom_groupe": st.column_config.TextColumn("Auteur·rice",width=100),
                                    "objet": st.column_config.TextColumn("Objet", width = 450),
                                    "com": st.column_config.TextColumn("Com",width=300),
                                    "avis_gouv": st.column_config.TextColumn("Avis gouv",width=90),
                                    "avis_com": st.column_config.TextColumn("Avis com",width=90),
                                    "proposition_vote_amdt": st.column_config.SelectboxColumn("Prop. vote",options=OPTIONS,width=100),
                                    "sort": st.column_config.TextColumn("Sort",width=60),},
                            disabled=["article","lien_article","amdt","lien_amdt","nom_groupe","avis_gouv","avis_com","sort"],
                            hide_index=True,
                            height=hauteur_tab,
                            width="content",)

    return(df_edite)


def synchroniser_vote(id_article, key_source, toutes_les_cles):
    """
    Synchronise les selectbox d'un même article.
    """
    nouvelle_valeur = st.session_state[key_source]

    st.session_state[f"vote_commun_{id_article}"] = nouvelle_valeur

    for key in toutes_les_cles:
        if key != key_source:
            st.session_state[key] = nouvelle_valeur


def display_vote( est_additionnel: bool, dict_votes_articles: dict, id_article: str, article: str, votes: dict, id_partie: str):

    if not est_additionnel:
        id_article = str(id_article)
        id_partie = str(id_partie)

        col_vote, col_droite = st.columns(2)

        with col_vote:
            with st.container(horizontal=True):

                st.write(f"Vote sur {article}")

                col_gauche, col_droite = st.columns([1, 1])

                with col_gauche:

                    # Une clé distincte par occurrence
                    key = f"vote_{id_article}_{id_partie}"

                    # Clés communes
                    vote_commun_key = f"vote_commun_{id_article}"
                    db_key = f"dernier_vote_db_{id_article}"
                    cles_key = f"cles_vote_{id_article}"

                    # Valeur enregistrée dans SQLite
                    vote_db = dict_votes_articles.get(id_article)

                    # Initialisation de la liste des widgets
                    if cles_key not in st.session_state:
                        st.session_state[cles_key] = []

                    # Initialisation ou actualisation du vote commun
                    if vote_commun_key not in st.session_state:
                        st.session_state[vote_commun_key] = vote_db
                        st.session_state[db_key] = vote_db

                    else:
                        ancien_vote_db = st.session_state.get(
                            db_key, vote_db
                        )

                        vote_local = st.session_state[vote_commun_key]

                        # Actualisation depuis SQLite uniquement si
                        # aucune modification locale n'est en attente
                        if vote_local == ancien_vote_db:
                            st.session_state[vote_commun_key] = vote_db

                        st.session_state[db_key] = vote_db

                    # Enregistrement de cette occurrence
                    if key not in st.session_state[cles_key]:
                        st.session_state[cles_key].append(key)

                    # Initialisation avant création du widget
                    if key not in st.session_state:
                        st.session_state[key] = st.session_state[
                            vote_commun_key
                        ]

                    votes[id_article] = st.selectbox(
                        f"vote-{id_article}-{id_partie}",
                        OPTIONS,
                        index=None,
                        placeholder="Sélectionner un vote",
                        key=key,
                        label_visibility="collapsed",
                        on_change=synchroniser_vote,
                        args=(
                            id_article,
                            key,
                            st.session_state[cles_key].copy()
                        )
                    )

                    # Valeur commune destinée à la sauvegarde
                    votes[id_article] = st.session_state[vote_commun_key]

                    st.write("Pensez à sauvegarder ! 💾")


def synchroniser_resume(id_article, key_source, toutes_les_cles):
    nouvelle_valeur = st.session_state[key_source]

    st.session_state[f"resume_commun_{id_article}"] = nouvelle_valeur

    # Sauvegarde persistante de la modification
    st.session_state.setdefault("pending_resumes", {})
    st.session_state["pending_resumes"][id_article] = nouvelle_valeur

    for key in toutes_les_cles:
        if key != key_source:
            st.session_state[key] = nouvelle_valeur


def display_titre_resume_article(
    id_article: str,
    article: str,
    id_partie: str,
    dict_resumes: dict,
    resumes: dict
):
    id_article = str(id_article)
    id_partie = str(id_partie)

    # Clé unique pour chaque occurrence
    key = f"resum_{id_article}_{id_partie}"

    # Clés communes à toutes les occurrences
    resume_commun_key = f"resume_commun_{id_article}"
    db_key = f"dernier_resume_db_{id_article}"
    cles_key = f"cles_resume_{id_article}"

    # Récupération du résumé depuis SQLite
    resume_db = dict_resumes.get(id_article)

    if resume_db is None or pd.isna(resume_db):
        resume_db = ""
    else:
        resume_db = str(resume_db)

    # Initialisation de la liste des widgets
    if cles_key not in st.session_state:
        st.session_state[cles_key] = []

    # Initialisation du résumé commun
    if resume_commun_key not in st.session_state:
        st.session_state[resume_commun_key] = resume_db
        st.session_state[db_key] = resume_db

    else:
        ancien_resume_db = st.session_state.get(db_key, resume_db)
        resume_local = st.session_state[resume_commun_key]

        # Actualisation depuis SQLite uniquement si aucune
        # modification locale n'est en attente
        if resume_local == ancien_resume_db and resume_db != ancien_resume_db:
            st.session_state[resume_commun_key] = resume_db

        st.session_state[db_key] = resume_db

    # Enregistrement de cette occurrence
    if key not in st.session_state[cles_key]:
        st.session_state[cles_key].append(key)

    # Initialisation du widget avant sa création
    if key not in st.session_state:
        st.session_state[key] = st.session_state[resume_commun_key]

    # Titre et champ de résumé
    with st.container(
        horizontal=True,
        horizontal_alignment="center",
        vertical_alignment="center"
    ):
        st.markdown(
            f"""
            <div id="article-{id_article}-{id_partie}" class="titre-article"
                style="display:flex; align-items:center; gap:8px;
                font-size:24px; font-weight:600; margin:0; padding:0;">
                <a class="ancre" href="#article-{id_article}-{id_partie}">🔗</a>
                <span>{article}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

        resumes[id_article] = st.text_input(
            key=key,
            label="Résumé",
            label_visibility="collapsed",
            placeholder="Tapez ici le résumé de l'article",
            on_change=synchroniser_resume,
            args=(
                id_article,
                key,
                st.session_state[cles_key].copy()
            )
        )

    # Valeur commune disponible pour la sauvegarde
    resumes[id_article] = st.session_state[resume_commun_key]
