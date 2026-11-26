
############### IMPORTS ###############

import streamlit as st
import sys
import sqlite3
import tempfile
import os
import math
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import Paragraph
from fonctions.exports import exporter_bdd
import re

from pathlib import Path
import pandas as pd
from fonctions.exports import exporter_csv
from pages.pdf_generation import df2table, generer_pdf, encadrer_vote, style_article, style_partie, style_vote, style_titre, generer_content

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fonctions.fonctions_tableau.get_tab_to_aff import retrieve_infos_disc,retrieve_info_articles, retrieve_1_partie, retrieve_tab_autres_parties, retrieve_tab

from fonctions.fonctions_tableau.display_tab import display_titre_resume_article, display_vote, display_tab
from fonctions.fonctions_scrapping_cleaning.fonctions_cleaning import abrev_article, ffill_df

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
    borne_min = ((page - 1) * 5) + 1
    if borne_min == 1:
        borne_min = -1
    return borne_min

def get_borne_max(borne_min : int) -> int :
    if borne_min == -1:
        borne_max = 5
    else :
        borne_max = borne_min + 4
    return(borne_max)

def propager_ordre_examen(df) -> int :
    """Fonction pour trouver l'emplacement des articles sans amendements"""
    for index, row in df.iterrows():
        print(f"ARTICLE REGARDE : {df.loc[index, "article"]}")
        #if (df.loc[index, "ordre_examen_in_partie"] is None and df.loc[index, "ordre_partie"] is None) :
        if (
            pd.isna(df.loc[index, "ordre_examen_in_partie"])
            and pd.isna(df.loc[index, "ordre_partie"])
        ):
            #df.loc[index, "ordre_examen_in_partie"] = 999999
            df.loc[index, "ordre_partie"] = 1
            row["ordre_partie"] = 1

            id_disc = df.loc[index, "id_disc"]
            article = df.loc[index,"article"]

            num_article = article.replace(f"{id_disc}-", "")
            match = re.search(r"\d+", num_article)

            if not match: # cas des articles uniques, liminaires (pas des chiffres)
                continue

            chiffre_article = int(match.group())
            chiffre_prev_article = chiffre_article - 1

            if chiffre_article == 1 :
                df.loc[index, "ordre_examen_in_partie"] = 9 # uniquement valable pour plf 2027

            else : 
                if "addav" in num_article :
                    print("XXX")
                #    if f"{id_disc}-addap{chiffre_prev_article}" in df["article"] :
                #        filtered_df = df[df["article"] == f"{id_disc}-addap{chiffre_prev_article}"] & df[["is_active"] == 1] # que pour les is active
                #        row["ordre_examen_in_partie"] = filtered_df["ordre_examen_in_partie"].max()
                elif "addap" in num_article :
                    print("XXX")
                #        filtered_df = df[df["article"] == f"{id_disc}-{chiffre_prev_article}"] & df[["is_active"] == 1]
                #        row["ordre_examen_in_partie"] = filtered_df["ordre_examen_in_partie"].max()
                else:  # article principal
                    if f"{id_disc}-addap{chiffre_prev_article}" in df["id_article"].values:
                        filtered_df = df[
                            (df["id_article"] == f"{id_disc}-addap{chiffre_prev_article}")
                            & (df["is_active"] == 1)
                            & (df["ordre_examen_in_partie"].notna())
                        ]
                    else:
                        print("cas B")
                        print(f"Article précédent = {id_disc}-{chiffre_prev_article}")

                        filtered_df = pd.DataFrame()

                        while chiffre_prev_article >= 1:
                            filtered_df = df[
                                (df["id_article"] == f"{id_disc}-{chiffre_prev_article}")
                                & (df["is_active"].isin([1, None]) | df["is_active"].isna())
                                & (df["ordre_examen_in_partie"].notna())
                            ]

                            print(filtered_df)

                            if not filtered_df.empty:
                                break

                            chiffre_prev_article -= 1

                    if not filtered_df.empty:
                        df.loc[index, "ordre_examen_in_partie"] = filtered_df["ordre_examen_in_partie"].max()
                    else:
                        print("Aucun article précédent avec un ordre d'examen trouvé")
        else :
            print("Contient bien un ordre et tout ce qu'il faut")
    return(df)




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

    pending_amdt = st.session_state.get("pending_amdt",{})
    pending_votes = st.session_state.get("pending_votes",{})
    pending_resumes = st.session_state.get("pending_resumes",{})

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





############### AFFICHAGE DE LA PAGE ###############


@st.fragment(run_every="1800s")
def afficher_page(search):

    titre_partie = ""
    id_partie = "2026-2027-SCE-155-p1"

    # --------------------------------------------------
    # 1. RECUPERATION DES DONNEES
    # --------------------------------------------------

    # Ce nettoyage devrait être dégé dans la requete
    df_all_partie = retrieve_tab(search)

    if df_all_partie.empty:
        st.warning("Aucune donnée disponible pour cette discussion.")
        return
    
    # + ajouter le "première partie en string" + id_partie

    #df_all_partie["ordre_partie"] = df_all_partie["ordre_partie"].fillna(value=1)
    df_all_partie = df_all_partie.sort_values(["ordre_partie","ordre_examen_in_partie"])
     # les articles sans amendements sont attribués à la premières partie par défaut
    
    df_all_partie = propager_ordre_examen(df_all_partie)

#    df_all_partie["ordre_examen_in_partie"] = df_all_partie["ordre_examen_in_partie"].ffill()
    df_all_partie = df_all_partie.sort_values(["ordre_partie","ordre_examen_in_partie"])
    df_all_partie = df_all_partie[(df_all_partie["is_active"] == 1)|(df_all_partie["id_amdt"].isna())]
    df_all_partie = df_all_partie.sort_values(["ordre_partie","ordre_examen_in_partie"])
    # Ecriture des blocs globaux
    bloc_globaux = df_all_partie[["id_article","ordre_partie"]].drop_duplicates().reset_index(drop=True)
    bloc_globaux["bloc_global"] = range(-1,len(bloc_globaux)-1)
    df_all_partie = df_all_partie.merge(bloc_globaux, on = ["id_article","ordre_partie"]) 
    df_all_partie["nom_groupe"] = (df_all_partie["nom_groupe"].fillna(df_all_partie["auteur"])) # faudrait que ce soit géré dans la requête

    # --------------------------------------------------
    # 2. INFORMATIONS DE LA DISCUSSION
    # --------------------------------------------------

    df_infos_disc = retrieve_infos_disc(search)

    if df_infos_disc.empty:
        st.error("Impossible de récupérer les informations de la discussion.")
        return

    titre_discussion = (df_infos_disc["titre_disc_long"].iloc[0])
    lien_dossier_discussion = (df_infos_disc["lien_dossier"].iloc[0])
    lien_note_discussion = (df_infos_disc["lien_note"].iloc[0])

    # --------------------------------------------------
    # 3. INFORMATIONS DES VOTES ET RESUMES
    # --------------------------------------------------

    df_votes_articles = retrieve_info_articles(search)

    if df_votes_articles.empty:
        dict_votes_articles = {}
        dict_resumes = {}
    else:
        dict_votes_articles = dict(
            zip(df_votes_articles["id_article"].astype(str),
                df_votes_articles["proposition_vote_article"]))

        dict_resumes = dict(zip(df_votes_articles["id_article"].astype(str),
                                df_votes_articles["resume_article"]))

    # Dictionnaires de modifications en attente.
    st.session_state.setdefault("pending_resumes",{})

    st.session_state.setdefault("pending_votes",{})

    st.session_state.setdefault("pending_amdt",{})

    resumes = st.session_state["pending_resumes"]
    votes = st.session_state["pending_votes"]

    # Titre
    with st.container():
        st.markdown(f"""<h1 style='text-align:center;'>Amendements liés au {titre_discussion}</h1>""",unsafe_allow_html=True)

    # Boutons
    col_vide, col_buttons = st.columns([4, 1])

    with col_buttons:

        if lien_note_discussion:
            st.link_button("Lien vers la note du groupe",lien_note_discussion)
        if lien_dossier_discussion:
            st.link_button("Lien vers le dossier législatif",lien_dossier_discussion)
        if st.button("Lien vers la version «sans édition possible»",width="stretch"):
            st.query_params["discussion_choisie"] = search
            st.switch_page("pages/vue_seule_tab_amdts.py")

    st.space("medium")

    # Pagination

    max_bloc = df_all_partie["bloc_global"].max()

    nb_pages = get_nb_pages(int(max_bloc))
    page_key = f"page_actuelle_{search}"

    if page_key not in st.session_state:
        st.session_state[page_key] = 1
    st.session_state[page_key] = min(max(1, st.session_state[page_key]),nb_pages)

    page_actuelle = st.session_state[page_key]

    borne_min = get_borne_min(page_actuelle)
    borne_max = get_borne_max(borne_min)

    # Boutons de pagination.
    with st.container(horizontal=True,horizontal_alignment="center",vertical_alignment="center"):
        afficher_pagination(page_actuelle, nb_pages, page_key, search, "haut")

    # --------------------------------------------------
    # 7. AFFICHAGE DES PARTIES ET DES ARTICLES
    # --------------------------------------------------

    st.write(borne_min)
    st.write(borne_max)
        
    df_page = df_all_partie[df_all_partie["bloc_global"].between(borne_min, borne_max)]
    
    st.header(titre_partie)

    articles = (df_page[["bloc", "id_article", "article"]].drop_duplicates(subset=["bloc", "id_article", "article"]))
    for bloc, id_article, article in articles.itertuples(index=False, name=None):

        df_by_article = df_page[(df_page["bloc"] == bloc)& (df_page["id_article"] == id_article)]
        df_amdt_actifs = df_by_article[df_by_article["amdt"].notna()& (pd.to_numeric(df_by_article["is_active"], errors="coerce") == 1)].sort_values("ordre_examen_in_partie")

        if df_amdt_actifs.empty :
            print("")
        else : 
            # Afficher le titre de la partie si c'est une nouvelle partie
            new_titre_partie = df_amdt_actifs["titre_partie"].iloc[0]
            id_partie = df_amdt_actifs["id_partie"].unique()[0]
            if new_titre_partie == titre_partie :
                print("")
            else : 
                titre_partie = new_titre_partie
                st.header(titre_partie)

        # Afficher titre de l'article et son résumé (et si besoin le vote)
        display_titre_resume_article(id_article, article, id_partie, dict_resumes, resumes)

        est_article_add = "add" in str(article).lower()

        if df_amdt_actifs.empty: # si aucun amendements actifs
            st.write("Pas d'amendement")
            
            if not est_article_add:
                
                display_vote(False, dict_votes_articles, id_article, article, votes, id_partie)

        else:

            display_tab(df_amdt_actifs, article, id_partie)

            if not est_article_add:
                display_vote(False, dict_votes_articles, id_article, article, votes, id_partie)

        st.space("xlarge")

    afficher_pagination(page_actuelle, nb_pages, page_key, search, "bas")        

        ##
    ### Bouton de sauvegarde ###

    if st.button("Sauvegarder les modifications",type="primary"):
        succes = sauvegarder_modifications()
        if succes:
            st.success("Modifications enregistrées avec succès !")

def afficher_boutons_download(search : str):

    df_all_partie = retrieve_tab(search)

    ### afficher les boutons d'export

    st.download_button(
        "Télécharger une copie de la base en .DB",
        data=exporter_bdd(),
        file_name="ma_base_backup.db",
        mime="application/octet-stream")

    #st.download_button(
    #    label="Télécharger en CSV",
    #    data= exporter_csv(search),
    #    file_name="tableau.csv",
    #    mime="text/csv",
    #    icon=":material/download:"
    #)

    if "afficher_export_pdf" not in st.session_state:
        st.session_state.afficher_export_pdf = False

    if "afficher_articles_export_pdf" not in st.session_state:
        st.session_state.afficher_articles_export_pdf = False

    if "partie_selectionnee" not in st.session_state:
        st.session_state.partie_selectionnee = None

    if "articles_selectionnes" not in st.session_state:
        st.session_state.articles_selectionnes = []


    if st.button("Télécharger en pdf", key="ouvrir_export_pdf") : 
        st.session_state.afficher_export_pdf = True

    if st.session_state.afficher_export_pdf: 
        parties = (df_all_partie[["id_partie","titre_partie"]].dropna().drop_duplicates(subset=["id_partie","titre_partie"]))
        articles = (df_all_partie[["id_article","article"]].dropna(subset=["id_article"]).drop_duplicates(subset=["id_article","article"])) 
        id_article_list = articles["id_article"].to_list()      

        try:
            with st.spinner("Chargement...") :
                contenu = generer_content(search, id_article_list)
                content = generer_pdf(contenu)
                st.download_button(

                    "Télécharger tous les articles",
                    data=content,
                    file_name="tableau.pdf",
                    mime="application/pdf",
                    icon=":material/download:")

        except Exception as e:
            st.error(f"Erreur lors de la génération du PDF : {e}")

        if st.button("Sélectionner les parties à exporter"):
            st.session_state.afficher_articles_export_pdf = True

        if (st.session_state.afficher_articles_export_pdf and st.session_state.partie_selectionnee is None):
            with st.container(horizontal=True):
                for id_partie, titre_partie in parties.itertuples(index=False, name=None):
                    if st.button(titre_partie, key=f"partie_{id_partie}"):
                        st.session_state.partie_selectionnee = id_partie
                        st.session_state.articles_selectionnes = []
                        st.rerun()

        if st.session_state.partie_selectionnee is not None:
            articles_in_partie = df_all_partie[df_all_partie["id_partie"] == st.session_state.partie_selectionnee][["id_article", "article"]].drop_duplicates()
            articles_selectionnes = []
            for id_article, article in  articles_in_partie.itertuples(index = None, name = None) :
                print("LISTE DES ARTICLES")
                print(id_article)
                if st.checkbox(article, key={id_article}) :
                    articles_selectionnes.append(id_article)

            st.session_state.articles_selectionnes = articles_selectionnes        

            st.write(st.session_state.articles_selectionnes)
            st.download_button(
                label="Télécharger la sélection",
                data= generer_pdf(generer_content(search,st.session_state.articles_selectionnes, st.session_state.partie_selectionnee)),
                file_name="tableau.pdf",
                mime="application/pdf",
                icon=":material/download:"
            )
 

############### LANCEMENT DE LA PAGE ###############

search = st.query_params.get("discussion_choisie")
if search:
    afficher_page(search)
    afficher_boutons_download(search)


else:
    st.error("Aucune discussion sélectionnée.")