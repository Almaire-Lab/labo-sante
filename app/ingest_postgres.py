"""
Ingestion PostgreSQL — labo-sante
- Médecins, patients, médicaments (référentiels)
- Prescriptions + table de liaison N-N
Utilise execute_values pour des INSERT en bulk (~10-50x plus rapide qu'un par un).
Idempotent : ON CONFLICT DO NOTHING sur les colonnes UNIQUE.
"""
import os
import sys
import time
import psycopg2
from psycopg2.extras import execute_values

from generate_data import (
    gen_medecins, gen_patients, gen_medicaments,
    gen_prescriptions, gen_prescription_medicaments,
)


def connect():
    """Lit les variables d'env injectées par docker-compose."""
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "postgres"),
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        dbname=os.environ["POSTGRES_DB"],
    )


def ingest_medecins(cur, n: int) -> int:
    rows = gen_medecins(n)
    execute_values(
        cur,
        """INSERT INTO medecins (nom, prenom, specialite, email, telephone)
           VALUES %s
           ON CONFLICT (email) DO NOTHING""",
        rows, page_size=1000,
    )
    cur.execute("SELECT COUNT(*) FROM medecins")
    return cur.fetchone()[0]


def ingest_patients(cur, n: int, batch: int = 5000) -> int:
    rows = gen_patients(n)
    for i in range(0, len(rows), batch):
        execute_values(
            cur,
            """INSERT INTO patients (nom, prenom, date_naissance, sexe, email, telephone, adresse)
               VALUES %s
               ON CONFLICT (email) DO NOTHING""",
            rows[i:i + batch], page_size=1000,
        )
    cur.execute("SELECT COUNT(*) FROM patients")
    return cur.fetchone()[0]


def ingest_medicaments(cur) -> int:
    rows = gen_medicaments()
    execute_values(
        cur,
        """INSERT INTO medicaments (nom_commercial, dci, dosage, forme, laboratoire)
           VALUES %s
           ON CONFLICT (nom_commercial, dosage, forme) DO NOTHING""",
        rows,
    )
    cur.execute("SELECT COUNT(*) FROM medicaments")
    return cur.fetchone()[0]


def ingest_prescriptions(cur, n: int, nb_patients: int, nb_medecins: int,
                         nb_medicaments: int, batch: int = 5000) -> int:
    """Insère les prescriptions par lots, puis génère les lignes de liaison.
    Récupère les vrais IDs depuis la BDD (SERIAL peut être non contigu après ON CONFLICT)."""
    cur.execute("SELECT id FROM patients")
    patient_ids = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT id FROM medecins")
    medecin_ids = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT id FROM medicaments")
    medic_ids = [r[0] for r in cur.fetchall()]

    inserted = 0
    buffer = []
    import random
    from datetime import datetime, timedelta
    from faker import Faker
    fake = Faker("fr_FR")

    for _ in range(n):
        pid = random.choice(patient_ids)
        mid = random.choice(medecin_ids)
        days_ago = random.randint(0, 730)
        date_p = (datetime.now() - timedelta(days=days_ago)).date()
        notes = fake.sentence(nb_words=random.randint(4, 10))
        buffer.append((pid, mid, date_p, notes))
        if len(buffer) >= batch:
            inserted += _flush_prescriptions(cur, buffer, medic_ids)
            buffer.clear()
    if buffer:
        inserted += _flush_prescriptions(cur, buffer, medic_ids)
    return inserted


def _flush_prescriptions(cur, rows, medic_ids):
    """INSERT prescriptions + RETURNING id, puis INSERT lignes de liaison."""
    import random
    sql = """INSERT INTO prescriptions (patient_id, medecin_id, date_prescription, notes)
             VALUES %s RETURNING id"""
    execute_values(cur, sql, rows, page_size=1000)
    ids = [r[0] for r in cur.fetchall()]

    posologies = [
        "1 cp matin et soir", "1 cp 3x/jour pendant les repas",
        "2 cp au coucher", "1 sachet matin", "1 cp toutes les 6h si besoin",
    ]
    liaisons = []
    for pid in ids:
        nb = random.randint(1, 3)
        chosen = random.sample(medic_ids, min(nb, len(medic_ids)))
        for mid in chosen:
            liaisons.append((pid, mid, random.choice(posologies), random.randint(3, 30)))
    execute_values(
        cur,
        """INSERT INTO prescription_medicaments
               (prescription_id, medicament_id, posologie, duree_jours)
           VALUES %s
           ON CONFLICT (prescription_id, medicament_id) DO NOTHING""",
        liaisons, page_size=2000,
    )
    return len(ids)


def main():
    n_medecins   = int(os.environ.get("NB_MEDECINS",   "100"))
    n_patients   = int(os.environ.get("NB_PATIENTS",   "5000"))
    n_prescriptions = int(os.environ.get("NB_PRESCRIPTIONS", "60000"))

    print(f"[PG] target: {n_medecins} médecins, {n_patients} patients, "
          f"{n_prescriptions} prescriptions", flush=True)

    conn = connect()
    conn.autocommit = False
    cur = conn.cursor()

    t0 = time.perf_counter()
    n_med   = ingest_medecins(cur, n_medecins);            conn.commit()
    n_pat   = ingest_patients(cur, n_patients);            conn.commit()
    n_drug  = ingest_medicaments(cur);                     conn.commit()
    t_ref = time.perf_counter() - t0
    print(f"[PG] référentiels OK en {t_ref:.2f}s -> medecins={n_med}, "
          f"patients={n_pat}, medicaments={n_drug}", flush=True)

    t1 = time.perf_counter()
    n_resc = ingest_prescriptions(cur, n_prescriptions, n_pat, n_med, n_drug)
    conn.commit()
    t_resc = time.perf_counter() - t1

    cur.execute("SELECT COUNT(*) FROM prescriptions")
    total_resc = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM prescription_medicaments")
    total_lignes = cur.fetchone()[0]

    print(f"[PG] prescriptions OK en {t_resc:.2f}s -> +{n_resc} insérées "
          f"(total={total_resc}, lignes_medic={total_lignes})", flush=True)
    print(f"[PG] DONE en {(time.perf_counter()-t0):.2f}s", flush=True)

    cur.close(); conn.close()
    return total_resc


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[PG] ERROR: {e}", file=sys.stderr, flush=True)
        sys.exit(1)
