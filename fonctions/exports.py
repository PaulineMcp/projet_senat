import pandas as pd
import os
import sqlite3
import tempfile
from utils import *
from fonctions.fonctions_tableau.get_tab_to_aff import retrieve_tab
from fonctions.fonctions_scrapping_cleaning.fonctions_cleaning import abrev_article, ffill_df

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
        

def convert_for_download(df):
        return df.to_csv(
            index=False
        ).encode("utf-8-sig")


def exporter_csv(search) :
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

            ### faut encore convertir en csv


### boutons
#   st.download_button(
#        "Télécharger une copie de la base en .DB",
#        data=exporter_bdd(),
#        file_name="ma_base_backup.db",
#        mime="application/octet-stream")

    #st.download_button(
    #    label="Télécharger en CSV",
    #    data= exporter_csv(search),
    #    file_name="tableau.csv",
    #    mime="text/csv",
    #    icon=":material/download:"
    #)

#    if "afficher_export_pdf" not in st.session_state:
#        st.session_state.afficher_export_pdf = False

#    if "afficher_articles_export_pdf" not in st.session_state:
#        st.session_state.afficher_articles_export_pdf = False

#    if "partie_selectionnee" not in st.session_state:
#        st.session_state.partie_selectionnee = None

#    if "articles_selectionnes" not in st.session_state:
#        st.session_state.articles_selectionnes = []


#    if st.button("Télécharger en pdf", key="ouvrir_export_pdf") : 
#        st.session_state.afficher_export_pdf = True

#    if st.session_state.afficher_export_pdf: 
#        parties = (df_all_partie[["id_partie","titre_partie"]].dropna().drop_duplicates(subset=["id_partie","titre_partie"]))
#        articles = (df_all_partie[["id_article","article"]].dropna(subset=["id_article"]).drop_duplicates(subset=["id_article","article"])) 
#        id_article_list = articles["id_article"].to_list()      

#        try:
#            with st.spinner("Génération du PDF") :
#                contenu = generer_content(search, id_article_list)
#                content = generer_pdf(contenu)
#                st.download_button(
#                    "Télécharger tous les articles",
#                    data=content,
#                    file_name="tableau.pdf",
#                    mime="application/pdf",
#                    icon=":material/download:")

#        except Exception as e:
#            st.error(f"Erreur lors de la génération du PDF : {e}")

#        if st.button("Sélectionner les parties à exporter"):
#            st.session_state.afficher_articles_export_pdf = True

#        if (st.session_state.afficher_articles_export_pdf and st.session_state.partie_selectionnee is None):
#            with st.container(horizontal=True):
#                for id_partie, titre_partie in parties.itertuples(index=False, name=None):
#                    if st.button(titre_partie, key=f"partie_{id_partie}"):
#                        st.session_state.partie_selectionnee = id_partie
#                        st.session_state.articles_selectionnes = []
#                        st.rerun()

#        if st.session_state.partie_selectionnee is not None:
#            for id_article, article in articles.itertuples(index = None, name = None) :
#                if st.checkbox(article, key={id_article}):
#                    st.session_state.articles_selectionnes.append(id_article)

#                st.download_button(
#                    label="Télécharger la sélection",
#                    data= generer_pdf(generer_content(search,st.session_state.articles_selectionnes)),
#                    file_name="tableau.pdf",
#                    mime="application/pdf",
#                    icon=":material/download:"
#                )