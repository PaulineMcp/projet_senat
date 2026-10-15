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

###############     FONCTIONS     ###############
def get_id_disc(url_disc):
    if commission_ou_sceance(url_disc) == "Commission":
        id = url_disc[55:].replace("/liste_discussion.html","")
    else :
        id = url_disc[43:].replace("/liste_discussion.html","")
    return(id)

def get_id_amdt(amdt):
    amdt = amdt.replace("\n","")
    digits = amdt.replace("Amt n° ","")
    digits = digits.replace("Motion n° ","")
    if "rect. decies" in amdt:
        id_amdt = digits.replace(" rect. decies","") + "rdc"
    elif "rect. nonies" in amdt:
        id_amdt = digits.replace(" rect. nonies","") + "rnn"
    elif "rect. octies" in amdt:
        id_amdt = digits.replace(" rect. octies","") + "roc"
    elif "rect. septies" in amdt:
        id_amdt = digits.replace(" rect. septies","") + "rsp"
    elif "rect. sexties" in amdt:
        id_amdt = digits.replace(" rect. sexties","") + "rsx"
    elif "rect. quinquies" in amdt:
        id_amdt = digits.replace(" rect. quinquies","") + "rqq"
    elif "rect. quater" in amdt:
        id_amdt = digits.replace(" rect. quater","") + "rqt"
    elif "rect. ter" in amdt:
        id_amdt = digits.replace(" rect. ter","") + "rt"
    elif "rect. bis" in amdt:
        id_amdt = digits.replace(" rect. bis","") + "rb"
    elif "rect." in amdt:
        id_amdt = digits.replace(" rect.","") + "r"      
    else : 
        id_amdt = digits  
    return(id_amdt)

def commission_ou_sceance(url_pjl) :
    if "commission" in url_pjl:
        return("Commission")
    else:
        return("Séance")
     
def get_session(url):
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

def abrev_article(article):  
    prefixe = ""
    digits = re.sub(r"\D","",re.sub(r"\([^)]*\)", "", article)) # produit une liste de chiffre
    suffixe = ""
    if "decies" in article:
        suffixe = "decies"
    if "nonies" in article:
        suffixe = "nonies"
    if "octies" in article:
        suffixe = "octies"
    if "septies" in article:
        suffixe = "septies"
    if "sexties" in article:
        suffixe = "sexties"
    if "quinquies" in article:
        suffixe = "quinquies"
    if "quater" in article:
        suffixe = "quater"
    if "ter" in article:
        suffixe = "ter"
    if "bis" in article:
        suffixe = "bis"  

    if "Motion" in article:
        prefixe = "Motion "
    elif "Lim. " in article:
        prefixe = "Lim"
    elif "additionnel avant" in article : 
        prefixe = "Add av art. "
    elif "additionnel(s) avant" in article : 
        prefixe = "Add av art. "
    elif "additionnel après" in article : 
        prefixe = "Add ap art. "
    elif "additionnel(s) avant" in article : 
        prefixe = "Add av art. "
    else : 
        prefixe = "Art. "
    abrev = prefixe + digits + " " + suffixe             
    return(abrev)

def get_id_article(article, id_disc) :
    article = unicodedata.normalize("NFKC", article)  # \xa0 = espace normal
    article = " ".join(article.split())

    if "additionnel(s) après" in article :
        article = article.replace("Article(s) additionnel(s) après Article ","addap")
    elif "additionnel(s) avant" in article :
        article = article.replace("Article(s) additionnel(s) avant Article ","addav") 
    else : 
        article = article.replace("Article ","")

    if "er" in article :
        article = article.replace("er","")
    if "(" in article :
        article = re.sub(r" \(.*$", "", article, flags=re.DOTALL)
    if "decies" in article:
        article = article.replace(" decies","") + "dc"
    if "nonies" in article:
        article = article.replace(" nonies","") + "nn"
    if "octies" in article:
        article = article.replace(" octies","") + "oc"
    if "septies" in article:
        article = article.replace(" septies","") + "sp"
    if "sexties" in article:
        article = article.replace(" sexties","") + "sx"
    if "quinquies" in article:
        article = article.replace(" quinquies","") + "qq"
    if "quater" in article:
        article = article.replace(" quater","") + "qt"
    if "ter" in article:
        article = article.replace(" ter","") + "t"
    if "bis" in article:
        article = article.replace(" bis","") + "b"
    id_article = id_disc + "-" + article
    return(id_article)

def get_id_bloc_article(article, id_disc):
    article = unicodedata.normalize("NFKC", article)
    article = " ".join(article.split())

    if "additionnel(s) après" in article :
        article = article.replace("Article(s) additionnel(s) après Article ","")
    elif "additionnel(s) avant" in article :
        article = article.replace("Article(s) additionnel(s) avant Article ","") 
    else : 
        article = article.replace("Article ","")

    if "er" in article :
        article = article.replace("er","")
    if "(" in article :
        article = re.sub(r" \(.*$", "", article, flags=re.DOTALL)
    if "decies" in article:
        article = article.replace(" decies","") + "dc"
    if "nonies" in article:
        article = article.replace(" nonies","") + "nn"
    if "octies" in article:
        article = article.replace(" octies","") + "oc"
    if "septies" in article:
        article = article.replace(" septies","") + "sp"
    if "sexties" in article:
        article = article.replace(" sexties","") + "sx"
    if "quinquies" in article:
        article = article.replace(" quinquies","") + "qq"
    if "quater" in article:
        article = article.replace(" quater","") + "qt"
    if "ter" in article:
        article = article.replace(" ter","") + "t"
    if "bis" in article:
        article = article.replace(" bis","") + "b"
    id_article = id_disc + "-" + article
    return(id_article)

def get_url_articles(url_disc):
    session = get_session(url_disc)
    id_disc = get_id_disc(url_disc)
    com_seance = commission_ou_sceance(url_disc)
    url_base = "https://www.senat.fr/amendements/textes/commissions/" if com_seance == "Commission" else "https://www.senat.fr/amendements/textes/"
    url_articles = url_base + session + "/" + id_disc + ".html"
    return(url_articles)

def abrev_groupe(groupe):
    match groupe:
        case "Groupe Les Républicains":
            return "LR"
        case "Groupe Union Centriste et Indépendants":
            return "UCI"
        case "Groupe Socialiste, Écologiste et Républicain":
            return "SER"
        case "Groupe Communiste Républicain Citoyen et Écologiste - Kanaky":
            return "CRCE-K"
        case "Groupe du Rassemblement Démocratique et Social Européen":
            return "RDSE"
        case "Groupe Rassemblement des démocrates, progressistes et indépendants":
            return "RDPI"
        case "Groupe Écologiste - Solidarité et Territoires":
            return "GEST"
        case "Groupe Les Indépendants - République et Territoires":
            return "LIRT"
        case "Groupe Union Nationale pour les Territoires":
            return "RN"
        case "Réunion administrative des Sénateurs ne figurant sur la liste d'aucun groupe":
            return "NI"
        case _:
            return "?"