""" Page de création d'une discussion """

###############     IMPORTS     ###############

# Import des librairies
import streamlit as st 
from pathlib import Path
import sys

# Chemin de la racine pour trouver les autres fichiers
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Fonctions
from fonctions.fonctions_checking import url_valide
from fonctions.fonctions_checking import disc_already_exist
from fonctions.fonctions_checking import is_not_google_doc

from fonctions.fonctions_cleaning import commission_ou_sceance
from fonctions.fonctions_cleaning import get_session
from fonctions.fonctions_cleaning import get_id_disc
from fonctions.fonctions_cleaning import get_url_articles

from fonctions.fonctions_scrapping import check_url

from fonctions.init_discussion import fetch_disc
from fonctions.init_discussion import fetch_articles
from fonctions.init_discussion import fetch_ordre_amdts
from fonctions.init_discussion import fetch_content_amdts
from fonctions.init_discussion import fetch_avis
from fonctions.init_discussion import init_remplissage_amdts
from fonctions.init_discussion import init_remplissage_articles

###############     PAGE    ###############

# Formulaire
col_gauche, col_centre, col_droite = st.columns([1,3,1])
with col_centre :
    st.title("Création d'un nouveau tableau")
    with st.form("my_form"):
        titre = st.text_input("Titre du PJL ou de la PPL", placeholder="exemple : PPL régime d'indemnisation des catastrophes naturelles")
        url_disc = st.text_input("Lien vers la page amendements", placeholder="exemple : https://www.senat.fr/amendements/commissions/2025-2026/689/liste_discussion.html")
        lien_dossier = st.text_input("Lien vers le dossier législatif", placeholder="exemple : https://www.senat.fr/dossier-legislatif/ppl23-612.html")
        lien_note = st.text_input("Lien vers le Google doc de la note du groupe")

        # Bouton pour soumettre
        submit = st.form_submit_button("Créer")

    # Soumettre le formulaire
    if submit:
            with st.spinner("Création du tableau ..."):

                erreurs = [] 

                # Nettoyer les saisies
                titre = titre.strip()
                url_disc = url_disc.strip()
                lien_note = lien_note.strip()
                lien_dossier = lien_dossier.strip()

                inputs = {
                    "titre" : titre,
                    "url" : url_disc,
                    "lien_note" : lien_note,
                    "lien_dossier" : lien_dossier,
                    "url_articles" : get_url_articles(url_disc)
                    }

                # Gestion des erreurs
                if not titre : 
                    erreurs.append("Le titre est obligatoire.")
                if not url_disc :
                    erreurs.append("Le lien vers les amendements est obligatoire")
                if not lien_dossier :
                    erreurs.append("Le lien du dossier est obligatoire")
                if url_valide(url_disc) == False :
                    erreurs.append("Le lien de la page des amendements est incorrect. Vérifiez le lien")
                if check_url(url_disc) != 200:
                    erreurs.append("L'accès à la page des amendements n'est pas possible. Vérifiez le lien")
                if is_not_google_doc(lien_note) :
                    erreurs.append("La note n'est pas un Google Doc")
                if disc_already_exist(url_disc) == True :
                    erreurs.append("Cette discussion est déjà surveillée")
                        
                # Affichage des erreurs
                if erreurs : 
                    for e in erreurs :
                        st.error(e)
                        st.stop()

                else :
                    # Identifier l'id de la discussion
                    session = get_session(url_disc)
                    com_seance = commission_ou_sceance(url_disc)
                    raw_com_seance = "COM" if com_seance == "Commission" else "SCE"
                    id_disc = session + "-" + raw_com_seance + "-" + get_id_disc(url_disc)
                    print(f"ID DISCUSSION : {id_disc}")

                    # Initiatilisation de la discussion dans la table discussion
                    print("TENTATIVE AJOUT DISCUSSION")
                    fetch_disc(url_disc, inputs)
                    print("DISCUSSION AJOUTEE !")

                    # Initialisation des titres et des articles dans leurs tables respectives
                    print("TENTATIVE RECUP ARTICLES")
                    fetch_articles(id_disc)
                    print("ARTICLES RECUPERES")                  

                    # Initialise l'ordre des amdts dans la table ordre_examen
                    print("TENTATIVE RECUP ORDRE AMDTS")
                    fetch_ordre_amdts(url_disc)
                    print("ORDRE AMDTS RECUPERES !")
                    
                    # Initialise le contenu des amdt dans la table admts
                    print("TENTATIVE RECUP CONTENU AMDTS")
                    fetch_content_amdts(url_disc)
                    print("CONTENU DES AMDTS RECUPERE !")

                    # Initialiser les avis dans la table avis
                    print("TENTATIVE RECUP AVIS")
                    fetch_avis(id_disc)
                    print("AVIS RECUPERES")

                    # Initialisation des cases objets, commentaires et vote des amdts
                    print("TENTATIVE INIT OBJET ET COM")
                    init_remplissage_amdts(id_disc)
                    print("INIT OBJET ET COM")

                    # Initialisation des cases resumes et votes des articles
                    print("TENTATIVE INIT VOTES")
                    init_remplissage_articles(id_disc)
                    print("INIT VOTES")
                    st.success("Enregistré")

    st.space("large")

    col_gauche, col_bouton = st.columns([1.7,1])
    with col_bouton:
        if st.button("Voir la liste des tableaux déjà créés", width="stretch"):
            st.switch_page("pages/discussions.py")