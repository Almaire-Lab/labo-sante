# Cahier des charges — Plateforme de données Labo Santé

## 1. Contexte

Un laboratoire de santé souhaite **centraliser ses données médicales** aujourd'hui éclatées entre plusieurs fichiers et logiciels métier. L'objectif est de bâtir une plateforme de données :

- **fiable** (intégrité référentielle, pas de perte au redémarrage),
- **scalable** (capable d'ingérer plusieurs millions de consultations),
- **administrable** (interfaces web pour explorer les données),
- **observable** (monitoring temps réel des services),
- **portable** (tout est containerisé, déployable en une commande).

À terme, ces données alimenteront des modèles IA (prédiction de prescription, détection d'interactions médicamenteuses, NLP sur les consultations).

## 2. Données à gérer

| Domaine | Type | Stockage cible | Justification |
|---|---|---|---|
| Médecins | structuré | PostgreSQL | schéma stable, jointures |
| Patients | structuré | PostgreSQL | schéma stable, intégrité forte |
| Médicaments | structuré | PostgreSQL | référentiel, peu volatile |
| Prescriptions | structuré (N-N) | PostgreSQL | relations patient ↔ médecin ↔ médicament |
| Consultations | semi-structuré | MongoDB | symptômes/diagnostics de longueur et structure variables, pas de jointures nécessaires |

## 3. Besoins fonctionnels

- **F1** — Enregistrer/consulter médecins, patients, médicaments via une UI (pgAdmin).
- **F2** — Créer des prescriptions liant patient + médecin + 1..N médicaments.
- **F3** — Stocker les consultations (symptômes libres, diagnostic structuré, notes) avec lien `patient_id` vers PostgreSQL.
- **F4** — Ingérer en masse des données simulées (jusqu'à 6 M de consultations) pour tester la volumétrie.
- **F5** — Re-exécuter le pipeline sans créer de doublons (idempotence).
- **F6** — Consulter en temps réel l'état des services et leurs logs (Portainer).

## 4. Besoins techniques

| Catégorie | Exigence |
|---|---|
| Conteneurisation | `docker compose up -d` démarre **tous** les services |
| Persistance | volumes Docker pour Postgres et Mongo (survie à `down`) |
| Réseau | un réseau Docker isolé, communication inter-services par **nom de service** (`postgres`, `mongo`…) |
| Secrets | aucun mot de passe en dur — variables via fichier `.env` (jamais commité) |
| Ordonnancement | `depends_on` + `healthcheck` pour démarrer l'ingestor seulement quand les bases sont **prêtes** |
| Observabilité | pgAdmin (Postgres UI), Mongo Express (Mongo UI), Portainer (Docker UI), `docker stats` |
| Reproductibilité | `.env.example`, `requirements.txt`, `Dockerfile` versionnés ; `.gitignore` strict |

## 5. Périmètre

**Inclus :** modélisation, infra Docker, pipeline d'ingestion Python, monitoring infra, documentation.
**Hors périmètre :** authentification utilisateurs finaux, frontal métier, RGPD opérationnel (données 100 % synthétiques pour le TP), entraînement de modèles IA.

## 6. Critères d'acceptation

- [ ] `docker compose up -d` démarre tous les services sans erreur.
- [ ] pgAdmin accessible sur `localhost:5050`, Mongo Express sur `localhost:8081`, Portainer sur `localhost:9000`.
- [ ] Schéma SQL créé automatiquement au premier démarrage (`init.sql`).
- [ ] Ingestion de 60 000 / 600 000 / 6 000 000 lignes mesurée (temps + RAM).
- [ ] Aucune donnée perdue après `docker compose down && docker compose up -d`.
- [ ] Aucun secret en clair dans le dépôt Git.
