# Import des librairies
import pandas as pd
from pathlib import Path
import sys
import math
import streamlit as st
from reportlab.platypus import KeepTogether


# Chemin de la racine
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from reportlab.lib.styles import getSampleStyleSheet
from fonctions.fonctions_scrapping_cleaning.fonctions_cleaning import abrev_article
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.platypus import Table, Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
import pandas as pd
from fonctions.fonctions_tableau.get_tab_to_aff import retrieve_tab, retrieve_infos_disc, retrieve_info_articles





##### STYLES ####
# faut définir la fontSize en fonction du nbr de char
style_titre = ParagraphStyle(
    "Texte",
    fontName="Helvetica",
    fontSize=24,
    textColor=colors.HexColor("#333333"),
    alignment=TA_LEFT,
    wordWrap="CJK",
    leading=28,
)

style_partie = ParagraphStyle(
    "Texte",
    fontName="Helvetica",
    fontSize=20,
    textColor=colors.HexColor("#333333"),
    alignment=TA_LEFT,
    leading=25,
)

style_article = ParagraphStyle(
    "Texte",
    fontName="Helvetica",
    fontSize=18,
    textColor=colors.HexColor("#333333"),
    alignment=TA_LEFT,
    leading=20,
)

style_vote = TableStyle([
    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#000000")),
    ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ("TOPPADDING", (0, 0), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]
)


style_cellule = ParagraphStyle(
    "Cellule",
    fontName="Helvetica",
    fontSize=7,
    leading=9,  # Hauteur entre les lignes de texte
    alignment=TA_LEFT,
    wordWrap="CJK"
)

style_texte_vote = ParagraphStyle(
    "TexteVote",
    fontName="Helvetica",
    fontSize=10,
    textColor=colors.HexColor("#333333"),
    alignment=TA_LEFT,
    leading=13)

style_bordure_vote = TableStyle([
    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#000000")),
    ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ("TOPPADDING", (0, 0), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
])

def encadrer_vote(texte):
    paragraphe = Paragraph(texte,style_texte_vote)
    tableau = Table([[paragraphe]],hAlign="LEFT")
    tableau.setStyle(style_bordure_vote)
    return(tableau)


def df2table(df):

    # Transformer les noms de colonnes
    header = [Paragraph(str(col), style_cellule)for col in df.columns]
    data = [header]
    for ligne in df.itertuples(index=False, name=None):
        data.append([
            Paragraph(str(val) if val is not None else "", style_cellule)
            for val in ligne
        ])

    table = Table(
            data,
            colWidths= [50, 100, 90, 180, 100, 80, 80, 60, 50],
            style=[
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                #('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
                #('BOX', (0,0), (-1,-1), 1, colors.black),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#B7C9D6")),
                #("BACKGROUND", (3, 5), (3, 5), colors.yellow))
                ],
            hAlign = 'LEFT',
            splitByRow=1,
            splitInRow=1)
    
    return table

def generer_content(search : str, list_articles_selected : list, id_partie = None):
    content = []

    # Récupérer les infos
    df_votes_articles = retrieve_info_articles(search)
    dict_votes_articles = dict(zip(
                df_votes_articles["id_article"].astype(str),
                df_votes_articles["proposition_vote_article"]))

    dict_resumes_article = dict(zip(
                df_votes_articles["id_article"].astype(str),
                df_votes_articles["resume_article"]))
    
    df = retrieve_tab(search)
    df_infos_disc = retrieve_infos_disc(search)
    titre_discussion = (df_infos_disc["titre_disc_long"].iloc[0])
    

    # Ajout du titre
    content.append(Paragraph(str(titre_discussion), style_titre))
    content.append(Spacer(1, 12))

    if id_partie :
        df = df[df["id_partie"] == id_partie]

    parties = (df[["id_partie", "titre_partie"]].dropna(subset=["id_partie"]).drop_duplicates(subset=["id_partie"],keep="first"))
    for id_partie, titre_partie in parties.itertuples(index=False, name=None):

        # Ajout de la partie
        content.append(Paragraph(str(titre_partie), style_partie))
        df["id_partie"] = df["id_partie"].ffill()

        # Filtre sur les parties
        df_partie = df[df["id_partie"] == id_partie]
        df_partie = df_partie.sort_values(["bloc", "ordre_examen_in_partie"])

        articles = (df_partie[["bloc", "id_article", "article"]].drop_duplicates(subset=["bloc", "id_article", "article"]).sort_values(["bloc", "id_article"]))
        for bloc, id_article, article in  articles.itertuples(index=False, name=None) :
            df_by_article = df_partie[(df_partie["bloc"] == bloc)&(df_partie["id_article"] == id_article)]
            if id_article in list_articles_selected :

                content.append(Paragraph(str(article)))
                # content . append ==> résumé !
                content.append(Spacer(1, 12))

                df_amdt_actifs = df_by_article[df_by_article["amdt"].notna()& (pd.to_numeric(df_by_article["is_active"], errors="coerce") == 1)].sort_values("ordre_examen_in_partie")
                est_article_add = "add" in str(article).lower()

                if df_amdt_actifs.empty:    # si pas d'amdt actif
                    content.append(Paragraph("Pas d'amendement"))   # ajouter le style

                    if not est_article_add:
                        content.append(encadrer_vote(f"Vote sur {article} : {dict_votes_articles.get(id_article)}"))
                        content.append(Spacer(1, 6))

                else : 
                    df_for_pdf = df_amdt_actifs[["abrev_article","amdt","nom_groupe","objet","com","avis_com","avis_gouv","proposition_vote_amdt","sort"]]
                    df_for_pdf = df_for_pdf.rename(columns={"abrev_article": "Article", "amdt": "Amdt","nom_groupe" : "Auteur.rice", "objet" : "Objet", "com" : "Commentaire", "avis_com" : "Avis com", "avis_gouv" : "Avis gouv", "proposition_vote_amdt" : "Proposition vote", "sort" : "Sort"})
                    content.append(df2table(df_for_pdf))
                    content.append(Spacer(1, 6))

                    if est_article_add:
                        content.append(encadrer_vote(f"Vote sur {article} : {dict_resumes_article.get(id_article)}"))
                        content.append(Spacer(1, 6))
            else : 
                continue   
    return(content)

    

def generer_pdf(content) : 
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer,
                            pagesize = landscape(A4),
                            leftMargin=10,
                            rightMargin=10)
    doc.build(content)
    pdf_bytes = buffer.getvalue() 
    return(pdf_bytes)


### TEST
#content = generer_content("2026-2027-SCE-155",["2026-2027-SCE-155-2", "2026-2027-SCE-155-41"])
#generer_pdf(content)