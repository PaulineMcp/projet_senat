""" Principales fonctions pour permettre le scrapping
        - check_url : vérifier que l'URL répond correctement
        - get_content_page : extraire le contenu d'une page
        - get_tab : extraire le tableau d'une page
        - parsing_line_tab : parser un tableau pour récupérer les infos sur le contenu de l'amdt
         - clean_amdt_info : c
        - parsing_sort_tab : parser un tableau pour récupérer l'ordre des amdts
        - clean_tab_ordre :  - clean_amdt_info
        - get_avis_com : récupérer l'avis de la commission
        - get_avis_gouv : récupérer l'avis du gouvernement
        - get_lecture : savoir s'il s'agit de la 1e ou 2e lecture 
"""
from pathlib import Path
import sqlite3
import streamlit as st 
import sys
import hashlib
import re
import requests
from bs4 import BeautifulSoup
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fonctions.fonctions_scrapping_cleaning.fonctions_cleaning import commission_ou_sceance, get_id_disc, get_session, get_id_article, get_id_bloc_article, get_id_amdt, is_ss_amdt
#get_avis_com, get_avis_gouv, get_tab_content
from utils import *

def check_url(url):
        try :
                r = requests.get(url)
                return(r.status_code)
        except : 
              return None

def get_content_page(url):
        try : 
                r = requests.get(url, timeout= 10)
                content = r.content.decode("utf-8")
                soup = BeautifulSoup(content, 'html.parser')
                return(soup)
        except Exception as e: 
              return("Erreur :", e)

# VA FALLOIR PREVOIR UNE FONCTION DE RETRY

#def get_tab(tab):
#    soup = get_content_page(url)
#    tab = soup.find_all('table')
#    tab = soup.find("tbody")
#    return(tab)

def get_tab_list(url : str):
      soup = get_content_page(url)
      tab_list = soup.find_all("table")
      return(tab_list)

#def get_tbody(tab) :      
#       tbody = tab.find("tbody")
#       return(tbody)

#def get_clean_tab(tbody) :
#       clean_tab = 
#       return(cleaned_tab)

      

def parsing_line(line):
        cells = line.find_all("td") # pour chaque ligne on regarde les cellules

        # 1ère cellule
        num_article =  num_article = " ".join(re.sub(r"\((?!s\))[^()]*\)", "", cells[0].text).split())
        try :
                lien_article = "https:" + (cells[0].find('a').get("href"))
        except :
                lien_article = "Pas de lien vers l'article"

        # 2ème cellule
        num_amdt = cells[1].text.strip()
        lien_amdt = cells[1].find('a').get("href")

        # 3ème cellule
        auteur =   cells[2].text.strip().replace("\t","").replace("\n","").title()
        try :
                lien_auteur = "https:" + (cells[2].find('a').get("href").replace("senfic/","senateur/"))
        except:
                lien_auteur = "Pas de lien vers l'auteur"

        # 4ème cellule
        try :      
                sort = line.find("span").text.replace("\t","").replace("\n","")
        except :
                sort = "à déterminer"
       
        line_tab = {
                "article" : num_article,
                "lien_article" : lien_article,
                "amdt" : num_amdt,
                "lien_amdt" : lien_amdt,
                "auteur" : auteur,
                "url_senateur" : lien_auteur,
                "sort" : sort
        }
        return(line_tab) # retourne un dictionnaire
    

# Nettoye une liste de tab en un unique tab prêt à être regardé
#def _tab(tab_list : set):
#        cleaned_tab = []
#        for tab in tab_list :
#              tbody = tab.find("tbody")


    

#clean_tab((get_tab_list("https://www.senat.fr/amendements/2025-2026/138/liste_discussion.html")))

#def clean_amdt_info(tab):
#    size = len(tab.contents)
#    df = []
#    for i in range(0 , size):
#        if i % 2 != 0:
#            line = parsing_line(tab.contents[i])
#            df.append(line)
#    df = pd.DataFrame(df)
 #   return(df)

def get_avis_gouv(url_amdt):
        try :
              soup = get_content_page(url_amdt)
              avis = soup.find_all(attrs={"align" : "left", "valign" : "top", "width" : "70%"})
              avis_gouv = avis[1].text.replace("\t","").replace("\n","")  
        except Exception as e :
                avis_gouv = "Avis non-trouvé"
        return(avis_gouv)
               

def get_avis_com(url_amdt):

    soup = get_content_page(url_amdt)
    avis = soup.find_all(attrs={"align" : "left", "valign" : "top", "width" : "70%"})
    avis_com = avis[0].text.replace("\t","").replace("\n","")  
    return(avis_com)

# Récupérer le numéro de lecture
def get_lecture(soup):
        page_lead = soup.find("p", {"class": "page-lead"})
        if "1ère" in page_lead.text :
            type_lecture = "1ère lecture"
        else :
            type_lecture = "2ème lecture"
        return(type_lecture)

# Récupérer l'etag d'une page
def get_hash(url):
        try : 
                r = requests.get(url)
                h = hashlib.sha256(r.content).hexdigest()
                return(h)
        except Exception as e: 
              return("Erreur :", e)

def get_disc_info(url): # URL de la discussion                 
    com_seance = commission_ou_sceance(url)
    id_disc = get_id_disc(url)
    lecture = get_lecture(get_content_page(url))
    session = get_session(url)
    

    raw_com_seance = "COM" if com_seance == "Commission" else "SCE"
    id_disc = session + "-" + raw_com_seance + "-" + id_disc
    return{
            "com_seance" : com_seance,
            "id_disc" : id_disc,
            "lecture" : lecture,
            "session" : session 
    }