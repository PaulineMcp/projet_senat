
############### IMPORTS ###############

import streamlit as st
import sys
import sqlite3
import tempfile
import os
import math

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fonctions.fonctions_tableau.get_tab_to_aff import retrieve_tab, retrieve_infos_disc,retrieve_info_articles

from fonctions.fonctions_tableau.display_tab import (
    display_titre_resume_article,
    display_vote,
    display_tab
)

from fonctions.fonctions_scrapping_cleaning.fonctions_cleaning import (
    abrev_article,
    ffill_df
)

from fonctions.init_discussion import vide
from utils import *


############### STYLE IMPRESSION ###############

st.markdown("""
<style>
@media print {
    [data-testid="stVerticalBlock"] {
        gap: 0.3rem !important;
    }

    [data-testid="stElementContainer"] {
        margin-bottom: 0 !important;
    }
}
</style>
""", unsafe_allow_html=True)


############### FONCTIONS GENERALES ###############
import streamlit.components.v1 as components


def afficher_pagination(page_actuelle, nb_pages, page_key, search, position):

    with st.container(
        horizontal=True,
        horizontal_alignment="center",
        vertical_alignment="center"
    ):
        for page in range(1, nb_pages + 1):

            if st.button(
                str(page),
                key=f"page-{search}-{position}-{page}",
                type="primary" if page_actuelle == page else "secondary"
            ):
                st.session_state[page_key] = page
                st.rerun()

def valeurs_identiques(a, b):
    """Compare deux valeurs scalaires en tenant compte des valeurs nulles."""

    try:
        a_est_null = pd.isna(a)
        b_est_null = pd.isna(b)

        if a_est_null and b_est_null:
            return True

        if a_est_null or b_est_null:
            return False

    except (TypeError, ValueError):
        pass

    return a == b


def get_nb_pages(nb_bloc: int) -> int:
    """Calcule le nombre de pages avec 5 blocs par page."""

    if nb_bloc <= 0:
        return 0

    return math.ceil(nb_bloc / 5)


def get_borne_min(page: int) -> int:
    """Retourne le premier numéro de bloc global de la page."""

    return ((page - 1) * 5) + 1



def numeroter_blocs_globaux(df: pd.DataFrame) -> pd.DataFrame:

    df["bloc"] = pd.to_numeric(df["bloc"],errors="coerce").astype("Int64")
    df["ordre_examen_in_partie"] = pd.to_numeric(df["ordre_examen_in_partie"], errors="coerce"
    )


    # Conserver l'ordre d'apparition des parties.
    parties = (
        df["id_partie"]
        .dropna()
        .drop_duplicates()
        .tolist()
    )

    dernier_bloc_global = 0
    dfs = []

    for id_partie in parties:

        df_partie = df[
            df["id_partie"] == id_partie
        ].copy()

        # Déterminer le premier ordre d'examen de chaque bloc.
        ordre_blocs = (
            df_partie[df_partie["bloc"].notna()]
            .groupby("bloc", as_index=False)
            ["ordre_examen_in_partie"]
            .min()
            .sort_values(
                ["ordre_examen_in_partie", "bloc"],
                na_position="last"
            )
        )

        blocs_a_conserver = ordre_blocs["bloc"].tolist()

        # Numérotation continue entre les parties.
        correspondance = {
            bloc: dernier_bloc_global + numero
            for numero, bloc in enumerate(
                blocs_a_conserver,
                start=1
            )
        }

        df_partie["bloc_global"] = (
            df_partie["bloc"]
            .map(correspondance)
            .astype("Int64")
        )

        if correspondance:
            dernier_bloc_global = max(
                correspondance.values()
            )

        dfs.append(df_partie)

    # Conserver également les lignes sans partie.
    df_sans_partie = df[
        df["id_partie"].isna()
    ].copy()

    df_sans_partie["bloc_global"] = pd.Series(
        pd.NA,
        index=df_sans_partie.index,
        dtype="Int64"
    )

    if not df_sans_partie.empty:
        dfs.append(df_sans_partie)

    if not dfs:
        df["bloc_global"] = pd.Series(
            pd.NA,
            index=df.index,
            dtype="Int64"
        )
        return df

    return pd.concat(
        dfs,
        ignore_index=True
    )





############### SAUVEGARDE ###############


def sauvegarder_modifications() -> bool:
    """
    Sauvegarde les modifications en attente dans la base.

    Les trois sources de modifications sont directement récupérées
    depuis st.session_state :
        - pending_amdt
        - pending_votes
        - pending_resumes
    """

    pending_amdt = st.session_state.get(
        "pending_amdt",
        {}
    )

    pending_votes = st.session_state.get(
        "pending_votes",
        {}
    )

    pending_resumes = st.session_state.get(
        "pending_resumes",
        {}
    )

    conn = None

    try:

        with get_db() as conn:

            conn.execute(
                "PRAGMA busy_timeout = 5000"
            )

            # --------------------------------------------------
            # 1. SAUVEGARDE DES AMENDEMENTS
            # --------------------------------------------------

            colonnes_autorisees = {
                "objet",
                "com",
                "proposition_vote_amdt"
            }

            for id_amdt, modifications in pending_amdt.items():

                modifications_valides = {
                    colonne: valeur
                    for colonne, valeur in modifications.items()
                    if colonne in colonnes_autorisees
                }

                if not modifications_valides:
                    continue

                colonnes = list(
                    modifications_valides.keys()
                )

                set_sql = ", ".join(
                    f"{colonne} = ?"
                    for colonne in colonnes
                )

                valeurs = []

                for colonne in colonnes:

                    valeur = modifications_valides[colonne]

                    if pd.isna(valeur):
                        valeur = None

                    valeurs.append(valeur)

                cursor = conn.execute(
                    f"""
                    UPDATE remplissage_ap_amdt
                    SET {set_sql}
                    WHERE id_amdt = ?
                    """,
                    (*valeurs, id_amdt)
                )

                if cursor.rowcount == 0:
                    raise ValueError(
                        f"L'amendement {id_amdt} "
                        "n'existe plus dans la base de données."
                    )

            # --------------------------------------------------
            # 2. SAUVEGARDE DES VOTES
            # --------------------------------------------------

            for id_article, vote in pending_votes.items():

                ancien_vote_db = st.session_state.get(
                    f"dernier_vote_db_{id_article}"
                )

                if valeurs_identiques(
                    vote,
                    ancien_vote_db
                ):
                    continue

                conn.execute(
                    """
                    INSERT INTO remplissage_ap_article (
                        id_article,
                        proposition_vote_article
                    )
                    VALUES (?, ?)

                    ON CONFLICT(id_article) DO UPDATE SET
                        proposition_vote_article =
                        excluded.proposition_vote_article
                    """,
                    (
                        id_article,
                        vide(vote)
                    )
                )

            # --------------------------------------------------
            # 3. SAUVEGARDE DES RESUMES
            # --------------------------------------------------

            for id_article, resume in pending_resumes.items():

                ancien_resume_db = st.session_state.get(
                    f"dernier_resume_db_{id_article}"
                )

                if valeurs_identiques(
                    resume,
                    ancien_resume_db
                ):
                    continue

                resume_a_sauvegarder = (
                    vide(resume) or None
                )

                conn.execute(
                    """
                    INSERT INTO remplissage_ap_article (
                        id_article,
                        resume_article
                    )
                    VALUES (?, ?)

                    ON CONFLICT(id_article) DO UPDATE SET
                        resume_article = excluded.resume_article
                    """,
                    (
                        id_article,
                        resume_a_sauvegarder
                    )
                )

            conn.commit()

        # ------------------------------------------------------
        # 4. NETTOYAGE APRES SAUVEGARDE REUSSIE
        # ------------------------------------------------------

        st.session_state["pending_amdt"] = {}
        st.session_state["pending_votes"] = {}
        st.session_state["pending_resumes"] = {}

        # Mise à jour des valeurs de référence en session.
        for id_article, vote in pending_votes.items():
            st.session_state[
                f"dernier_vote_db_{id_article}"
            ] = vide(vote)

        for id_article, resume in pending_resumes.items():
            st.session_state[
                f"dernier_resume_db_{id_article}"
            ] = vide(resume) or None

        return True

    except Exception as e:

        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass

        st.error(
            f"Erreur d'enregistrement : {e}"
        )

        return False


############### STYLE GENERAL ###############


st.markdown(
    """
    <style>
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-color: rgba(250, 250, 250, 0.1) !important;
    }

    .stMainBlockContainer {
        max-width: 100% !important;
        width: 100% !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)


############### DISCUSSION SELECTIONNEE ###############


search = st.query_params.get(
    "discussion_choisie"
)


############### AFFICHAGE DE LA PAGE ###############


@st.fragment(run_every="1800s")
def afficher_page(search):

    # --------------------------------------------------
    # 1. RECUPERATION DES DONNEES
    # --------------------------------------------------

    df_all_partie = retrieve_tab(search)
    df_all_partie["nom_groupe"] = (df_all_partie["nom_groupe"].fillna(df_all_partie["auteur"]))

    if df_all_partie.empty:
        st.warning(
            "Aucune donnée disponible pour cette discussion."
        )
        return

    df_all_partie = df_all_partie.copy()

    df_all_partie["abrev_article"] = (
        df_all_partie["article"].apply(abrev_article)
    )

    # Numérotation de TOUS les blocs, sans filtrage des amendements.
    df_all_partie["bloc"] = pd.to_numeric(df_all_partie["bloc"],errors="coerce").astype("Int64")
    df_all_partie = df_all_partie.sort_values("bloc")

    # Liste des parties dans leur ordre d'apparition.
    parties = (
        df_all_partie[
            ["id_partie", "titre_partie"]
        ]
        .dropna(subset=["id_partie"])
        .drop_duplicates(
            subset=["id_partie"],
            keep="first"
        )
    )

    # --------------------------------------------------
    # 2. INFORMATIONS DE LA DISCUSSION
    # --------------------------------------------------

    df_infos_disc = retrieve_infos_disc(search)

    if df_infos_disc.empty:
        st.error(
            "Impossible de récupérer les informations de la discussion."
        )
        return

    titre_discussion = (
        df_infos_disc["titre_disc_long"].iloc[0]
    )

    lien_dossier_discussion = (
        df_infos_disc["lien_dossier"].iloc[0]
    )

    lien_note_discussion = (
        df_infos_disc["lien_note"].iloc[0]
    )

    # --------------------------------------------------
    # 3. INFORMATIONS DES VOTES ET RESUMES
    # --------------------------------------------------

    df_votes_articles = retrieve_info_articles(search)

    if df_votes_articles.empty:
        dict_votes_articles = {}
        dict_resumes = {}
    else:
        dict_votes_articles = dict(
            zip(
                df_votes_articles["id_article"].astype(str),
                df_votes_articles["proposition_vote_article"]
            )
        )

        dict_resumes = dict(
            zip(
                df_votes_articles["id_article"].astype(str),
                df_votes_articles["resume_article"]
            )
        )

    # Dictionnaires de modifications en attente.
    st.session_state.setdefault(
        "pending_resumes",
        {}
    )

    st.session_state.setdefault(
        "pending_votes",
        {}
    )

    st.session_state.setdefault(
        "pending_amdt",
        {}
    )

    resumes = st.session_state["pending_resumes"]
    votes = st.session_state["pending_votes"]

    # --------------------------------------------------
    # 4. TITRE
    # --------------------------------------------------

    with st.container():

        st.markdown(
            f"""
            <h1 style='text-align:center;'>
                Amendements liés au {titre_discussion}
            </h1>
            """,
            unsafe_allow_html=True
        )

    # --------------------------------------------------
    # 5. BOUTONS ET LIENS
    # --------------------------------------------------

    col_vide, col_buttons = st.columns([4, 1])

    with col_buttons:

        if lien_note_discussion:
            st.link_button(
                "Lien vers la note du groupe",
                lien_note_discussion
            )

        if lien_dossier_discussion:
            st.link_button(
                "Lien vers le dossier législatif",
                lien_dossier_discussion
            )

        if st.button(
            "Lien vers la version «sans édition possible»",
            width="stretch"
        ):

            st.query_params["discussion_choisie"] = search

            st.switch_page(
                "pages/vue_seule_tab_amdts.py"
            )

    st.space("medium")

    # --------------------------------------------------
    # 6. PAGINATION
    # --------------------------------------------------

    max_bloc = df_all_partie["bloc"].max()

    nb_pages = get_nb_pages(int(max_bloc))
    page_key = f"page_actuelle_{search}"

    if page_key not in st.session_state:
        st.session_state[page_key] = 1
    st.session_state[page_key] = min(max(1, st.session_state[page_key]),nb_pages)

    page_actuelle = st.session_state[page_key]

    borne_min = get_borne_min(page_actuelle)
    borne_max = borne_min + 4

    # Boutons de pagination.
    with st.container(
        horizontal=True,
        horizontal_alignment="center",
        vertical_alignment="center"
    ):

        afficher_pagination(page_actuelle, nb_pages, page_key, search, "haut")

    # --------------------------------------------------
    # 7. AFFICHAGE DES PARTIES ET DES ARTICLES
    # --------------------------------------------------

    for id_partie, titre_partie in parties.itertuples(index=False, name=None):

        df_all_partie["id_partie"] = df_all_partie["id_partie"].ffill()
        df_partie = df_all_partie[df_all_partie["id_partie"] == id_partie]
        df_partie = df_partie.sort_values(["bloc", "ordre_examen_in_partie"])

        if borne_min == 1:
            borne_min = -1

        df_page = df_partie[df_partie["bloc"].between(borne_min, borne_max)]

        st.header(titre_partie)

        articles = (
            df_page[["bloc", "id_article", "article"]]
            .drop_duplicates(subset=["bloc", "id_article", "article"])
            .sort_values(["bloc", "id_article"])
        )

        for bloc, id_article, article in articles.itertuples(index=False, name=None):

            df_by_article = df_page[
                (df_page["bloc"] == bloc)
                & (df_page["id_article"] == id_article)
            ]

            df_amdt_actifs = df_by_article[
                df_by_article["amdt"].notna()
                & (pd.to_numeric(df_by_article["is_active"], errors="coerce") == 1)
            ].sort_values("ordre_examen_in_partie")

            display_titre_resume_article(
                id_article, article, id_partie, dict_resumes, resumes
            )

            est_article_add = "add" in str(article).lower()

            if df_amdt_actifs.empty:
                st.write("Pas d'amendement")
                if not est_article_add:
                    
                    display_vote(
                        False, dict_votes_articles, id_article, article, votes, id_partie
                    )

            else:

                display_tab(df_amdt_actifs, article, id_partie)

                if not est_article_add:
                    display_vote(
                        False, dict_votes_articles, id_article, article, votes, id_partie
                    )

            # Espacement systématique, y compris pour les articles add sans amendement
            st.space("xlarge")

        afficher_pagination(page_actuelle, nb_pages, page_key, search, "bas")        


    # --------------------------------------------------
    # 8. SAUVEGARDE
    # --------------------------------------------------

        if st.button(
            "Sauvegarder les modifications",
            type="primary"
        ):

            succes = sauvegarder_modifications()

            if succes:
                st.success(
                    "Modifications enregistrées avec succès !"
                )


############### LANCEMENT DE LA PAGE ###############


if search:

    afficher_page(search)

    st.divider()

else:

    st.error(
        "Aucune discussion sélectionnée."
    )


############### EXPORT DE LA BASE DE DONNEES ###############


def exporter_bdd() -> bytes:

    with tempfile.TemporaryDirectory() as dossier:

        chemin = os.path.join(
            dossier,
            "backup.db"
        )

        with get_db() as src:

            dst = sqlite3.connect(chemin)

            try:
                src.backup(dst)
            finally:
                dst.close()

        with open(chemin, "rb") as fichier:
            return fichier.read()


st.download_button(
    "Télécharger une copie de la base en .DB",
    data=exporter_bdd(),
    file_name="ma_base_backup.db",
    mime="application/octet-stream"
)



############### EXPORT CSV ###############


def convert_for_download(df):

    return df.to_csv(
        index=False
    ).encode("utf-8-sig")


if search:

    df_for_download = retrieve_tab(search)

    if not df_for_download.empty:

        df_for_download = df_for_download.copy()

        df_for_download["abrev_article"] = (
            df_for_download["article"].apply(abrev_article)
        )

        df_for_download["bloc"] = pd.to_numeric(
            df_for_download["bloc"],
            errors="coerce"
        ).astype("Int64")

        df_for_download = df_for_download.sort_values(
            [
                "id_partie",
                "bloc",
                "ordre_examen_in_partie"
            ],
            na_position="last"
        )

        df_for_download = ffill_df(
            df_for_download
        )

        df_for_download["nom_groupe"] = (
            df_for_download["nom_groupe"].fillna(
                df_for_download["auteur"]
            )
        )

        # Filtrage des amendements actifs uniquement pour l'export.
        df_for_download = df_for_download[
            df_for_download["id_amdt"].notna()
            & (
                pd.to_numeric(
                    df_for_download["is_active"],
                    errors="coerce"
                ) == 1
            )
        ].copy()

        colonnes_csv = [
            "abrev_article",
            "amdt",
            "nom_groupe",
            "lien_amdt",
            "lien_article",
            "objet",
            "com",
            "avis_com",
            "avis_gouv",
            "proposition_vote_amdt",
            "sort"
        ]

        df_for_download = df_for_download[
            colonnes_csv
        ]

        csv = convert_for_download(
            df_for_download
        )

        st.download_button(
            label="Télécharger en CSV",
            data=csv,
            file_name="tableau.csv",
            mime="text/csv",
            icon=":material/download:"
        )
