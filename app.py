# Pour gérer la navigation
import streamlit as st

accueil = st.Page("pages/accueil.py", title="Accueil", default=True) # à quoi sert le default ici ??
creer_discussion = st.Page("pages/creer_discussion.py", title = "Créer une discussion")
recherche = st.Page("pages/recherche.py", title="Recherche")
discussions = st.Page("pages/discussions.py", title="Discussions")
afficher_tab_amdts = st.Page("pages/afficher_tab_amdts.py", title="Afficher tab amdts")
vue_seule_tab_amdts = st.Page("pages/vue_seule_tab_amdts.py", title="Afficher tab amdts vue seule")

# Header

st.set_page_config(layout="wide")

st.markdown(
    """
    <style>
        /* Le conteneur entier (titre + bouton) est collé en haut */
        .st-key-header_site {
            position: fixed;
            padding : 5px;
            top: 0.4rem;
            left: 0.75rem;
            z-index: 999991;
            width: 100%;
            align-items: center;      /* alignement vertical titre / bouton */
        }
        .st-key-header_site p { margin: 0; }   /* retire la marge du texte */

        /* Le contenu des pages commence sous le header */
        .block-container { padding-top: 4rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.container(key="header_site", horizontal=True, vertical_alignment="center"):
    col_button, col_titre = st.columns([1,2])
    with col_button :
        if st.button("🏠 Accueil", key="btn_accueil"):
            st.switch_page("pages/accueil.py")
    with col_titre : 
        st.markdown('<p style="font-size:30px;">Suivi des amendements du Sénat</p>', unsafe_allow_html=True)


pg = st.navigation([accueil, creer_discussion, recherche, discussions, afficher_tab_amdts, vue_seule_tab_amdts])

##### STYLE


print("LANCEMENT NEW")
pg.run()