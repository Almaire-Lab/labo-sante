"""
Ingestion MongoDB — labo-sante
- Collection unique `consultations`
- Insert en bulk via insert_many (ordered=False, plus rapide)
- Crée les index recommandés si absents
"""
import os
import sys
import time
from pymongo import MongoClient, ASCENDING, DESCENDING

from generate_data import gen_consultation


def connect():
    user = os.environ["MONGO_USER"]
    pwd  = os.environ["MONGO_PASSWORD"]
    host = os.environ.get("MONGO_HOST", "mongo")
    port = int(os.environ.get("MONGO_PORT", "27017"))
    db   = os.environ["MONGO_DB"]
    uri = f"mongodb://{user}:{pwd}@{host}:{port}/?authSource=admin"
    client = MongoClient(uri)
    return client, client[db]


def ensure_indexes(coll):
    coll.create_index([("patient_id", ASCENDING)], name="patient_id_1")
    coll.create_index([("date", DESCENDING)],      name="date_-1")
    coll.create_index([("diagnosis.primary.code_cim10", ASCENDING)],
                      name="diag_primary_cim10_1")


def ingest_consultations(coll, n: int, nb_patients: int, nb_medecins: int,
                         batch: int = 5000) -> int:
    """Génère et insère par lots. Note: les patient_id/medecin_id sont des refs
    logiques vers Postgres ; on les tire au hasard sans vérifier l'existence
    (la BDD documentaire ne valide pas les FK)."""
    import random
    total = 0
    buffer = []
    for i in range(n):
        pid = random.randint(1, max(nb_patients, 1))
        mid = random.randint(1, max(nb_medecins, 1))
        buffer.append(gen_consultation(pid, mid))
        if len(buffer) >= batch:
            coll.insert_many(buffer, ordered=False)
            total += len(buffer)
            buffer.clear()
    if buffer:
        coll.insert_many(buffer, ordered=False)
        total += len(buffer)
    return total


def main():
    n_consult    = int(os.environ.get("NB_CONSULTATIONS", "60000"))
    n_patients   = int(os.environ.get("NB_PATIENTS",      "5000"))
    n_medecins   = int(os.environ.get("NB_MEDECINS",      "100"))

    print(f"[MG] target: {n_consult} consultations "
          f"(pour {n_patients} patients × {n_medecins} médecins)", flush=True)

    client, db = connect()
    coll = db.consultations

    t_idx = time.perf_counter()
    ensure_indexes(coll)
    print(f"[MG] index prêts en {time.perf_counter()-t_idx:.2f}s", flush=True)

    t0 = time.perf_counter()
    inserted = ingest_consultations(coll, n_consult, n_patients, n_medecins)
    elapsed = time.perf_counter() - t0

    total = coll.count_documents({})
    rate = inserted / elapsed if elapsed > 0 else 0
    print(f"[MG] DONE: +{inserted} consultations en {elapsed:.2f}s "
          f"({rate:.0f} docs/s) - total collection = {total}", flush=True)

    client.close()
    return inserted


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[MG] ERROR: {e}", file=sys.stderr, flush=True)
        sys.exit(1)
