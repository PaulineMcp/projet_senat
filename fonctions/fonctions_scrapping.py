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

######  IMPORTS #######

# Imports des librairies
import re
import requests
from bs4 import BeautifulSoup
import pandas as pd

#############   FONCTIONS   #####################

def check_url(url):
        try :
                r = requests.get(url)
                return(r.status_code)
        except : 
              return None

def get_content_page(url): # anciennement get_content_ppl_pjl
        try : 
                r = requests.get(url)
                content = r.content.decode("utf-8")
                soup = BeautifulSoup(content, 'html.parser')
                return(soup)
        except Exception as e: 
              return("Erreur :", e)

def get_tab(url):
    soup = get_content_page(url)
    tab = soup.find_all('table')
    tab = soup.find("tbody")
    return(tab)
    
def parsing_line_tab(line):
        cells = line.find_all("td") # pour chaque ligne on regarde les cellules
        
        num_article = cells[0].text.strip()
        try :
                lien_article = "https:" + (cells[0].find('a').get("href"))
        except :
                lien_article = "Pas de lien vers l'article"

        num_amdt = cells[1].text.strip()
        lien_amdt = cells[1].find('a').get("href")    
        try :
                lien_auteur = "https:" + (cells[2].find('a').get("href").replace("senfic/","senateur/"))
        except:
                lien_auteur = "Pas de lien vers l'amendement"       
        sort = line.find("span").text.replace("\t","").replace("\n","")
       
        line_tab = {
                "article" : num_article,
                "lien_article" : lien_article,
                "amdt" : num_amdt,
                "lien_amdt" : lien_amdt,
                "url_senateur" : lien_auteur,
                "sort" : sort
        }
        return line_tab
    
def parsing_sort_tab(line):
        cells = line.find_all("td") # pour chaque ligne on regarde les cellules       
        num_article = cells[0].text  
        num_amdt = cells[1].text
        line_tab = {
                "article" : num_article,
                "amdt" : num_amdt,
        }
        return line_tab
    
def clean_tab_ordre(tab):
    size = len(tab.contents)
    df = []
    for i in range(0 , size):
        if i % 2 != 0:
            line = parsing_sort_tab(tab.contents[i])
            df.append(line)
    df = pd.DataFrame(df)
    return(df)

def clean_amdt_info(tab):
    size = len(tab.contents)
    df = []
    for i in range(0 , size):
        if i % 2 != 0:
            line = parsing_line_tab(tab.contents[i])
            df.append(line)
    df = pd.DataFrame(df)
    return(df)

def get_avis_gouv(url_amdt):
    soup = get_content_page(url_amdt)
    avis = soup.find_all(attrs={"align" : "left", "valign" : "top", "width" : "70%"})
    avis_gouv = avis[1].text.replace("\t","").replace("\n","")  
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