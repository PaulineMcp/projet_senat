
"""
Fonctions pour nettoyer les éléments de base :
id des amendements, id de sessions, id des articles ...

Liste des fonctions :
    - get_id_disc
    - get_id_amdt
    - commission_ou_sceance
    - get_session
    - is_ss_amdt
    - abrev_article
    - get_id_article
    - get_bloc_article
    - get_id_bloc_article
    - get_url_articles
    - abrev_groupe
    - get_info_from_id
    - turn_into_content
    - turn_into_ordre
    - get_url_article
    - ffill_df
"""

############### IMPORTS ###############

import re
import unicodedata
import sys
from pathlib import Path

import pandas as pd
from typing import Literal, Optional


# Constantes
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from utils import get_db


############### IDENTIFIANTS ###############

def get_id_disc(url_disc: str):

    if commission_ou_sceance(url_disc) == "Commission":
        id_disc = url_disc[55:].replace(
            "/liste_discussion.html", ""
        )
    else:
        id_disc = url_disc[43:].replace(
            "/liste_discussion.html", ""
        )

    return id_disc


def get_id_amdt(amdt: str):

    amdt = amdt.replace("\n", "")
    amdt = unicodedata.normalize("NFKC", amdt)

    amdt = amdt.replace("S/Amt ", "s/a-").replace("n°", "").strip()
    amdt = amdt.replace("Amt", "").replace("n°", "").strip()

    id_amdt = amdt.replace("Motion", "").strip()

    multiplicatifs = {
        "rect. decies": "rdc",
        "rect. nonies": "rnn",
        "rect. octies": "roc",
        "rect. septies": "rsp",
        "rect. sexies": "rsx",
        "rect. quinquies": "rqq",
        "rect. quater": "rqt",
        "rect. ter": "rt",
        "rect. bis": "rb",
        "rect.": "r"
    }

    for cle, code in multiplicatifs.items():
        if cle in amdt:
            id_amdt = amdt.replace(cle, "").replace(" ", "")
            break

    return id_amdt


def commission_ou_sceance(url_pjl: str):

    if "commission" in url_pjl:
        return "Commission"

    return "Séance"


def get_session(url: str):

    if commission_ou_sceance(url) == "Commission":
        session = url[45:54]
    else:
        session = url[33:42]

    return session


def is_ss_amdt(amdt):

    if not isinstance(amdt, str):
        return False

    return "S/" in amdt


############### ARTICLES ###############

def abrev_article(article: str):

    multiplicatif = [
        "bis", "ter", "quater", "quinquies", "sexies",
        "septies", "octies", "nonies", "decies",
        "undecies", "duodecies", "terdecies",
        "quaterdecies", "quindecies", "sexdecies",
        "septdecies", "octodecies", "novodecies",
        "vicies", "unvicies", "duovicies", "tervicies",
        "quatervicies", "quinvicies", "sexvicies",
        "septvicies", "octovicies", "novovicies",
        "tricies", "untricies", "duotricies",
        "tertricies", "quatertricies", "quintricies",
        "sextricies", "septtricies", "octotricies",
        "novotricies", "quadragies", "unquadragies",
        "duoquadragies", "terquadragies",
        "quaterquadragies", "quinquadragies",
        "sexquadragies", "septquadragies",
        "octoquadragies", "novoquadragies",
        "quinquagies", "unquinquagies",
        "duoquinquagies", "terquinquagies",
        "quaterquinquagies", "quinquinquagies",
        "sexquinquagies", "septquinquagies",
        "octoquinquagies", "novoquinquagies",
        "sexagies", "unsexagies", "duosexagies",
        "tersexagies", "quatersexagies",
        "quinsexagies", "sexsexagies",
        "septsexagies", "octosexagies", "novosexagies"
    ]

    prefixe = {
        "additionnel avant": "Add av art.",
        "additionnel(s) avant": "Add av art.",
        "additionnel après": "Add ap art.",
        "additionnel(s) après": "Add ap art.",
        "motion": "Motion(s)",
        "liminaire": "Art. lim "
    }

    suffixe = {
        "état": "Ét.",
        "annexe": "Anx."
    }

    article = unicodedata.normalize("NFKC", article).lower()

    if article == "intitulé de la proposition de loi":
        abrev = "Int.PPL"

    else:

        if "unique" in article:
            digits = "Unq"
        else:
            digits = re.sub(
                r"\D", "",
                re.sub(r"\([^)]*\)", "", article)
            )

        pref = "Art."

        for cle, code in prefixe.items():
            if cle in article:
                pref = code
                break

        mult = ""

        for item in multiplicatif:
            if item in re.findall(r"[a-zà-ÿ]+", article):
                mult = item
                break

        suf = ""

        for cle, code in suffixe.items():
            if cle in article:
                if cle == "état":
                    suf = code + article[-1].upper()
                    break
                else:
                    suf = code

        abrev = pref + digits + mult + suf

    return abrev


def get_id_bloc_article(article: str):

    article = unicodedata.normalize(
        "NFKC", article
    ).lower()

    if "unique" in article:
        id_bloc = "1"

    elif "liminaire" in article:
        id_bloc = "0"

    elif "motion" in article:
        id_bloc = "-1"

    elif "intitulé de la proposition de loi" in article:
        id_bloc = "intppl"

    else:
        id_bloc = re.sub(
            r"\D", "",
            re.sub(r"\([^)]*\)", "", article)
        )

    return id_bloc
      
############### URL DES ARTICLES ###############

def get_url_articles(url_disc: str):

    try:

        session = get_session(url_disc)
        id_disc = get_id_disc(url_disc)

        com_seance = commission_ou_sceance(url_disc)

        url_base = (
            "https://www.senat.fr/amendements/textes/commissions/"
            if com_seance == "Commission"
            else "https://www.senat.fr/amendements/textes/"
        )

        return url_base + session + "/" + id_disc + ".html"

    except Exception as e:

        print(f"Erreur URL des articles : {e}")
        return None


############### GROUPES POLITIQUES ###############

def abrev_groupe(input: str):

    groupe_liste = {
        "Groupe Les Républicains": "LR",
        "Groupe Union Centriste et Indépendants": "UCI",
        "Groupe Socialiste, Écologiste et Républicain": "SER",
        "Groupe Communiste Républicain Citoyen et Écologiste - Kanaky": "CRCE-K",
        "Groupe du Rassemblement Démocratique et Social Européen": "RDSE",
        "Groupe Rassemblement des démocrates, progressistes et indépendants": "RDPI",
        "Groupe Écologiste - Solidarité et Territoires": "GEST",
        "Groupe Les Indépendants - République et Territoires": "LIRT",
        "Groupe Union Nationale pour les Territoires": "RN",
        "Réunion administrative des Sénateurs ne figurant sur la liste d'aucun groupe": "NI"
    }

    return groupe_liste.get(input, "?")


############### INFORMATIONS BDD ###############

TypeInfo = Literal[
    "url_disc",
    "url_articles",
    "url_txt",
    "nb_parties",
    "com_seance"
]


def get_info_from_id(
    id_disc: str,
    type_info: TypeInfo,
    conn=None
) -> Optional[str]:

    colonnes_autorisees = {
        "url_disc",
        "url_articles",
        "url_txt",
        "nb_parties",
        "com_seance"
    }

    if type_info not in colonnes_autorisees:
        raise ValueError(
            f"Information non autorisée : {type_info}"
        )

    if conn is None:

        with get_db() as conn:
            return get_info_from_id(
                id_disc,
                type_info,
                conn=conn
            )

    requete = f"""
        SELECT {type_info}
        FROM discussion
        WHERE id_disc = ?
    """

    df = pd.read_sql(
        requete,
        conn,
        params=(id_disc,)
    )

    if df.empty:
        raise ValueError(
            f"Discussion {id_disc} introuvable dans la BDD."
        )

    return df.iloc[0, 0]


############### TRANSFORMATION DES AMENDEMENTS ###############

def turn_into_content(
    df: pd.DataFrame,
    id_disc: str,
    ordre: int,
    conn=None
) -> pd.DataFrame:

    df = df.copy()

    url_disc = get_info_from_id(
        id_disc,
        "url_disc",
        conn=conn
    )

    df["id_partie"] = id_disc + "-p" + str(ordre)

    df["id_article"] = (
        id_disc + "-"
        + df["article"].apply(get_id_article)
    )

    df["id_amdt"] = (
        df["id_article"] + "-"
        + df["amdt"].apply(get_id_amdt)
    )

    df["is_ss_amdt"] = df["amdt"].apply(is_ss_amdt)

    df["lien_amdt"] = (
        url_disc.replace("liste_discussion.html", "")
        + df["lien_amdt"]
    )

    df["is_active"] = 1

    return df[[
        "id_amdt",
        "id_article",
        "id_partie",
        "article",
        "amdt",
        "is_ss_amdt",
        "lien_amdt",
        "lien_article",
        "auteur",
        "url_senateur",
        "sort",
        "is_active"
    ]]


############### TRANSFORMATION DE L'ORDRE ###############

def turn_into_ordre(
    df: pd.DataFrame,
    id_disc: str,
    ordre: int
) -> pd.DataFrame:

    df = df.copy()

    df["id_article"] = (
        id_disc + "-"
        + df["article"].apply(get_id_article)
    )

    df["id_amdt"] = (
        df["id_article"] + "-"
        + df["amdt"].apply(get_id_amdt)
    )

    df["id_partie"] = id_disc + "-p" + str(ordre)

    df["ordre_examen_in_partie"] = df.index

    return df[[
        "id_amdt",
        "id_partie",
        "ordre_examen_in_partie"
    ]]


############### URL D'UN ARTICLE ###############

def get_url_article(
    article: str,
    id_disc: str,
    conn=None
):

    url_articles = get_info_from_id(
        id_disc,
        "url_txt",
        conn=conn
    )

    if not url_articles:
        return None

    return (
        url_articles
        + "#AMELI_SUB_4__Article_"
        + get_id_bloc_article(article)
    )


############### ORDRE DES ARTICLES ###############

def ffill_df(df: pd.DataFrame) -> pd.DataFrame:

    df = df.copy()

    for idx, row in df.iterrows():

        if pd.isna(row["ordre_examen_in_partie"]):

            precedents = df[
                (df["bloc"] < row["bloc"])
                & df["ordre_examen_in_partie"].notna()
            ]

            if precedents.empty:

                df.at[idx, "ordre_examen_in_partie"] = -1

            else:

                bloc_prec = precedents["bloc"].max()

                max_value = precedents.loc[
                    precedents["bloc"] == bloc_prec,
                    "ordre_examen_in_partie"
                ].max()

                df.at[idx, "ordre_examen_in_partie"] = max_value

    return df

def retrieve_article_list(id_disc : str) -> pd.DataFrame :
    with get_db() as conn :
        df_articles = pd.read_sql(
            """ SELECT id_article, article
            FROM articles
            WHERE id_disc = ?
            """,
        conn,params=(id_disc,),)
    return(df_articles)

def valeurs_identiques(a, b):
    if pd.isna(a) and pd.isna(b):
        return True
    if pd.isna(a) or pd.isna(b):
        return False
    return a == b


MULTIPLICATIF_ARTICLE = {
    "bis": "b", "ter": "t", "quater": "qt", "quinquies": "qq", "sexies": "sx",
    # ... colle ici ton dict complet bis -> b, ter -> t, ... jusqu'à novosexagies
}

NATURE_ARTICLE = {
    "motion": "mot",
    "liminaire": "lim",
    "unique": "unq",
    "intitulé de la proposition de loi": "intPPL",
}

SUFFIXE_ARTICLE = {"état": "E", "annexe": "anx"}


def get_id_article(article: str):

    article = unicodedata.normalize("NFKC", article).lower()
    sans_s = article.replace("(s)", "")
    digits = re.sub(r"\D", "", re.sub(r"\([^)]*\)", "", article))
    texte = " ".join(re.sub(r"\([^()]*\)", "", article).split())

    pref = ""
    if re.search(r"additionnel\s+apr[eè]s", sans_s):
        pref = "addap"
    elif re.search(r"additionnel\s+avant", sans_s):
        pref = "addav"

    nature = ""
    for cle, code in NATURE_ARTICLE.items():
        if re.search(rf"(?<![a-zà-ÿ]){cle}(?![a-zà-ÿ])", sans_s):
            nature = code
            break

    mult = ""
    for cle, code in MULTIPLICATIF_ARTICLE.items():
        m = re.search(
            rf"(?<![a-zà-ÿ]){cle}(?![a-zà-ÿ])(?:\s+([a-z])(?![a-zà-ÿ]))?",
            texte
        )
        if m:
            mult = code + (m.group(1).upper() if m.group(1) else "")
            break

    lettre = ""
    if not mult:
        m = re.search(r"\d+(?:er)?\s+([a-z])(?![a-zà-ÿ0-9])", texte)
        if m:
            lettre = m.group(1).upper()

    suf = ""
    for cle, code in SUFFIXE_ARTICLE.items():
        if re.search(rf"(?<![a-zà-ÿ]){cle}(?![a-zà-ÿ])", texte):
            suf = code + texte[-1].upper() if cle == "état" else code

    return pref + nature + digits + mult + lettre + suf