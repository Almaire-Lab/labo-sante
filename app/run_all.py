"""
Pipeline complet : Postgres puis Mongo, avec récap final.
Utilisé comme CMD par défaut dans le Dockerfile.
"""
import os
import sys
import time

from ingest_postgres import main as run_pg
from ingest_mongo import main as run_mg


def main():
    t0 = time.perf_counter()
    print("=" * 60, flush=True)
    print(" PIPELINE LABO-SANTÉ — Session 2", flush=True)
    print("=" * 60, flush=True)

    print("\n[1/2] Ingestion PostgreSQL...", flush=True)
    run_pg()

    print("\n[2/2] Ingestion MongoDB...", flush=True)
    run_mg()

    total = time.perf_counter() - t0
    print(f"\n{'='*60}\n PIPELINE TERMINÉ en {total:.2f}s\n{'='*60}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[PIPELINE] ERROR: {e}", file=sys.stderr, flush=True)
        sys.exit(1)
