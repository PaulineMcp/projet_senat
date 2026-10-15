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

def get_row_height(df, colonnes_largeurs) :
    PX_PAR_CARACTERE = 7      # largeur moyenne d'un caractère
    PX_PAR_LIGNE = 22         # hauteur d'une ligne de texte
    PADDING_CELLULE = 16      # marge haut + bas dans la cellule
    HAUTEUR_MIN = 35
    nb_lignes_max = 1
    for colonne, largeur_px in colonnes_largeurs.items():
        caracteres_par_ligne = max(1, largeur_px // PX_PAR_CARACTERE)
        for texte in df[colonne].dropna().astype(str):
            nb_lignes = math.ceil(len(texte) / caracteres_par_ligne)
            nb_lignes_max = max(nb_lignes_max, nb_lignes)

    return max(HAUTEUR_MIN, nb_lignes_max * PX_PAR_LIGNE + PADDING_CELLULE)