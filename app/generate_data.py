"""
Génération de données synthétiques pour le Labo Santé.
Utilise Faker (FR) pour produire des noms, dates, adresses réalistes.
Toutes les données sont SYNTHÉTIQUES — aucune donnée personnelle réelle.
"""
import random
from datetime import datetime, timedelta, timezone
from faker import Faker

fake = Faker("fr_FR")
Faker.seed(42)
random.seed(42)

# -------- Référentiels statiques --------

SPECIALITES = [
    "Médecine générale", "Cardiologie", "Pédiatrie", "Dermatologie",
    "Ophtalmologie", "Gynécologie", "Neurologie", "Pneumologie",
    "Endocrinologie", "Rhumatologie",
]

# (nom_commercial, dci, dosage, forme, laboratoire)
MEDICAMENTS_BASE = [
    ("Doliprane",     "Paracétamol",        "500 mg", "comprimé",    "Sanofi"),
    ("Doliprane",     "Paracétamol",        "1000 mg","comprimé",    "Sanofi"),
    ("Efferalgan",    "Paracétamol",        "500 mg", "comprimé eff.","UPSA"),
    ("Aspegic",       "Acide acétylsalicylique","1000 mg","sachet",  "Sanofi"),
    ("Ibuprofène",    "Ibuprofène",         "400 mg", "comprimé",    "Mylan"),
    ("Amoxicilline",  "Amoxicilline",       "500 mg", "gélule",      "Biogaran"),
    ("Augmentin",     "Amoxicilline+Acide clavulanique","1 g","sachet","GSK"),
    ("Ventoline",     "Salbutamol",         "100 µg", "aérosol",     "GSK"),
    ("Spasfon",       "Phloroglucinol",     "80 mg",  "comprimé",    "Teva"),
    ("Smecta",        "Diosmectite",        "3 g",    "poudre",      "Ipsen"),
    ("Imodium",       "Lopéramide",         "2 mg",   "gélule",      "Janssen"),
    ("Levothyrox",    "Lévothyroxine",      "50 µg",  "comprimé",    "Merck"),
    ("Kardégic",      "Acide acétylsalicylique","75 mg","sachet",    "Sanofi"),
    ("Tahor",         "Atorvastatine",      "20 mg",  "comprimé",    "Pfizer"),
    ("Metformine",    "Metformine",         "500 mg", "comprimé",    "Biogaran"),
    ("Lansoprazole",  "Lansoprazole",       "15 mg",  "gélule",      "Mylan"),
    ("Inexium",       "Ésoméprazole",       "20 mg",  "comprimé",    "AstraZeneca"),
    ("Solupred",      "Prednisolone",       "20 mg",  "comprimé",    "Sanofi"),
    ("Xanax",         "Alprazolam",         "0,25 mg","comprimé",    "Pfizer"),
    ("Lexomil",       "Bromazépam",         "6 mg",   "comprimé",    "Roche"),
]

# Symptômes possibles, regroupés par "famille" pour avoir des consultations cohérentes
SYMPTOMS_POOL = [
    ("toux sèche",       {"duree_jours": (3, 21)}),
    ("toux grasse",      {"duree_jours": (3, 21)}),
    ("fièvre",           {"temperature_c": (37.8, 40.0)}),
    ("maux de tête",     {"intensite": ["legere", "moderee", "severe"]}),
    ("fatigue",          {"duree_jours": (1, 30)}),
    ("douleur abdominale",{"intensite": ["legere", "moderee", "severe"]}),
    ("nausées",          {}),
    ("vomissements",     {"nb_episodes": (1, 8)}),
    ("diarrhée",         {"duree_jours": (1, 7)}),
    ("éruption cutanée", {"localisation": ["bras", "torse", "jambes", "visage"]}),
    ("douleur thoracique",{"intensite": ["legere", "moderee", "severe"]}),
    ("essoufflement",    {"intensite": ["legere", "moderee", "severe"]}),
    ("vertiges",         {}),
    ("douleur articulaire",{"localisation": ["genou", "epaule", "coude", "poignet", "hanche"]}),
    ("anxiété",          {"intensite": ["legere", "moderee", "severe"]}),
]

# Diagnostics CIM-10 simplifiés
DIAGNOSES = [
    ("J20.9", "Bronchite aiguë"),
    ("J06.9", "Infection des voies respiratoires supérieures"),
    ("J11.1", "Grippe"),
    ("K59.1", "Diarrhée fonctionnelle"),
    ("K30",   "Dyspepsie"),
    ("R51",   "Céphalée"),
    ("G43.9", "Migraine"),
    ("M54.5", "Lombalgie"),
    ("L20.9", "Dermatite atopique"),
    ("F41.1", "Anxiété généralisée"),
    ("I10",   "Hypertension essentielle"),
    ("E11.9", "Diabète de type 2 sans complication"),
    ("J45.9", "Asthme"),
    ("N39.0", "Infection urinaire"),
    ("H10.9", "Conjonctivite"),
]

SEVERITIES = ["legere", "moderee", "severe"]

# ============ Générateurs ============

def gen_medecins(n: int):
    """Renvoie une liste de tuples prêts à INSERT."""
    rows = []
    for i in range(n):
        sex = random.choice(["M", "F"])
        nom = fake.last_name()
        prenom = fake.first_name_male() if sex == "M" else fake.first_name_female()
        specialite = random.choice(SPECIALITES)
        email = f"{prenom.lower()}.{nom.lower()}.{i}@labo.test"
        tel = fake.phone_number()
        rows.append((nom, prenom, specialite, email, tel))
    return rows


def gen_patients(n: int):
    rows = []
    for i in range(n):
        sex = random.choice(["M", "F", "X"])
        nom = fake.last_name()
        prenom = (
            fake.first_name_male() if sex == "M"
            else fake.first_name_female() if sex == "F"
            else fake.first_name()
        )
        naissance = fake.date_of_birth(minimum_age=0, maximum_age=95)
        email = f"{prenom.lower()}.{nom.lower()}.{i}@patient.test"
        tel = fake.phone_number()[:20]
        adresse = fake.address().replace("\n", ", ")
        rows.append((nom, prenom, naissance, sex, email, tel, adresse))
    return rows


def gen_medicaments():
    """Renvoie le référentiel statique (toujours le même)."""
    return list(MEDICAMENTS_BASE)


def gen_prescriptions(n: int, nb_patients: int, nb_medecins: int):
    """Yields des tuples (patient_id, medecin_id, date, notes) — IDs 1-indexés."""
    for _ in range(n):
        patient_id = random.randint(1, nb_patients)
        medecin_id = random.randint(1, nb_medecins)
        days_ago = random.randint(0, 730)
        date_p = (datetime.now() - timedelta(days=days_ago)).date()
        notes = fake.sentence(nb_words=random.randint(4, 10))
        yield (patient_id, medecin_id, date_p, notes)


def gen_prescription_medicaments(prescription_id: int, nb_medicaments: int):
    """Pour une prescription, renvoie 1..3 lignes (prescription_id, medic_id, posologie, duree)."""
    nb = random.randint(1, 3)
    medic_ids = random.sample(range(1, nb_medicaments + 1), nb)
    posologies = [
        "1 cp matin et soir", "1 cp 3x/jour pendant les repas",
        "2 cp au coucher", "1 sachet matin", "1 cp toutes les 6h si besoin",
    ]
    for mid in medic_ids:
        yield (prescription_id, mid, random.choice(posologies), random.randint(3, 30))


def gen_consultation(patient_id: int, medecin_id: int):
    """Renvoie UN document MongoDB."""
    nb_symptoms = random.randint(1, 4)
    chosen = random.sample(SYMPTOMS_POOL, nb_symptoms)
    symptoms = []
    for label, attrs in chosen:
        s = {"label": label}
        for key, val in attrs.items():
            if isinstance(val, tuple):
                if isinstance(val[0], float):
                    s[key] = round(random.uniform(*val), 1)
                else:
                    s[key] = random.randint(*val)
            elif isinstance(val, list):
                s[key] = random.choice(val)
        symptoms.append(s)

    code, label = random.choice(DIAGNOSES)
    secondary = []
    if random.random() < 0.3:
        c2, l2 = random.choice(DIAGNOSES)
        if c2 != code:
            secondary.append({"code_cim10": c2, "label": l2})

    days_ago = random.randint(0, 365)
    return {
        "patient_id": patient_id,
        "medecin_id": medecin_id,
        "date": datetime.now(timezone.utc) - timedelta(days=days_ago),
        "symptoms": symptoms,
        "diagnosis": {
            "primary":   {"code_cim10": code, "label": label},
            "secondary": secondary,
            "severity":  random.choice(SEVERITIES),
            "confidence": round(random.uniform(0.6, 0.99), 2),
        },
        "notes": fake.sentence(nb_words=random.randint(6, 15)),
    }
