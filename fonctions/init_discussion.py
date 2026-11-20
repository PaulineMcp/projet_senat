
"""
Initialiser une discussion.

Fonctions principales :
    - fetch_disc : récupérer les informations d'une discussion.
    - init_disc : enregistrer une discussion.
    - fetch_content : récupérer les parties, l'ordre et les amendements.
    - init_content : enregistrer les parties, l'ordre et les amendements.
    - fetch_articles_from_texte : récupérer les articles depuis le texte de loi.
    - fetch_articles_from_amdts : récupérer les articles depuis les amendements.
    - init_articles : enregistrer les articles.
    - fetch_avis : récupérer les avis gouvernement et commission.
    - init_avis : enregistrer les avis.
    - init_remplissage_amdts : initialiser les remplissages des amendements.
    - init_remplissage_articles : initialiser les remplissages des articles.
"""

############### IMPORTS ###############

from pathlib import Path
import sys
import re
import unicodedata

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fonctions.fonctions_scrapping_cleaning.fonctions_cleaning import (
    get_id_article,
    get_id_bloc_article,
    get_id_amdt,
    is_ss_amdt,
    get_info_from_id,
    turn_into_content,
    turn_into_ordre,
    get_bloc_article
)

from fonctions.fonctions_scrapping_cleaning.fonctions_scrapping import (
    get_content_page,
    get_hash,
    get_tab_list,
    get_disc_info,
    parsing_line,
    get_avis_gouv,
    get_avis_com,
    get_avis
)

from fonctions.upsert_bdd import upsert_df
from utils import get_db


############### OUTILS INTERNES ###############

def normaliser_article(texte):
    """Normalise un texte d'article sans modifier les valeurs nulles."""

    if isinstance(texte, str):
        return " ".join(
            unicodedata.normalize("NFKC", texte).split()
        )

    return texte


def normaliser_df_articles(df):
    """Normalise et supprime les doublons dans un DataFrame d'articles."""

    if df.empty:
        return df

    df = df.copy()

    df["article"] = df["article"].map(normaliser_article)

    df = df.drop_duplicates(
        subset=[
            "id_bloc_article",
            "bloc_article",
            "bloc",
            "id_article",
            "id_disc"
        ],
        keep="first"
    )

    return df


############### DISCUSSION ###############

def fetch_disc(url: str, inputs: dict) -> pd.DataFrame:
    """Récupère les informations d'une discussion."""

    infos = get_disc_info(url)

    titre_disc_long = (
        inputs["titre"]
        + " - "
        + infos["com_seance"]
        + " - "
        + infos["lecture"]
        + " - "
        + infos["session"]
    )

    nb_parties = len(get_tab_list(url))
    last_hash = get_hash(url)

    disc = [{
        "id_disc": infos["id_disc"],
        "url_disc": inputs["url"],
        "titre_disc": inputs["titre"],
        "titre_disc_long": titre_disc_long,
        "nb_parties": nb_parties,
        "com_seance": infos["com_seance"],
        "lecture": infos["lecture"],
        "last_hash": last_hash,
        "lien_note": inputs["lien_note"].strip(),
        "lien_dossier": inputs["lien_dossier"].strip(),
        "url_txt": inputs["url_txt"],
        "is_archived": 0
    }]

    df = pd.DataFrame(disc)

    print("Infos de la discussion récupérées")

    return df


def init_disc(url: str, inputs: dict, conn=None) -> None:
    """Récupère et enregistre les informations d'une discussion."""

    df = fetch_disc(url, inputs)

    if conn is None:
        with get_db() as conn:
            upsert_df("discussion", df, "id_disc", conn=conn)

    else:
        upsert_df("discussion", df, "id_disc", conn=conn)


############### PARTIES ET AMENDEMENTS ###############

def fetch_content(id_disc: str, conn=None):
    """
    Récupère le contenu d'une discussion.

    Renvoie :
        df_parties
        df_ordre
        df_content
    """

    url_disc = get_info_from_id(
        id_disc,
        "url_disc",
        conn=conn
    )

    nb_parties = get_info_from_id(
        id_disc,
        "nb_parties",
        conn=conn
    )

    soup = get_content_page(url_disc)

    df_parties = []

    df_ordre = pd.DataFrame(
        columns=[
            "id_amdt",
            "id_partie",
            "ordre_examen_in_partie"
        ]
    )

    df_content = pd.DataFrame(
        columns=[
            "id_amdt",
            "id_article",
            "id_partie",
            "amdt",
            "is_ss_amdt",
            "lien_amdt",
            "auteur",
            "url_senateur",
            "sort"
        ]
    )

    ############### DISCUSSION AVEC UNE SEULE PARTIE ###############

    if nb_parties == 1:

        df_parties.append({
            "id_partie": id_disc + "-p1",
            "id_disc": id_disc,
            "titre_partie": "Première et unique partie",
            "ordre_partie": 1
        })

        tbody = soup.find("tbody")

        if tbody is not None:

            lines = tbody.find_all("tr")

            parsed = [
                parsing_line(line)
                for line in lines
            ]

            df = pd.DataFrame(parsed)

            if not df.empty:

                df_ordre = turn_into_ordre(
                    df.copy(),
                    id_disc,
                    1
                )

                df_content = turn_into_content(
                    df.copy(),
                    id_disc,
                    1,
                    conn=conn
                )

    ############### DISCUSSION AVEC PLUSIEURS PARTIES ###############

    else:

        tables = soup.find_all("table")

        ordre = 1

        for table in tables:

            titre = table.find_previous("h5")

            if titre is None:
                titre = "Première partie"
            else:
                titre = titre.get_text(strip=True)

            df_parties.append({
                "id_partie": id_disc + "-p" + str(ordre),
                "id_disc": id_disc,
                "titre_partie": titre.capitalize(),
                "ordre_partie": ordre
            })

            tbody = table.find("tbody")

            if tbody is not None:

                lines = tbody.find_all("tr")

                parsed = [
                    parsing_line(line)
                    for line in lines
                ]

                df_tmp = pd.DataFrame(parsed)

                if not df_tmp.empty:

                    df_ordre_tmp = turn_into_ordre(
                        df_tmp.copy(),
                        id_disc,
                        ordre
                    )

                    df_content_tmp = turn_into_content(
                        df_tmp.copy(),
                        id_disc,
                        ordre,
                        conn=conn
                    )

                    df_ordre = pd.concat(
                        [df_ordre, df_ordre_tmp],
                        ignore_index=True
                    )

                    df_content = pd.concat(
                        [df_content, df_content_tmp],
                        ignore_index=True
                    )

            ordre += 1

    ############### FINALISATION ###############

    df_parties = pd.DataFrame(df_parties)

    if not df_ordre.empty:
        df_ordre["ordre_examen_abs"] = range(len(df_ordre))

    print("Contenu, parties et ordre récupérés")

    return df_parties, df_ordre, df_content


def init_content(id_disc: str, conn=None) -> None:
    """Récupère et enregistre les parties, amendements et ordre."""

    if conn is None:

        with get_db() as conn:
            init_content(id_disc, conn=conn)

        return

    df_parties, df_ordre, df_content = fetch_content(
        id_disc,
        conn=conn
    )

    # Respect de l'ordre des clés étrangères :
    # parties -> amdts -> ordre_examen

    if not df_parties.empty:
        upsert_df(
            "parties",
            df_parties,
            "id_partie",
            conn=conn
        )

    if not df_content.empty:

        df_content["is_active"] = 1

        upsert_df(
            "amdts",
            df_content,
            "id_amdt",
            conn=conn
        )

    if not df_ordre.empty:

        upsert_df(
            "ordre_examen",
            df_ordre,
            "id_amdt",
            conn=conn
        )


############### ARTICLES ###############

def fetch_articles_from_texte(
    id_disc: str,
    conn=None
) -> pd.DataFrame:
    """
    Récupère les articles identifiés dans le texte de loi.
    """

    url_articles = get_info_from_id(
        id_disc,
        "url_txt",
        conn=conn
    )

    if not url_articles:
        return pd.DataFrame()

    soup = get_content_page(url_articles)

    articles = soup.find_all(
        "p",
        {"class": "TCNumArticle"}
    )

    df = []

    for article in articles:

        try:
            lien_article = (
                url_articles
                + "#"
                + article.find("a")["id"]
            )

        except (TypeError, KeyError):
            lien_article = "Pas de lien vers l'article"

        article_texte = re.sub(
            r"\([^()]*\)",
            "",
            article.get_text(strip=True)
        ).strip()

        id_article = (
            id_disc
            + "-"
            + get_id_article(article_texte)
        )

        id_bloc_article = (
            id_disc
            + "-"
            + get_id_bloc_article(article_texte)
        )

        df.append({
            "id_bloc_article": id_bloc_article,
            "bloc_article": get_bloc_article(article_texte),
            "bloc": get_id_bloc_article(article_texte),
            "id_article": id_article,
            "article": article_texte,
            "lien_article": lien_article,
            "id_disc": id_disc
        })

    return pd.DataFrame(df).drop_duplicates()


def fetch_articles_from_amdts(
    id_disc: str,
    conn=None
) -> pd.DataFrame:
    """
    Récupère les articles identifiés grâce aux amendements.
    """

    requete = """
        SELECT
            amdts.id_article,
            amdts.article,
            amdts.lien_article
        FROM amdts
        JOIN parties
            ON parties.id_partie = amdts.id_partie
        WHERE parties.id_disc = ?
    """

    if conn is None:

        with get_db() as conn:
            df = pd.read_sql(
                requete,
                conn,
                params=(id_disc,)
            )

    else:

        df = pd.read_sql(
            requete,
            conn,
            params=(id_disc,)
        )

    df = df.drop_duplicates()

    if df.empty:
        return pd.DataFrame(
            columns=[
                "id_bloc_article",
                "bloc_article",
                "bloc",
                "id_article",
                "article",
                "lien_article",
                "id_disc"
            ]
        )

    df["id_bloc_article"] = (
        id_disc
        + "-"
        + df["article"].apply(get_id_bloc_article)
    )

    df["bloc_article"] = df["article"].apply(
        get_bloc_article
    )

    df["id_disc"] = id_disc

    df["bloc"] = df["article"].apply(
        get_id_bloc_article
    )

    df = df[
        [
            "id_bloc_article",
            "bloc_article",
            "bloc",
            "id_article",
            "article",
            "lien_article",
            "id_disc"
        ]
    ]

    return df


def init_articles(id_disc: str, conn=None) -> None:
    """Récupère et enregistre les articles."""

    if conn is None:

        with get_db() as conn:
            init_articles(id_disc, conn=conn)

        return

    df_art_from_amdts = fetch_articles_from_amdts(
        id_disc,
        conn=conn
    )

    df_art_from_txt = fetch_articles_from_texte(
        id_disc,
        conn=conn
    )

    df = pd.concat(
        [df_art_from_amdts, df_art_from_txt],
        ignore_index=True
    )

    df = normaliser_df_articles(df)

    if not df.empty:

        upsert_df(
            "articles",
            df,
            "id_article",
            conn=conn
        )

    print(f"{len(df)} articles récupérés.")


############### AVIS ###############

import time
from utils import get_db

AVIS_VIDES = ("En cours de récupération", "Pas d'avis", "NA")

def est_vide(v) -> bool:
    return v is None or (isinstance(v, float) and pd.isna(v)) or v in AVIS_VIDES


def fetch_avis(id_disc: str, conn=None, pause: float = 0.5) -> pd.DataFrame:
    """Récupère les avis des amendements nouveaux ou sans avis.
    Un avis déjà renseigné n'est jamais écrasé. Renvoie (id_amdt, avis_gouv, avis_com)."""
    requete = """
        SELECT amdts.id_amdt, amdts.lien_amdt, avis.avis_gouv, avis.avis_com
        FROM amdts
        JOIN parties ON parties.id_partie = amdts.id_partie
        LEFT JOIN avis ON avis.id_amdt = amdts.id_amdt
        WHERE parties.id_disc = ?
          AND amdts.is_active = 1
          AND (avis.id_amdt IS NULL
               OR avis.avis_gouv IS NULL OR avis.avis_gouv IN (?, ?, ?)
               OR avis.avis_com  IS NULL OR avis.avis_com  IN (?, ?, ?))
    """
    params = (id_disc, *AVIS_VIDES, *AVIS_VIDES)

    if conn is None:
        with get_db() as c:
            df = pd.read_sql(requete, c, params=params)
            com_seance = get_info_from_id(id_disc, "com_seance")
    else:
        df = pd.read_sql(requete, conn, params=params)
        com_seance = get_info_from_id(id_disc, "com_seance")

    resultats = []
    for id_amdt, lien, cur_gouv, cur_com in df.itertuples(index=False, name=None):
        print(f"Récupération des avis de :{id_amdt}")
        if com_seance == "Commission":                 # rien à scraper en commission
            gouv, com = "Pas d'avis", "Pas d'avis"
        else:
            gouv, com = get_avis(lien)                 # page chargée une seule fois
            time.sleep(pause)
            if gouv is None or com is None:            # échec réseau : on retentera au prochain passage
                continue

        # On ne remplace que ce qui est vide : un avis déjà trouvé est conservé
        gouv_final = gouv if est_vide(cur_gouv) else cur_gouv
        com_final = com if est_vide(cur_com) else cur_com
        resultats.append((id_amdt, gouv_final, com_final))

    print(f"Avis traités : {len(resultats)} sur {len(df)} candidats")
    return pd.DataFrame(resultats, columns=["id_amdt", "avis_gouv", "avis_com"])



def init_avis(id_disc: str, conn=None) -> None:
    """Récupère et enregistre les avis."""

    if conn is None:

        with get_db() as conn:
            init_avis(id_disc, conn=conn)

        return

    df = fetch_avis(
        id_disc,
        conn=conn
    )

    if not df.empty:

        upsert_df(
            "avis",
            df,
            "id_amdt",
            conn=conn
        )


############### REMPLISSAGE AP DES AMENDEMENTS ###############

def init_remplissage_amdts(
    id_disc: str,
    conn=None
) -> None:
    """
    Initialise les objets, commentaires et propositions de vote
    uniquement pour les amendements non encore initialisés.
    """

    if conn is None:

        with get_db() as conn:
            init_remplissage_amdts(id_disc, conn=conn)

        return

    df = pd.read_sql("""
        SELECT DISTINCT a.id_amdt
        FROM amdts a
        JOIN parties p
            ON p.id_partie = a.id_partie
        WHERE p.id_disc = ?
        AND NOT EXISTS (
            SELECT 1
            FROM remplissage_ap_amdt r
            WHERE r.id_amdt = a.id_amdt
        )
    """, conn, params=(id_disc,))

    if df.empty:
        print("Aucun nouvel amendement à initialiser.")
        return

    df["objet"] = "À compléter"
    df["com"] = ""
    df["proposition_vote_amdt"] = "À définir"

    upsert_df(
        "remplissage_ap_amdt",
        df,
        "id_amdt",
        conn=conn
    )

    print(f"{len(df)} amendements initialisés.")


############### REMPLISSAGE AP DES ARTICLES ###############

def init_remplissage_articles(
    id_disc: str,
    conn=None
) -> None:
    """
    Initialise les résumés et propositions de vote
    uniquement pour les articles non encore initialisés.
    """

    if conn is None:

        with get_db() as conn:
            init_remplissage_articles(id_disc, conn=conn)

        return

    df = pd.read_sql("""
        SELECT DISTINCT a.id_article
        FROM articles a
        WHERE a.id_disc = ?
        AND NOT EXISTS (
            SELECT 1
            FROM remplissage_ap_article r
            WHERE r.id_article = a.id_article
        )
    """, conn, params=(id_disc,))

    if df.empty:
        print("Aucun nouvel article à initialiser.")
        return

    df["resume_article"] = None
    df["proposition_vote_article"] = None

    upsert_df(
        "remplissage_ap_article",
        df,
        "id_article",
        conn=conn
    )

    print(f"{len(df)} articles initialisés.")


############### OUTIL VALEURS MANQUANTES ###############

def vide(x):
    """Remplace une valeur manquante par None."""

    return None if pd.isna(x) else x