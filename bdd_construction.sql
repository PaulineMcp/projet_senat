-- Code pour créer la BDD
-- Code pour créer la table discussion (il faudrait la renommer en PPL_PJL)
CREATE TABLE discussion(
    id_disc TEXT PRIMARY KEY,
    url_disc TEXT NOT NULL UNIQUE,
    titre_disc  TEXT NOT NULL,
    titre_disc_long TEXT,
    com_seance TEXT NOT NULL,
    lecture TEXT,
    lien_note TEXT DEFAULT '',
    lien_dossier TEXT DEFAULT '',
    url_articles TEXT
);

CREATE TABLE articles(
    id_article TEXT PRIMARY KEY,
    id_bloc_article TEXT,
    id_disc TEXT,
    article TEXT,
    ordre_article INT
);

CREATE TABLE amdts(
    id_amdt TEXT PRIMARY KEY,
    id_article TEXT NOT NULL,
    id_bloc_article TEXT NOT NULL,
    amdt TEXT NOT NULL,
    is_ss_amdt TEXT NOT NULL,
    lien_amdt TEXT,
    url_senateur TEXT NOT NULL,
    sort TEXT DEFAULT 'NA'
);

CREATE TABLE ordre_examen(
    ordre_amdt INT NOT NULL,
    id_amdt TEXT PRIMARY KEY
);

-- TEST --
CREATE TABLE ordre_examen(
    ordre_amdt INT NOT NULL,
    id_amdt TEXT
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

CREATE TABLE senateurs(
    url_senateur TEXT PRIMARY KEY UNIQUE,
    nom_groupe TEXT,
    civilite TEXT NOT NULL,
    nom TEXT NOT NULL,
    prenom TEXT NOT NULL,
    groupe TEXT NOT NULL
);

CREATE TABLE remplissage_ap_article(
    id_article TEXT PRIMARY KEY,
    resume_article TEXT,
    proposition_vote_article TEXT
);