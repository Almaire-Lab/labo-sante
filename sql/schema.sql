-- ============================================================
-- Labo Santé — Schéma PostgreSQL
-- Exécuté automatiquement par Postgres au 1er démarrage
-- (monté via /docker-entrypoint-initdb.d/ dans docker-compose)
-- ============================================================

-- ---------- Référentiels ----------

CREATE TABLE IF NOT EXISTS medecins (
    id              SERIAL PRIMARY KEY,
    nom             VARCHAR(80)  NOT NULL,
    prenom          VARCHAR(80)  NOT NULL,
    specialite      VARCHAR(120) NOT NULL,
    email           VARCHAR(160) UNIQUE,
    telephone       VARCHAR(20),
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS patients (
    id              SERIAL PRIMARY KEY,
    nom             VARCHAR(80)  NOT NULL,
    prenom          VARCHAR(80)  NOT NULL,
    date_naissance  DATE         NOT NULL,
    sexe            CHAR(1)      NOT NULL CHECK (sexe IN ('M','F','X')),
    email           VARCHAR(160) UNIQUE,
    telephone       VARCHAR(20),
    adresse         TEXT,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS medicaments (
    id              SERIAL PRIMARY KEY,
    nom_commercial  VARCHAR(160) NOT NULL,
    dci             VARCHAR(160) NOT NULL,            -- Dénomination Commune Internationale
    dosage          VARCHAR(60)  NOT NULL,            -- ex: "500 mg"
    forme           VARCHAR(60)  NOT NULL,            -- comprimé, sirop, injection...
    laboratoire     VARCHAR(120),
    UNIQUE (nom_commercial, dosage, forme)
);

-- ---------- Transactionnel ----------

CREATE TABLE IF NOT EXISTS prescriptions (
    id                SERIAL PRIMARY KEY,
    patient_id        INT  NOT NULL REFERENCES patients(id)  ON DELETE RESTRICT,
    medecin_id        INT  NOT NULL REFERENCES medecins(id)  ON DELETE RESTRICT,
    date_prescription DATE NOT NULL DEFAULT CURRENT_DATE,
    notes             TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Table de liaison N-N : une prescription contient plusieurs médicaments
CREATE TABLE IF NOT EXISTS prescription_medicaments (
    prescription_id INT NOT NULL REFERENCES prescriptions(id) ON DELETE CASCADE,
    medicament_id   INT NOT NULL REFERENCES medicaments(id)   ON DELETE RESTRICT,
    posologie       VARCHAR(200) NOT NULL,    -- ex: "1 cp matin et soir pendant les repas"
    duree_jours     INT          NOT NULL CHECK (duree_jours > 0),
    PRIMARY KEY (prescription_id, medicament_id)
);

-- ---------- Index pour les requêtes fréquentes ----------

CREATE INDEX IF NOT EXISTS idx_prescriptions_patient  ON prescriptions(patient_id);
CREATE INDEX IF NOT EXISTS idx_prescriptions_medecin  ON prescriptions(medecin_id);
CREATE INDEX IF NOT EXISTS idx_prescriptions_date     ON prescriptions(date_prescription);
CREATE INDEX IF NOT EXISTS idx_patients_nom           ON patients(nom);
CREATE INDEX IF NOT EXISTS idx_medicaments_dci        ON medicaments(dci);
