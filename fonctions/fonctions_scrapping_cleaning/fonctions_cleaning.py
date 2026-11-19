"""Fonctions pour nettoyer les éléments de base : id des amendements, id de sessions, id des articles ...

Liste des fonctions :
    -   get_id_disc : extraire l'id d'un PPL / PJL d'une url
    -   get_id_amdt : extraire l'id d'un amdt d'une str comme "Amt n° COM-19"
    -   commission_ou_seance : savoir si la page fait référence à une session séance ou commission
    -   get_session : extraire l'annee de la session d'une url
    -   is_ss_amdt : teste si un amendement est un sous-amendement
    -   abrev_article : abrévie le nom d'un article
    -   get_id_article : extraire l'id d'un article d'une str comme "Article(s) additionnel(s) après Article 9"
    -   get_bloc_article : extraire l'id_bloc d'un article (un article et un article additionnel font partie d'un même bloc)
    -   get_url_article : trouver l'url de l'article à partir de son id
    -   abrev_groupe : extraire l'acronyme depuis le nom au long d'un groupe politique
"""

###############     IMPORTS     ###############
# Import des librairies
import re
import inspect
import unicodedata
import sys
from pathlib import Path
import pandas as pd
from typing import Literal, Optional

# Constantes
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from utils import *

###############     FONCTIONS     ###############
def get_id_disc(url_disc : str):
    if commission_ou_sceance(url_disc) == "Commission":
        id = url_disc[55:].replace("/liste_discussion.html","")
    else :
        id = url_disc[43:].replace("/liste_discussion.html","")
    return(id)

def get_id_amdt(amdt : str):
    amdt = amdt.replace("\n","")
    amdt = unicodedata.normalize("NFKC", amdt)
    amdt = amdt.replace("S/Amt ","s/a-").replace("n°","").strip()
    amdt = amdt.replace("Amt","").replace("n°","").strip() 
    id_amdt = amdt.replace("Motion","").strip()
    multiplicatifs = {"rect. decies": "rdc", "rect. nonies": "rnn", "rect. octies": "roc", "rect. septies": "rsp", "rect. sexies": "rsx", "rect. quinquies": "rqq", "rect. quater": "rqt", "rect. ter": "rt", "rect. bis": "rb", "rect.": "r"}
    for cle, code in multiplicatifs.items():
        if cle in amdt:
            id_amdt = amdt.replace(cle,"").replace(" ","")
            break
    return(id_amdt)

def commission_ou_sceance(url_pjl : str) :
    if "commission" in url_pjl:
        return("Commission")
    else:
        return("Séance")
     
def get_session(url : str ):
    if commission_ou_sceance(url) == "Commission" :
        session = url[45:54]
    else :
        session = url[33:42]
    return(session)

def is_ss_amdt(amdt):
    if "S/" in amdt:
        return True
    else :
        return False

def abrev_article(article : str):
    multiplicatif = ["bis", "ter", "quater", "quinquies", "sexies", "septies", "octies", "nonies", "decies", "undecies", "duodecies", "terdecies", "quaterdecies", "quindecies", "sexdecies", "septdecies", "octodecies", "novodecies", "vicies", "unvicies", "duovicies", "tervicies", "quatervicies", "quinvicies", "sexvicies", "septvicies", "octovicies", "novovicies", "tricies", "untricies", "duotricies", "tertricies", "quatertricies", "quintricies", "sextricies", "septtricies", "octotricies", "novotricies", "quadragies", "unquadragies", "duoquadragies", "terquadragies", "quaterquadragies", "quinquadragies", "sexquadragies", "septquadragies", "octoquadragies", "novoquadragies", "quinquagies", "unquinquagies", "duoquinquagies", "terquinquagies", "quaterquinquagies", "quinquinquagies", "sexquinquagies", "septquinquagies", "octoquinquagies", "novoquinquagies", "sexagies", "unsexagies", "duosexagies", "tersexagies", "quatersexagies", "quinsexagies", "sexsexagies", "septsexagies", "octosexagies", "novosexagies"]
    prefixe = {"additionnel avant" : "Add av art.", "additionnel(s) avant" : "Add av art.", "additionnel après" : "Add ap art.", "additionnel(s) après" : "Add ap art.", "motion" : "Motion(s)", "liminaire" : "Art. lim "}
    suffixe = {"état" : "Ét.", "annexe" : "Anx."}
    
    article = unicodedata.normalize("NFKC", article).lower()  # \xa0 = espace normal
    if article == "intitulé de la proposition de loi" :
        abrev = "Int.PPL"
    else : 
        if "unique" in article :
            digits = "Unq"
        else :
            digits = re.sub(r"\D","",re.sub(r"\([^)]*\)", "", article))

        pref = "Art."
        for cle,code in prefixe.items():
            if cle in article :
                pref = code
                break
                
        mult = ""
        for item in multiplicatif :
            if item in re.findall(r"[a-zà-ÿ]+", article) :
                mult = item
                break

        suf = ""
        for cle,code in suffixe.items():
            if cle in article :
                if cle == "état" :
                    suf = code + article[-1].upper()
                    break
                else : 
                    suf = code

        abrev = pref + digits + mult + suf            
    return(abrev)


def get_id_article(article : str) :

    multiplicatif = {"bis": "b", "ter": "t", "quater": "qt", "quinquies": "qq", "sexies": "sx", "septies": "sp", "octies": "oc", "nonies": "nn", "decies": "dc", "undecies": "udc", "duodecies": "ddc", "terdecies": "tdc", "quaterdecies": "qtdc", "quindecies": "qdc", "sexdecies": "sxdc", "septdecies": "spdc", "octodecies": "odc", "novodecies": "ndc", "vicies": "vc", "unvicies": "uvc", "duovicies": "dvc", "tervicies": "tvc", "quatervicies": "qtvc", "quinvicies": "qvc", "sexvicies": "sxvc", "septvicies": "spvc", "octovicies": "ovc", "novovicies": "nvc", "tricies": "tc", "untricies": "utc", "duotricies": "dtc", "tertricies": "ttc", "quatertricies": "qttc", "quintricies": "qtc", "sextricies": "sxtc", "septtricies": "sptc", "octotricies": "otc", "novotricies": "ntc", "quadragies": "qc", "unquadragies": "uqc", "duoquadragies": "dqc", "terquadragies": "tqc", "quaterquadragies": "qtqc", "quinquadragies": "qqc", "sexquadragies": "sxqc", "septquadragies": "spqc", "octoquadragies": "oqc", "novoquadragies": "nqc", "quinquagies": "pc", "unquinquagies": "upc", "duoquinquagies": "dpc", "terquinquagies": "tpc", "quaterquinquagies": "qtpc", "quinquinquagies": "qpc", "sexquinquagies": "sxpc", "septquinquagies": "sppc", "octoquinquagies": "opc", "novoquinquagies": "npc", "sexagies": "sc", "unsexagies": "usc", "duosexagies": "dsc", "tersexagies": "tsc", "quatersexagies": "qtsc", "quinsexagies": "qsc", "sexsexagies": "sxsc", "septsexagies": "spsc", "octosexagies": "osc", "novosexagies": "nsc"}
    prefixe = {"additionnel(s) après" : "addap",  "additionnel(s) avant" : "addav", "motion" : "mot", "liminaire" : "lim", "unique" : "unq", "intitulé de la proposition de loi" : "intPPL"}
    suffixe = {"état" : "E", "annexe" : "anx"}
    
    article = unicodedata.normalize("NFKC", article).lower()  # \xa0 = espace normal
    digits = re.sub(r"\D","",re.sub(r"\([^)]*\)", "", article))
    texte = re.sub(r"\([^()]*\)", "", article).strip()

    pref = ""
    for cle,code in prefixe.items():
        if cle in article :
            pref = code
            
    mult = ""
    for cle, code in multiplicatif.items():
        m = re.search(rf"(?<![a-zà-ÿ]){cle}(?![a-zà-ÿ])(?:\s+([a-z])(?![a-zà-ÿ]))?", texte)
        if m:
            mult = code + (m.group(1).upper() if m.group(1) else "")
            break

    lettre = ""
    if not mult:
        m = re.search(r"\d+(?:er)?\s+([a-z])(?![a-zà-ÿ0-9])", texte)
        if m:
            lettre = m.group(1).upper()

    suf = ""
    for cle,code in suffixe.items():
        if cle in article :
            if cle == "état" :
                suf = code + article[-1].upper()
            else : 
                suf = code

    id_article = pref + digits + mult + lettre + suf
    return(id_article)

def get_bloc_article(article : str) :
    article = unicodedata.normalize("NFKC", article).lower()  # \xa0 = espace normal
    pref = "Article "
    if "unique" in article :
        digits = "unique"
    elif "liminaire" in article :
        digits = "liminaire"
    elif "intitulé de la proposition de loi" in article :
        pref = ""
        digits = "Int. PPL"
    elif "motions" in article :
        pref = ""
        digits = "Motions"
    else :
        digits = re.sub(r"\D","",re.sub(r"\([^)]*\)", "", article))
    bloc = pref + digits
    return(bloc)


def get_id_bloc_article(article : str) -> str :   
    article = unicodedata.normalize("NFKC", article).lower()
    if "unique" in article :
        id_bloc = "unq"
    elif "liminaire" in article :
        id_bloc = "lim"
    elif "motion" in article :
        id_bloc = "mot"
    elif "intitulé de la proposition de loi" in article :
        id_bloc = "intppl"
    else :
        id_bloc = re.sub(r"\D","",re.sub(r"\([^)]*\)", "", article)) # extrait les nombres
    return(id_bloc)

# TEST
#print(get_id_bloc_article("Article unique"))
#print(get_id_bloc_article("Intitulé de la proposition de loi"))
#print(get_id_bloc_article("Motions"))
#print(get_id_bloc_article("Article 1er"))
#print(get_id_bloc_article("Article 49 (crédits de la mission) État B"))
#print(get_id_bloc_article("Article(s) additionnel(s) après Article 23 bis"))
#print(get_id_bloc_article("Article(s) additionnel(s) après Article 5 (Supprimé)"))
#print(get_id_bloc_article("Article(s) additionnel(s) après Article 24 (réservé jusqu'après les amendements portant article additionnel après l'article 30)"))

def get_url_articles(url_disc : str):
    try :
        session = get_session(url_disc)
        id_disc = get_id_disc(url_disc)
        com_seance = commission_ou_sceance(url_disc)
        url_base = "https://www.senat.fr/amendements/textes/commissions/" if com_seance == "Commission" else "https://www.senat.fr/amendements/textes/"
        url_articles = url_base + session + "/" + id_disc + ".html"
        return(url_articles)
    except Exception as e :
        print(f"Erreur URL des articles : {e}")




def abrev_groupe(input : str):
    groupe_liste = {"Groupe Les Républicains": "LR", "Groupe Union Centriste et Indépendants": "UCI", "Groupe Socialiste, Écologiste et Républicain": "SER", "Groupe Communiste Républicain Citoyen et Écologiste - Kanaky": "CRCE-K", "Groupe du Rassemblement Démocratique et Social Européen": "RDSE", "Groupe Rassemblement des démocrates, progressistes et indépendants": "RDPI", "Groupe Écologiste - Solidarité et Territoires": "GEST", "Groupe Les Indépendants - République et Territoires": "LIRT", "Groupe Union Nationale pour les Territoires": "RN", "Réunion administrative des Sénateurs ne figurant sur la liste d'aucun groupe": "NI"}
    abrev_input = "?"
    for groupe, abrev in groupe_liste.items() :
        if input == groupe :
            abrev_input = abrev           
    return(abrev_input)

TypeInfo = Literal["url_disc", "url_articles", "nb_parties"]
def get_info_from_id(id_disc: str, type_info: TypeInfo) -> Optional[str]:
    with get_db() as conn:
        requete = f"SELECT {type_info} FROM discussion WHERE id_disc = '{id_disc}'"
        df = pd.read_sql(requete, conn,)
    info = df.iloc[0, 0]
    return(info)

def turn_into_content(df : pd.DataFrame, id_disc, ordre) :
    df["id_partie"] = id_disc + "-p" + str(ordre)
    df["id_article"] = id_disc + "-" + df["article"].apply(lambda x : get_id_article(x))                                     
    df["id_amdt"] = df["id_article"] + "-" + df["amdt"].apply(lambda x : get_id_amdt(x))           
    df["is_ss_amdt"] = is_ss_amdt(df["amdt"])
    df["lien_amdt"] = get_info_from_id(id_disc,"url_disc").replace("liste_discussion.html","") + df["lien_amdt"]
    df["is_active"] = 1
    df = df[["id_amdt","id_article","id_partie","article","amdt","is_ss_amdt","lien_amdt","lien_article","auteur","url_senateur","sort", "is_active"]]
    return(df)

def turn_into_ordre(df : pd.DataFrame, id_disc, ordre) :
    df["id_article"] = id_disc + "-" + df["article"].apply(lambda x : get_id_article(x))
    df["id_amdt"] = df["id_article"] + "-" + df["amdt"].apply(lambda x : get_id_amdt(x))
    df["id_partie"] = id_disc + "-p" + str(ordre)
    df["ordre_examen_in_partie"] = df.index
    df = df[["id_amdt", "id_partie","ordre_examen_in_partie"]]
    return(df)

# un avec un s et l'autre sans ... faire du tri
def get_url_article(article : str, id_disc : str):
    url_articles = get_info_from_id(id_disc, "url_txt")
    url_articles = url_articles + "#AMELI_SUB_4__Article_" + get_id_bloc_article(article)
    return(url_articles)



def ffill_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for idx, row in df.iterrows():
        if pd.isna(row["ordre_examen_in_partie"]):
            # lignes des blocs précédents qui ont un ordre
            precedents = df[(df["bloc"] < row["bloc"]) & df["ordre_examen_in_partie"].notna()]
            if precedents.empty:
                df.at[idx, "ordre_examen_in_partie"] = -1   # tout en haut
            else:
                bloc_prec = precedents["bloc"].max()
                max_value = precedents.loc[precedents["bloc"] == bloc_prec, "ordre_examen_in_partie"].max()
                df.at[idx, "ordre_examen_in_partie"] = max_value   # juste après le bloc précédent
    return df    