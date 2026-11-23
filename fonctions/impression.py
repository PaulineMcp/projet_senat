# Récupération des parties dans leur ordre d'apparition
df_all_partie = retrieve_tab(search)
parties = (df_all_partie[["id_partie", "titre_partie"]].dropna(subset=["id_partie"]).drop_duplicates(subset=["id_partie"], keep="first"))
        


# Initialisation des états
if "afficher_options_impression" not in st.session_state:
    st.session_state["afficher_options_impression"] = False

if "afficher_checkbox" not in st.session_state:
    st.session_state["afficher_checkbox"] = False


# Bouton principal
if st.button("📄 Imprimer"):
    st.session_state["afficher_options_impression"] = (
        not st.session_state["afficher_options_impression"]
    )


if st.session_state["afficher_options_impression"]:

    with st.container(border=True):

        # Imprimer toute la discussion
        if st.button("Imprimer tout"):
            st.write("Génération du PDF complet...")

        # Afficher la sélection
        if st.button("Sélectionner les parties et articles"):
            st.session_state["afficher_checkbox"] = (
                not st.session_state["afficher_checkbox"]
            )

        if st.session_state["afficher_checkbox"]:

            st.write("### Choisir les parties et les articles")

            # Récupération des parties
            parties = (
                df_all_partie[
                    ["id_partie", "titre_partie"]
                ]
                .dropna(subset=["id_partie"])
                .drop_duplicates(subset=["id_partie"], keep="first")
            )

            for id_partie, titre_partie in parties.itertuples(
                index=False, name=None
            ):

                with st.container(border=True):

                    # Case à cocher de la partie
                    partie_cochee = st.button(
                        titre_partie,
                        key=f"select_partie_{id_partie}"
                    )

                    if partie_cochee:

                        # Récupération des articles de cette partie
                        df_articles = df_all_partie[
                            df_all_partie["id_partie"] == id_partie
                        ][
                            ["id_article", "article"]
                        ].dropna(subset=["id_article"]).drop_duplicates(
                            subset=["id_article"]
                        )

                        # Tout sélectionner dans cette partie
                        tout_selectionner = st.checkbox(
                            "Tout sélectionner",
                            key=f"tout_articles_{id_partie}"
                        )

                        for id_article, titre_article in df_articles.itertuples(
                            index=False, name=None
                        ):

                            st.checkbox(
                                titre_article,
                                value=tout_selectionner,
                                key=f"select_article_{id_partie}_{id_article}"
                            )

            # Bouton de génération
            if st.button("📄 Générer le PDF"):

                selection = []

                for id_partie, titre_partie in parties.itertuples(
                    index=False, name=None
                ):

                    if not st.session_state.get(
                        f"select_partie_{id_partie}", False
                    ):
                        continue

                    df_articles = df_all_partie[
                        df_all_partie["id_partie"] == id_partie
                    ][
                        ["id_article", "article"]
                    ].dropna(subset=["id_article"]).drop_duplicates(
                        subset=["id_article"]
                    )

                    for id_article, titre_article in df_articles.itertuples(
                        index=False, name=None
                    ):

                        if st.session_state.get(
                            f"select_article_{id_partie}_{id_article}",
                            False
                        ):
                            selection.append((id_partie, id_article))

                if selection:

                    df_export = df_all_partie[
                        df_all_partie.apply(
                            lambda ligne: (
                                ligne["id_partie"],
                                ligne["id_article"]
                            ) in selection,
                            axis=1
                        )
                    ].copy()

                    st.write("Articles sélectionnés :")
                    st.dataframe(df_export)

                else:
                    st.warning(
                        "Sélectionne au moins une partie et un article."
                    )
