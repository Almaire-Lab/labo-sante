# 📥 Session 2 — Pipeline d'ingestion

## Rôle du service `ingestor`

Conteneur **Python 3.12** qui :

1. **Génère** des données médicales synthétiques (faker FR)
2. **Insère en masse** dans PostgreSQL via `psycopg2` (référentiels + prescriptions + table de liaison N-N)
3. **Insère en masse** dans MongoDB via `pymongo` (collection `consultations`)
4. **Mesure** le temps d'ingestion par étape

## Structure du dossier

```
app/
├── Dockerfile              ← image Python construite localement
├── requirements.txt        ← psycopg2-binary, pymongo, faker, python-dotenv
├── generate_data.py        ← générateurs Faker (médecins, patients, etc.)
├── ingest_postgres.py      ← INSERT bulk Postgres (execute_values)
├── ingest_mongo.py         ← INSERT bulk Mongo (insert_many)
└── run_all.py              ← pipeline complet (Postgres puis Mongo)
```

## Variables d'environnement (lues du `.env`)

| Variable | Défaut | Rôle |
|---|---|---|
| `POSTGRES_HOST` | `postgres` | nom DNS du service Docker |
| `POSTGRES_USER` | (`.env`) | utilisateur Postgres |
| `POSTGRES_PASSWORD` | (`.env`) | mot de passe Postgres |
| `POSTGRES_DB` | `labo` | base cible |
| `MONGO_HOST` | `mongo` | nom DNS du service Docker |
| `MONGO_USER` | (`.env`) | utilisateur Mongo |
| `MONGO_PASSWORD` | (`.env`) | mot de passe Mongo |
| `MONGO_DB` | `labo` | base cible |
| `NB_MEDECINS` | `100` | nb médecins à générer |
| `NB_PATIENTS` | `5000` | nb patients |
| `NB_PRESCRIPTIONS` | `60000` | nb prescriptions Postgres |
| `NB_CONSULTATIONS` | `60000` | nb consultations Mongo |

## Lancer une ingestion

```bash
# Test 60k (rapide, ~45 sec)
docker compose --profile ingest run --rm ingestor

# Test 600k (~1m30)
NB_PRESCRIPTIONS=600000 NB_CONSULTATIONS=600000 \
NB_PATIENTS=20000 NB_MEDECINS=200 \
docker compose --profile ingest run --rm ingestor

# Test 6M (~15-20 min)
NB_PRESCRIPTIONS=6000000 NB_CONSULTATIONS=6000000 \
NB_PATIENTS=100000 NB_MEDECINS=500 \
docker compose --profile ingest run --rm ingestor
```

> **Note Windows PowerShell** : `$env:NB_PRESCRIPTIONS="600000"` puis lancer la commande.

> Le `profiles: ["ingest"]` dans le compose évite que `ingestor` démarre par défaut avec `docker compose up`. C'est un **script one-shot** — il s'exécute, fait son travail, sort.

## Idempotence

- `ON CONFLICT (email) DO NOTHING` sur médecins et patients
- `ON CONFLICT (nom_commercial, dosage, forme) DO NOTHING` sur médicaments
- Les prescriptions et consultations n'ont **pas** de clé naturelle → relancer l'ingestion **ajoute** de nouvelles lignes (pas de doublons logiques car les notes/symptômes sont aléatoires)

## Optimisations utilisées

| Technique | Gain |
|---|---|
| `execute_values()` (psycopg2) | 10-50× plus rapide que `executemany` |
| `insert_many(ordered=False)` (pymongo) | ne s'arrête pas au premier doublon |
| Batchs de 5000 lignes | équilibre RAM / commits |
| Index créés **avant** ingestion Mongo | pas de ré-indexation post-insertion |
| Image `python:3.12-slim` (~150 MB) | démarrage rapide |

## Résultats de benchmark (voir `docs/benchmarks/`)

| Volume | Temps total | Postgres | Mongo | Débit Mongo |
|---|---|---|---|---|
| 60 000 lignes | 44 s | 30 s | 14 s | 4 400 docs/s |
| 600 000 lignes | 93 s | 62 s | 31 s | 19 300 docs/s |
| 6 000 000 lignes | *voir log test-6M.log* | | | |
