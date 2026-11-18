-- Code pour créer la BDD
CREATE TABLE discussion(
    id_disc TEXT PRIMARY KEY,
    url_disc TEXT NOT NULL UNIQUE,
    titre_disc  TEXT NOT NULL,
    titre_disc_long TEXT,
    nb_parties INT,
    com_seance TEXT NOT NULL,
    lecture TEXT,
    last_hash TEXT NOT NULL,
    lien_note TEXT DEFAULT '',
    lien_dossier TEXT DEFAULT '',
    url_txt TEXT,
    is_archived INT DEFAULT 0
);

CREATE TABLE parties(
    id_partie TEXT PRIMARY KEY,
    id_disc TEXT NOT NULL,
    titre_partie TEXT NOT NULL,
    ordre_partie INT NOT NULL
);

CREATE TABLE amdts(
    id_amdt TEXT PRIMARY KEY,
    id_article TEXT NOT NULL,
    id_partie TEXT NOT NULL,
    article TEXT NOT NULL,     
    amdt TEXT NOT NULL,
    is_ss_amdt TEXT NOT NULL,
    lien_amdt TEXT,
    lien_article TEXT,
    auteur TEXT,
    url_senateur TEXT,
    sort TEXT DEFAULT 'NA'
);

CREATE TABLE ordre_examen(
    id_amdt TEXT PRIMARY KEY,
    id_partie TEXT NOT NULL,
    ordre_examen_in_partie INT NOT NULL,
    ordre_examen_abs INT NOT NULL 
);

CREATE TABLE articles(
    id_bloc_article TEXT,
    bloc_article TEXT,
    bloc TEXT,
    id_article TEXT PRIMARY KEY,
    id_disc TEXT,
    article TEXT,
    lien_article TEXT
);

CREATE TABLE avis(
    id_amdt TEXT PRIMARY KEY,
    avis_gouv TEXT DEFAULT 'NA',
    avis_com TEXT DEFAULT 'NA'
);

CREATE TABLE remplissage_ap_amdt(
    id_amdt TEXT PRIMARY KEY,
    objet TEXT NULL,
    com TEXT NULL,
    proposition_vote_amdt TEXT
);

CREATE TABLE remplissage_ap_article(
    id_article TEXT PRIMARY KEY,
    resume_article TEXT,
    proposition_vote_article TEXT
);

CREATE TABLE senateurs(
    url_senateur TEXT PRIMARY KEY UNIQUE,
    nom_groupe TEXT,
    civilite TEXT NOT NULL,
    nom TEXT NOT NULL,
    prenom TEXT NOT NULL,
    groupe TEXT NOT NULL
);