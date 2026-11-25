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