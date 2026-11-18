README
# 1. Présentation du projet

# 2. Documentation du code

## 2.1 Les fichiers à la racine 

- utils.py : Contient les appels aux librairies nécéssaires, les constantes communes à tout le projet et les fonctions permettant de se connecter à la base de données et d'appeler la feuille de style
- .streamlit : 
    - config.toml : 
- app.py : Contient le code du header du site et les paramètres pour faire fonctionner la navigation dans Streamlit
- schema.sql


## Les pages

## Les scripts 
Dans le dossier pages, se trouvent tous les scripts qui permettent de générer les pages web

Dans le dossier scrapping, se trouvent tous les dossiers qui permettent de mettre à jour la base de données
    - fonctions_cleaning : regroupe les fonctions de base pour nettoyer les éléments scrappés (id, session, etc...)
    - fonctions_scrapping : regroupe des fonctions de scrapping
    - maj_amdt : met à jour la table amdt
    - maj_ordre_examen : met à jour l'ordre de discussion des amdt

LES DONNEES
Les données sénateurs sont dispo à cette adressehttps://www.senat.fr/vos-senateurs/recherche-de-senateurs/recherche-avancee-de-senateurs.csv

A cette adresse : un fichier en ligne qui expose la structure de la base de données
