""" Page de création d'une discussion """

###############     IMPORTS     ###############

# Import des librairies
from utils import *

# Fonctions
from fonctions.fonctions_scrapping_cleaning.fonctions_checking import url_valide, disc_already_exist, is_not_google_doc
from fonctions.fonctions_scrapping_cleaning.fonctions_cleaning import commission_ou_sceance, get_session, get_id_disc, get_url_articles
from fonctions.fonctions_scrapping_cleaning.fonctions_scrapping import check_url
from fonctions.init_discussion import init_remplissage_amdts, init_remplissage_articles, init_disc, init_content, init_articles, init_avis
#from fonctions.init_discussion import fetch_content_amdts
#from fonctions.init_discussion import fetch_avis
#from fonctions.init_discussion import init_remplissage_amdts
#from fonctions.init_discussion import init_remplissage_articles

###############     PAGE    ###############

# Formulaire
col_gauche, col_centre, col_droite = st.columns([1,3,1])
with col_centre :
    st.title("Création d'un nouveau tableau")
    with st.form("my_form"):
        titre = st.text_input("Titre du PJL ou de la PPL", placeholder="exemple : PPL régime d'indemnisation des catastrophes naturelles")
        url_disc = st.text_input("Lien vers la page amendements", placeholder="exemple : https://www.senat.fr/amendements/commissions/2025-2026/689/liste_discussion.html")
        lien_dossier = st.text_input("Lien vers le dossier législatif", placeholder="exemple : https://www.senat.fr/dossier-legislatif/ppl23-612.html")
        lien_note = st.text_input("Lien vers le Google Doc de la note du groupe")

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
                    erreurs.append("Ce tableau existe déjà")
                        
                # Affichage des erreurs
                if erreurs : 
                    for e in erreurs :
                        st.error(e)
                        st.stop()

                else :

                    inputs = {
                    "titre" : titre,
                    "url" : url_disc,
                    "lien_note" : lien_note,
                    "lien_dossier" : lien_dossier,
                    "url_txt" : get_url_articles(url_disc)
                    }

                    # Identifier l'id de la discussion
                    session = get_session(url_disc)
                    com_seance = commission_ou_sceance(url_disc)
                    raw_com_seance = "COM" if com_seance == "Commission" else "SCE"
                    id_disc = session + "-" + raw_com_seance + "-" + get_id_disc(url_disc)
                    print(f"id discussion : {id_disc}")

                    print(inputs)

                    try:
                        init_disc(url_disc, inputs)
                        init_content(id_disc)
                        init_articles(id_disc)
                        init_avis(id_disc)
                        init_remplissage_amdts(id_disc)
                        init_remplissage_articles(id_disc)
                        st.success("Enregistré")
                    except Exception as e:
                        print(f"Erreur : {e}")
                        with get_db() as conn:
                            conn.execute("DELETE FROM discussion WHERE id_disc = ?", (id_disc,))
                        raise 


                    #fetch_content(id_disc)
                    
                    #fetch_all_articles(id_disc)
                    #print("articles récupérés")
                  

                    #fetch_avis(id_disc)
                    #print("AVIS RECUPERES")

                    #init_remplissage_amdts(id_disc)
                    #print("OBJET ET COM INITIALISES")
                    #init_remplissage_articles(id_disc)
                    #print("VOTES INITIALISES")
                    

    st.space("large")

    col_gauche, col_bouton = st.columns([1.7,1])
    with col_bouton:
        if st.button("Voir la liste des tableaux déjà créés", width="stretch"):
            st.switch_page("pages/discussions.py")