""" Fonctions d'affichage du tableau :
    -   couleur_sort : selection de la couleur en fonction du sort
    -   get_row_height : hauteur des lignes en fonctions de l'objet le plus long du tableau
"""

###############     IMPORTS     ###############
import math

def couleur_sort(val):
    if str(val).strip() == "Adopté":
        return "background-color: #198754; color: #ffffff"
    if str(val).strip() == "Rejeté":
        return "background-color: #dc0425; color: #ffffff"
    if str(val).strip() == "Tombé":
            return "background-color: #1b1e3b; color: #ffffff"
    if str(val).strip() == "Retiré":
            return "background-color: #1b1e3b; color: #ffffff"
    return ""

def couleur_parti(val):
    if  "(GEST)" in str(val) :
        return "background-color: #079C63; color: #ffffff"
    if "ouvernement" in str(val) :
        return "background-color: #A09CD6; color: #ffffff"
    else :
        return ""

def couleur_completion(val):
    if  "compléter" in str(val) :
        return "background-color: #FCFABB; color: #ffffff"
    # gérer l'affichage si c'est le gouvernement
    else :
        return ""

def couleur_ss_amdt(val):
    if  "S/A" in str(val) :
        return "background-color: #8F8F7B; color: #ffffff"
    else :
        return ""