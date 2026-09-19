"""
Balaji Medical - Database Model & Initialization
Handles SQLite schema creation, database connections, and catalog seeding.
"""

import sqlite3
import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "balaji_medical.db")

def get_db_connection():
    """Returns a database connection with dict-like row access."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db(force_reseed=False):
    """Initializes tables and seeds initial data if empty."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        icon TEXT NOT NULL,
        description TEXT
    );

    CREATE TABLE IF NOT EXISTS medicines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        generic_name TEXT NOT NULL,
        category_id INTEGER NOT NULL,
        manufacturer TEXT NOT NULL,
        dosage_form TEXT NOT NULL,
        strength TEXT,
        price REAL NOT NULL,
        discount_price REAL,
        stock_quantity INTEGER NOT NULL DEFAULT 0,
        batch_no TEXT,
        expiry_date TEXT NOT NULL,
        requires_prescription INTEGER DEFAULT 0,
        description TEXT,
        side_effects TEXT,
        usage_instructions TEXT,
        image_url TEXT,
        FOREIGN KEY (category_id) REFERENCES categories(id)
    );

    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'customer', -- 'customer' or 'pharmacist'
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS prescriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_name TEXT NOT NULL,
        patient_phone TEXT,
        doctor_name TEXT,
        filename TEXT NOT NULL,
        file_path TEXT NOT NULL,
        status TEXT DEFAULT 'Pending', -- 'Pending', 'Approved', 'Rejected'
        notes TEXT,
        uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_code TEXT UNIQUE NOT NULL,
        user_id INTEGER,
        customer_name TEXT NOT NULL,
        customer_phone TEXT NOT NULL,
        customer_email TEXT,
        delivery_address TEXT NOT NULL,
        subtotal REAL NOT NULL,
        delivery_fee REAL DEFAULT 0.0,
        discount REAL DEFAULT 0.0,
        total_amount REAL NOT NULL,
        payment_method TEXT NOT NULL,
        payment_status TEXT DEFAULT 'Pending', -- 'Paid', 'Pending'
        order_status TEXT DEFAULT 'Placed',   -- 'Placed', 'Processing', 'Dispatched', 'Delivered', 'Cancelled'
        prescription_id INTEGER,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (prescription_id) REFERENCES prescriptions(id)
    );

    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        medicine_id INTEGER NOT NULL,
        medicine_name TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        subtotal REAL NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(id),
        FOREIGN KEY (medicine_id) REFERENCES medicines(id)
    );
    """)
    conn.commit()

    # Migration for existing orders table
    try:
        cursor.execute("ALTER TABLE orders ADD COLUMN user_id INTEGER REFERENCES users(id)")
        conn.commit()
    except Exception:
        pass

    # Check if categories already exist
    cursor.execute("SELECT COUNT(*) FROM categories")
    cat_count = cursor.fetchone()[0]

    if cat_count == 0 or force_reseed:
        seed_data(cursor)
        conn.commit()

    conn.close()

def seed_data(cursor):
    """Seeds initial categories and comprehensive medicines list."""
    categories = [
        ("Pain Relief & Fever", "pain-relief", "flame", "Medicines for headaches, fevers, muscle pains, and inflammation"),
        ("Antibiotics & Anti-Infectives", "antibiotics", "shield-alert", "Broad-spectrum and targeted prescription antibiotics"),
        ("Diabetes & Metabolic Care", "diabetes", "activity", "Insulin, oral hypoglycemic tablets, and glucose monitors"),
        ("Cardiac & Blood Pressure", "cardiac", "heart-pulse", "Antihypertensives, cholesterol reducers, and cardiac care"),
        ("Respiratory & Cold Care", "respiratory", "wind", "Cough syrups, bronchodilators, antihistamines, and nasal sprays"),
        ("Gastrointestinal & Digestion", "gastro", "sparkles", "Antacids, proton pump inhibitors, and gut health care"),
        ("Skin Care & Antiseptics", "skincare", "bandage", "Antiseptic solutions, medicated ointments, and healing powders"),
        ("Vitamins & Health Devices", "wellness-devices", "pill", "Daily supplements, immunity boosters, and diagnostic devices")
    ]

    cursor.executemany(
        "INSERT OR IGNORE INTO categories (name, slug, icon, description) VALUES (?, ?, ?, ?)",
        categories
    )

    # Fetch category id map
    cursor.execute("SELECT slug, id FROM categories")
    cat_map = dict(cursor.fetchall())

    # Generate realistic dates
    today = datetime.now()
    exp_2027 = (today + timedelta(days=450)).strftime("%Y-%m-%d")
    exp_2028 = (today + timedelta(days=720)).strftime("%Y-%m-%d")
    exp_2029 = (today + timedelta(days=1080)).strftime("%Y-%m-%d")
    exp_near = (today + timedelta(days=45)).strftime("%Y-%m-%d") # Near expiry alert item

    medicines = [
        # Pain Relief & Fever
        ("Dolo 650 Tablet", "Paracetamol", cat_map["pain-relief"], "Micro Labs Ltd", "Tablet", "650mg",
         34.00, 30.50, 150, "DL-8821", exp_2027, 0,
         "Fast-acting paracetamol for high fever, mild to moderate body pain, headache, and dental pain.",
         "Mild nausea in rare cases, liver toxicity if overdosed.",
         "1 tablet every 6 hours as needed or as prescribed. Do not exceed 4g in 24 hours.",
         "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=300"),

        ("Crocin Advance 500mg", "Paracetamol (Fast Release)", cat_map["pain-relief"], "GlaxoSmithKline", "Tablet", "500mg",
         28.00, 25.00, 120, "CR-4190", exp_2027, 0,
         "Optizorb technology for rapid fever reduction and headache relief within 15 minutes.",
         "Rare allergic rash, mild epigastric discomfort.",
         "1-2 tablets 3 times daily after meals. Maximum 8 tablets per day.",
         "https://images.unsplash.com/photo-1584017911766-d451b3d0e843?w=300"),

        ("Combiflam Tablet", "Ibuprofen + Paracetamol", cat_map["pain-relief"], "Sanofi India", "Tablet", "400mg + 325mg",
         48.00, 42.00, 95, "CB-9022", exp_2027, 0,
         "Dual-action anti-inflammatory pain reliever for joint pain, toothache, and sprains.",
         "Acidity, heartburn, mild stomach upset.",
         "Take 1 tablet strictly after food. Not recommended on an empty stomach.",
         "https://images.unsplash.com/photo-1471864190281-a93a3070b6de?w=300"),

        ("Meftal-Spas Tablet", "Mefenamic Acid + Dicyclomine", cat_map["pain-relief"], "Blue Cross Labs", "Tablet", "250mg + 10mg",
         55.00, 49.00, 80, "MF-3310", exp_2027, 1,
         "Antispasmodic medication specifically formulated for abdominal cramps and menstrual pain.",
         "Dry mouth, drowsiness, blurred vision.",
         "Take 1 tablet with a glass of water during spasmodic episodes. Rx required.",
         "https://images.unsplash.com/photo-1550572017-edd951aa8f72?w=300"),

        ("Ultracet Tablet", "Tramadol Hydrochloride + Paracetamol", cat_map["pain-relief"], "Janssen / J&J", "Tablet", "37.5mg + 325mg",
         220.00, 195.00, 35, "UL-1120", exp_2027, 1,
         "Potent combination opioid analgesic for severe postoperative and acute traumatic pain.",
         "Drowsiness, dizziness, constipation, nausea.",
         "Strictly prescription only. Take as directed by registered medical practitioner.",
         "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=300"),

        # Antibiotics & Anti-Infectives
        ("Augmentin 625 Duo", "Amoxicillin + Potassium Clavulanate", cat_map["antibiotics"], "GlaxoSmithKline", "Tablet", "500mg + 125mg",
         205.00, 185.00, 60, "AG-7711", exp_2027, 1,
         "Potent broad-spectrum antibiotic combating bacterial infections of lungs, sinuses, urinary tract, and ear.",
         "Diarrhea, loose stools, nausea, skin rash.",
         "1 tablet twice daily with food for 5-7 days. Complete the entire course.",
         "https://images.unsplash.com/photo-1587854692152-cbe660dbde88?w=300"),

        ("Azithral 500mg", "Azithromycin", cat_map["antibiotics"], "Alembic Pharma", "Tablet", "500mg",
         132.00, 118.00, 75, "AZ-5044", exp_2027, 1,
         "Macrolide antibiotic treating respiratory tract infections, throat tonsillitis, and typhoid.",
         "Abdominal pain, nausea, loose stools.",
         "1 tablet daily 1 hour before or 2 hours after food for 3 consecutive days.",
         "https://images.unsplash.com/photo-1584017911766-d451b3d0e843?w=300"),

        ("Cifran 500 Tablet", "Ciprofloxacin", cat_map["antibiotics"], "Sun Pharma", "Tablet", "500mg",
         95.00, 85.00, 50, "CF-2289", exp_2027, 1,
         "Fluoroquinolone antibiotic for urinary tract infections, bacterial diarrhea, and skin infections.",
         "Mild dizziness, nausea, sun sensitivity.",
         "1 tablet twice daily with plenty of water. Avoid taking with antacids or dairy.",
         "https://images.unsplash.com/photo-1550572017-edd951aa8f72?w=300"),

        ("Taxim-O 200 Tablet", "Cefixime", cat_map["antibiotics"], "Alkem Laboratories", "Tablet", "200mg",
         110.00, 98.00, 45, "TX-6612", exp_2027, 1,
         "Third-generation cephalosporin antibiotic for typhoid fever, bronchitis, and gonococcal infections.",
         "Mild stomach cramps, dyspepsia.",
         "1 tablet twice daily for the duration prescribed by the doctor.",
         "https://images.unsplash.com/photo-1587854692152-cbe660dbde88?w=300"),

        ("Mox 500 Capsule", "Amoxicillin Trihydrate", cat_map["antibiotics"], "Ranbaxy / Sun Pharma", "Capsule", "500mg",
         82.00, 72.00, 9, "MX-1090", exp_near, 1, # Low stock + Near expiry sample
         "Standard penicillin antibiotic for throat, dental abscesses, and chest infections.",
         "Mild rash, gastric discomfort.",
         "Take 1 capsule thrice daily as directed by doctor.",
         "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=300"),

        # Diabetes & Metabolic Care
        ("Glycomet-GP 1/850", "Metformin + Glimepiride", cat_map["diabetes"], "USV Pvt Ltd", "Tablet", "850mg + 1mg",
         145.00, 130.00, 85, "GM-4401", exp_2028, 1,
         "Dual oral hypoglycemic agent for effective glycaemic control in Type 2 Diabetes Mellitus.",
         "Hypoglycemia (sweating, tremors), metallic taste, upset stomach.",
         "Take 1 tablet once daily with the first main meal (breakfast).",
         "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=300"),

        ("Januvia 100mg", "Sitagliptin", cat_map["diabetes"], "MSD Pharmaceuticals", "Tablet", "100mg",
         580.00, 520.00, 40, "JN-9921", exp_2028, 1,
         "DPP-4 inhibitor that helps regulate insulin levels after meals with minimal hypoglycemic risk.",
         "Upper respiratory tract discomfort, headache, joint discomfort.",
         "1 tablet once daily, with or without food at the same time each day.",
         "https://images.unsplash.com/photo-1471864190281-a93a3070b6de?w=300"),

        ("Accu-Chek Active Glucose Meter Kit", "Blood Glucose Diagnostic Device", cat_map["diabetes"], "Roche Diabetes Care", "Device", "Kit",
         1499.00, 1299.00, 25, "AC-0102", exp_2028, 0,
         "Accurate blood sugar monitoring meter with 10 test strips, lancing device, and lancets.",
         "None (Medical Diagnostic Hardware).",
         "Wash hands, apply tiny blood droplet (1-2 microliter) to test strip. Result in 5 seconds.",
         "https://images.unsplash.com/photo-1631549916768-4119b2e5f926?w=300"),

        ("Accu-Chek Active 50 Test Strips", "Diagnostic Reagent Strips", cat_map["diabetes"], "Roche Diabetes Care", "Strips", "50 Strips",
         995.00, 890.00, 70, "AS-8812", exp_2027, 0,
         "Original test strips compatible with Accu-Chek Active meters for frequent glucose monitoring.",
         "None.",
         "Keep bottle tightly closed, store away from direct heat and moisture.",
         "https://images.unsplash.com/photo-1631549916768-4119b2e5f926?w=300"),

        ("Lantus 100IU/ml SoloStar Pen", "Insulin Glargine (Long Acting)", cat_map["diabetes"], "Sanofi Healthcare", "Injection", "3ml Cartridge",
         780.00, 715.00, 18, "LT-3045", exp_2027, 1,
         "Once-daily basal insulin analog providing continuous 24-hour baseline glucose control.",
         "Hypoglycemia, injection site redness or lipodystrophy.",
         "Subcutaneous injection once daily at bedtime. Keep refrigerated at 2°C to 8°C.",
         "https://images.unsplash.com/photo-1579684385127-1ef15d508118?w=300"),

        # Cardiac & Blood Pressure
        ("Telma 40 Tablet", "Telmisartan", cat_map["cardiac"], "Glenmark Pharma", "Tablet", "40mg",
         125.00, 112.00, 110, "TM-4011", exp_2028, 1,
         "Angiotensin Receptor Blocker (ARB) for controlling essential hypertension and cardiovascular risk.",
         "Dizziness, lightheadedness when standing up quickly, hyperkalemia.",
         "Take 1 tablet every morning regularly at the exact same hour.",
         "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=300"),

        ("Amlong 5mg Tablet", "Amlodipine Besylate", cat_map["cardiac"], "Micro Labs Ltd", "Tablet", "5mg",
         45.00, 39.00, 90, "AL-5502", exp_2028, 1,
         "Calcium channel blocker for lowering elevated blood pressure and preventing angina episodes.",
         "Swelling of ankles or feet (edema), flushing, fatigue.",
         "1 tablet daily, preferably in the morning. Do not skip doses.",
         "https://images.unsplash.com/photo-1584017911766-d451b3d0e843?w=300"),

        ("Atorva 20 Tablet", "Atorvastatin Calcium", cat_map["cardiac"], "Zydus Cadila", "Tablet", "20mg",
         185.00, 160.00, 65, "AT-2009", exp_2027, 1,
         "Statin medication that lowers LDL (bad) cholesterol and triglycerides while elevating HDL.",
         "Muscle ache, mild liver enzyme changes, indigestion.",
         "Take 1 tablet at night after dinner. Avoid consuming grapefruit juice.",
         "https://images.unsplash.com/photo-1471864190281-a93a3070b6de?w=300"),

        ("Ecosprin 75 Tablet", "Aspirin (Enteric Coated)", cat_map["cardiac"], "USV Pvt Ltd", "Tablet", "75mg",
         12.00, 10.50, 140, "EC-7512", exp_2028, 1,
         "Antiplatelet blood thinner preventing clot formation, recurrent heart attacks, and ischemic strokes.",
         "Mild stomach burning, increased bleeding tendency.",
         "Swallow whole after meals with water. Do not crush or chew enteric coated tablets.",
         "https://images.unsplash.com/photo-1550572017-edd951aa8f72?w=300"),

        ("Concor 5 Tablet", "Bisoprolol Fumarate", cat_map["cardiac"], "Merck Ltd", "Tablet", "5mg",
         115.00, 102.00, 48, "CN-5012", exp_2027, 1,
         "Selective Beta-1 blocker for slowing heart rate, reducing high blood pressure, and heart failure.",
         "Bradycardia, cold extremities, dizziness.",
         "Take 1 tablet every morning. Never discontinue suddenly without consulting cardiologist.",
         "https://images.unsplash.com/photo-1587854692152-cbe660dbde88?w=300"),

        # Respiratory & Cold Care
        ("Ascoril-D Plus Cough Syrup", "Dextromethorphan + Chlorpheniramine + Phenylephrine", cat_map["respiratory"], "Glenmark Pharma", "Syrup", "100ml",
         130.00, 115.00, 55, "AS-1022", exp_2027, 0,
         "Soothing non-drowsy cough syrup for dry irritating cough, throat tickle, and nasal congestion.",
         "Mild drowsiness, dry mouth, blurred vision.",
         "Adults: 10ml (2 teaspoons) 3 times a day using measuring cup provided.",
         "https://images.unsplash.com/photo-1512069772995-ec65ed45afd6?w=300"),

        ("Montair-LC Tablet", "Montelukast + Levocetirizine", cat_map["respiratory"], "Cipla Ltd", "Tablet", "10mg + 5mg",
         195.00, 175.00, 85, "MT-9912", exp_2027, 1,
         "Dual anti-allergic medication for allergic rhinitis, sneezing, watery eyes, and asthmatic wheezing.",
         "Sleepiness, mild fatigue, dry mouth, vivid dreams.",
         "1 tablet once daily strictly at bedtime with a glass of water.",
         "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=300"),

        ("Allegra 120mg Tablet", "Fexofenadine Hydrochloride", cat_map["respiratory"], "Sanofi India", "Tablet", "120mg",
         140.00, 125.00, 70, "AL-1200", exp_2027, 0,
         "Non-sedating second generation antihistamine for seasonal hay fever, hives, and chronic sneezing.",
         "Mild headache, drowsiness in rare cases.",
         "1 tablet once daily with water before meals. Do not take with fruit juice.",
         "https://images.unsplash.com/photo-1584017911766-d451b3d0e843?w=300"),

        ("Asthalin 100mcg Inhaler", "Salbutamol (Albuterol)", cat_map["respiratory"], "Cipla Ltd", "Inhaler", "200 Metered Doses",
         165.00, 148.00, 30, "AS-2001", exp_2027, 1,
         "Fast-acting bronchodilator rescue inhaler providing instant relief from asthma attacks and bronchospasm.",
         "Tremor in fingers, mild palpitation, nervousness.",
         "1 to 2 puffs inhaled when sudden breathlessness occurs. Rinse mouth after inhalation.",
         "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=300"),

        ("Otrivin Oxy Fast Relief Nasal Spray", "Oxymetazoline HCl 0.05%", cat_map["respiratory"], "GSK Consumer Healthcare", "Nasal Spray", "10ml",
         98.00, 89.00, 60, "OT-0511", exp_2027, 0,
         "Fast acting decongestant that clears blocked nose and sinus congestion within 25 seconds for up to 12 hours.",
         "Local nasal stinging, dryness, rebound congestion if overused.",
         "1 spray into each nostril 2-3 times daily. Do not exceed 5 consecutive days of continuous usage.",
         "https://images.unsplash.com/photo-1512069772995-ec65ed45afd6?w=300"),

        # Gastrointestinal & Digestion
        ("Pan-D Capsule", "Pantoprazole + Domperidone", cat_map["gastro"], "Alkem Laboratories", "Capsule", "40mg + 30mg SR",
         185.00, 162.00, 100, "PD-4030", exp_2027, 1,
         "Sustained-release capsule for severe acid reflux (GERD), nausea, heartburn, and peptic ulcers.",
         "Headache, mild dry mouth, abdominal discomfort.",
         "Take 1 capsule first thing in the morning 30 minutes before breakfast with plain water.",
         "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=300"),

        ("Pantocid 40 Tablet", "Pantoprazole Sodium", cat_map["gastro"], "Sun Pharma", "Tablet", "40mg",
         140.00, 122.00, 115, "PC-4010", exp_2028, 1,
         "Proton pump inhibitor that significantly lowers stomach acid secretion and heals gastric erosion.",
         "Flatulence, joint pain, mild diarrhea.",
         "Take 1 tablet daily before morning breakfast. Swallow whole.",
         "https://images.unsplash.com/photo-1471864190281-a93a3070b6de?w=300"),

        ("Gelusil MPS Antacid Liquid", "Aluminium Hydroxide + Magnesium + Simethicone", cat_map["gastro"], "Pfizer India", "Liquid", "200ml",
         135.00, 119.00, 45, "GL-2001", exp_2027, 0,
         "Mint flavoured antacid liquid offering rapid soothing relief from acidity, gas bloating, and stomach burn.",
         "Mild laxative or constipating effect if taken in huge quantities.",
         "Shake bottle well. Take 1-2 teaspoonfuls (5-10ml) after meals or at bedtime.",
         "https://images.unsplash.com/photo-1512069772995-ec65ed45afd6?w=300"),

        ("Digene Chewable Tablets (Mint)", "Magnesium & Aluminium Hydroxide", cat_map["gastro"], "Abbott India", "Chewable Tablet", "Strip of 15",
         25.00, 22.00, 130, "DG-1502", exp_2027, 0,
         "Convenient pocket chewable antacids neutralizing gastric acid on demand.",
         "Chalky taste, loose stool in rare cases.",
         "Chew 1 to 2 tablets thoroughly after heavy or spicy meals.",
         "https://images.unsplash.com/photo-1550572017-edd951aa8f72?w=300"),

        # Skin Care & Antiseptics
        ("Betadine 10% Microbicidal Ointment", "Povidone-Iodine", cat_map["skincare"], "Win-Medicare / Mundipharma", "Ointment", "20g",
         95.00, 85.00, 80, "BT-1020", exp_2027, 0,
         "Broad-spectrum microbicidal topical ointment preventing infection in cuts, wounds, abrasions, and burns.",
         "Local irritation, transient skin staining (washes off with water).",
         "Clean wound, apply small amount directly or with sterile gauze 2-3 times daily.",
         "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=300"),

        ("Dettol Antiseptic Disinfectant Liquid", "Chloroxylenol (4.8% w/v)", cat_map["skincare"], "Reckitt Benckiser", "Liquid", "250ml",
         110.00, 99.00, 90, "DT-2500", exp_2028, 0,
         "Trusted antiseptic liquid for first aid wound cleansing, antiseptic bathing, and surface disinfection.",
         "Mild stinging sensation if applied concentrated.",
         "Dilute 1 tablespoon in 250ml clean water before applying to cuts or wounds.",
         "https://images.unsplash.com/photo-1584744982491-665216d95f8b?w=300"),

        ("Soframycin Skin Cream", "Framycetin Sulfate 1%", cat_map["skincare"], "Sanofi India", "Cream", "30g",
         58.00, 52.00, 65, "SF-3001", exp_2027, 0,
         "Topical antibacterial cream for superficial skin infections, infected cuts, ulcers, and minor burns.",
         "Local hypersensitivity, itching.",
         "Apply gently on infected skin area 1 to 3 times daily.",
         "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=300"),

        ("Candid Dusting Powder", "Clotrimazole 1%", cat_map["skincare"], "Glenmark Pharma", "Powder", "100g",
         135.00, 120.00, 70, "CD-1002", exp_2027, 0,
         "Antifungal dusting powder preventing and curing fungal infections like athlete's foot, jock itch, and sweat rash.",
         "Mild burning sensation, skin dryness.",
         "Dust generously over clean, dry affected area twice daily, especially after bathing.",
         "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=300"),

        # Vitamins & Health Devices
        ("Becosules Z Capsules", "Vitamin B-Complex + Vitamin C + Zinc", cat_map["wellness-devices"], "Pfizer India", "Capsule", "Strip of 20",
         52.00, 46.00, 110, "BC-2001", exp_2027, 0,
         "Essential therapeutic multivitamin boosting cellular energy, curing mouth ulcers, and strengthening immunity.",
         "Bright yellow urine discoloration (harmless vitamin B2 effect).",
         "1 capsule daily after any main meal with water.",
         "https://images.unsplash.com/photo-1577401239170-897942555fb3?w=300"),

        ("Shelcal 500 Tablet", "Calcium 500mg + Vitamin D3 250IU", cat_map["wellness-devices"], "Torrent Pharma", "Tablet", "Strip of 15",
         128.00, 112.00, 85, "SH-5001", exp_2028, 0,
         "Formulated calcium with active vitamin D3 to enhance bone density, prevent osteoporosis and joint weakness.",
         "Mild constipation, bloating if water intake is low.",
         "Take 1 tablet daily after lunch or dinner with ample water.",
         "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=300"),

        ("Neurobion Forte Tablet", "Vitamin B1 + B6 + B12", cat_map["wellness-devices"], "Procter & Gamble Health", "Tablet", "Strip of 30",
         38.00, 34.00, 120, "NB-3001", exp_2028, 0,
         "Nerve rejuvenation formula relieving peripheral neuropathy, tingling numbness in hands and feet.",
         "Rare flushing, slight sweating.",
         "1 tablet daily after food.",
         "https://images.unsplash.com/photo-1584017911766-d451b3d0e843?w=300"),

        ("OMRON HEM-7120 Digital BP Monitor", "Automatic Upper Arm Blood Pressure Monitor", cat_map["wellness-devices"], "Omron Healthcare", "Device", "Unit",
         2340.00, 1899.00, 15, "OM-7120", exp_2029, 0,
         "Clinically validated Japanese digital blood pressure monitor with Intellisense technology and hypertension alert.",
         "None (Medical Hardware Device).",
         "Wrap cuff around upper arm at heart level, rest comfortably for 5 minutes, press Start.",
         "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=300"),

        ("Fingertip Pulse Oximeter", "SpO2 & Pulse Rate Digital Monitor", cat_map["wellness-devices"], "Dr. Trust / MediTech", "Device", "Unit",
         1150.00, 799.00, 22, "PO-1080", exp_2029, 0,
         "High-accuracy dual OLED color display monitor measuring oxygen saturation (SpO2) and heart rate in 8 seconds.",
         "None.",
         "Insert index finger into rubber chamber, keep hand stationary, view readouts immediately.",
         "https://images.unsplash.com/photo-1584515933487-779824d29309?w=300"),

        # Multi-Company Brands: In-Stock vs Out-of-Stock Alternatives
        ("Calpol 650 Tablet", "Paracetamol", cat_map["pain-relief"], "GlaxoSmithKline", "Tablet", "650mg",
         33.00, 29.00, 95, "CP-6522", exp_2028, 0,
         "Proven antipyretic and analgesic for body aches, toothache, and fever. Trusted formula from GSK.",
         "Rare allergic reactions, mild nausea.",
         "1 tablet every 6 to 8 hours after food.",
         "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=300"),

        ("Pacimol 650 Tablet", "Paracetamol", cat_map["pain-relief"], "IPCA Laboratories", "Tablet", "650mg",
         31.00, 26.50, 0, "PC-9011", exp_2027, 0, # OUT OF STOCK
         "Paracetamol formulation by IPCA for quick pain and fever relief.",
         "Mild nausea in rare cases.",
         "Take as advised by doctor. (Currently out of stock - see Calpol or Dolo as alternate).",
         "https://images.unsplash.com/photo-1584017911766-d451b3d0e843?w=300"),

        ("Moxikind-CV 625", "Amoxicillin + Potassium Clavulanate", cat_map["antibiotics"], "Mankind Pharma", "Tablet", "500mg + 125mg",
         185.00, 160.00, 50, "MK-6251", exp_2027, 1,
         "High efficacy broad-spectrum penicillin combination by Mankind Pharma combating resistant bacterial infections.",
         "Diarrhea, nausea, stomach ache.",
         "1 tablet twice daily with food. Complete entire antibiotic course.",
         "https://images.unsplash.com/photo-1587854692152-cbe660dbde88?w=300"),

        ("Clavam 625 Tablet", "Amoxicillin + Potassium Clavulanate", cat_map["antibiotics"], "Alkem Laboratories", "Tablet", "500mg + 125mg",
         190.00, 168.00, 42, "CL-6202", exp_2027, 1,
         "Antibiotic formulated by Alkem Laboratories for respiratory, ear, and sinus bacterial infections.",
         "Mild stomach upset, loose stool.",
         "1 tablet twice daily with meals as prescribed.",
         "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=300"),

        ("Megapen-CV 625", "Amoxicillin + Potassium Clavulanate", cat_map["antibiotics"], "Aristo Pharmaceuticals", "Tablet", "625mg",
         178.00, 155.00, 0, "MP-6200", exp_2027, 1, # OUT OF STOCK
         "Penicillin antibiotic combination for severe infections. Out of stock.",
         "Stomach cramps, loose stools.",
         "Take strictly as prescribed. (Out of stock - see Augmentin or Moxikind-CV).",
         "https://images.unsplash.com/photo-1587854692152-cbe660dbde88?w=300"),

        ("Azee 500 Tablet", "Azithromycin", cat_map["antibiotics"], "Cipla Ltd", "Tablet", "500mg",
         130.00, 115.00, 85, "AZ-5001", exp_2028, 1,
         "Trusted macrolide antibiotic from Cipla for throat infections, chest congestion, and tonsillitis.",
         "Loose motions, nausea, abdominal cramps.",
         "1 tablet once daily 1 hour before meal for 3 days.",
         "https://images.unsplash.com/photo-1584017911766-d451b3d0e843?w=300"),

        ("Zady 500 Tablet", "Azithromycin", cat_map["antibiotics"], "Mankind Pharma", "Tablet", "500mg",
         120.00, 105.00, 40, "ZD-5009", exp_2027, 1,
         "Azithromycin formulation from Mankind Pharma.",
         "Mild abdominal distress.",
         "1 tablet daily for 3 days or as directed.",
         "https://images.unsplash.com/photo-1587854692152-cbe660dbde88?w=300"),

        ("Zithrox 500 Tablet", "Azithromycin", cat_map["antibiotics"], "Macleods Pharmaceuticals", "Tablet", "500mg",
         125.00, 110.00, 0, "ZX-5088", exp_2027, 1, # OUT OF STOCK
         "Macrolide antibiotic for upper and lower respiratory tract infections. Out of stock.",
         "Nausea, mild dizziness.",
         "Take as advised. (Out of stock - see Azee 500 or Azithral 500 as alternate).",
         "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=300"),

        ("Pantocid-DSR Capsule", "Pantoprazole + Domperidone", cat_map["gastro"], "Sun Pharma", "Capsule", "40mg + 30mg SR",
         180.00, 158.00, 65, "PT-4022", exp_2028, 1,
         "Sustained release anti-reflux capsule from Sun Pharma controlling severe acidity and gastric reflux.",
         "Headache, mild dry mouth.",
         "1 capsule daily early morning on an empty stomach.",
         "https://images.unsplash.com/photo-1471864190281-a93a3070b6de?w=300"),

        ("Pantosec-D Capsule", "Pantoprazole + Domperidone", cat_map["gastro"], "Cipla Ltd", "Capsule", "40mg + 30mg",
         175.00, 152.00, 0, "PS-4001", exp_2027, 1, # OUT OF STOCK
         "Acidity and GERD management capsule by Cipla. Currently out of stock.",
         "Mild bloating, dry mouth.",
         "Take 30 mins before breakfast. (Out of stock - see Pan-D or Pantocid-DSR).",
         "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=300"),

        ("Pantodac 40 Tablet", "Pantoprazole Sodium", cat_map["gastro"], "Zydus Lifesciences", "Tablet", "40mg",
         135.00, 118.00, 0, "PD-4011", exp_2027, 1, # OUT OF STOCK
         "Proton pump inhibitor by Zydus for gastric ulcer healing. Out of stock.",
         "Mild flatulence.",
         "1 tablet daily before breakfast. (Out of stock - see Pantocid 40 as alternate).",
         "https://images.unsplash.com/photo-1471864190281-a93a3070b6de?w=300"),

        ("Telmikind 40 Tablet", "Telmisartan", cat_map["cardiac"], "Mankind Pharma", "Tablet", "40mg",
         75.00, 62.00, 95, "TK-4020", exp_2028, 1,
         "Cost-effective blood pressure management tablet by Mankind Pharma.",
         "Mild dizziness on rising.",
         "1 tablet daily morning.",
         "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=300"),

        ("Cresar 40 Tablet", "Telmisartan", cat_map["cardiac"], "Cipla Ltd", "Tablet", "40mg",
         110.00, 95.00, 60, "CR-4001", exp_2028, 1,
         "Antihypertensive formulation from Cipla for chronic blood pressure regulation.",
         "Lightheadedness, fatigue.",
         "1 tablet daily at fixed morning time.",
         "https://images.unsplash.com/photo-1584017911766-d451b3d0e843?w=300"),

        ("Telvas 40 Tablet", "Telmisartan", cat_map["cardiac"], "Aristo Pharmaceuticals", "Tablet", "40mg",
         85.00, 72.00, 0, "TV-4011", exp_2027, 1, # OUT OF STOCK
         "Aristo's telmisartan formulation for high BP. Currently out of stock.",
         "Dizziness.",
         "Take as advised. (Out of stock - see Telma 40 or Telmikind 40).",
         "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=300"),

        ("Storvas 20 Tablet", "Atorvastatin Calcium", cat_map["cardiac"], "Sun Pharma", "Tablet", "20mg",
         170.00, 145.00, 55, "SV-2012", exp_2028, 1,
         "Trusted statin by Sun Pharma for cholesterol reduction and cardiovascular prevention.",
         "Muscle ache, mild dyspepsia.",
         "1 tablet at night after food.",
         "https://images.unsplash.com/photo-1471864190281-a93a3070b6de?w=300"),

        ("Lipitor 20 Tablet", "Atorvastatin Calcium", cat_map["cardiac"], "Viatris / Pfizer", "Tablet", "20mg",
         380.00, 340.00, 0, "LP-2001", exp_2027, 1, # OUT OF STOCK
         "Original innovator brand of Atorvastatin by Pfizer/Viatris. Currently out of stock.",
         "Muscle tenderness.",
         "Take at night. (Out of stock - see Atorva 20 or Storvas 20 for identical salt).",
         "https://images.unsplash.com/photo-1471864190281-a93a3070b6de?w=300"),

        ("Atocor 10 Tablet", "Atorvastatin Calcium", cat_map["cardiac"], "Dr. Reddy's Laboratories", "Tablet", "10mg",
         95.00, 82.00, 70, "AC-1002", exp_2028, 1,
         "Lipid-lowering statin from Dr. Reddy's Laboratories for optimal cardiac health.",
         "Mild indigestion, headache.",
         "1 tablet daily after evening meal.",
         "https://images.unsplash.com/photo-1471864190281-a93a3070b6de?w=300"),

        ("Obimet 500 SR", "Metformin Hydrochloride", cat_map["diabetes"], "Abbott India", "Tablet", "500mg SR",
         45.00, 38.00, 90, "OB-5001", exp_2028, 1,
         "Sustained-release metformin from Abbott India for first-line Type 2 Diabetes management.",
         "Metallic taste, mild stomach bloating.",
         "Take 1 tablet with dinner.",
         "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=300"),

        ("Gluconorm-G 1 Tablet", "Metformin + Glimepiride", cat_map["diabetes"], "Lupin Ltd", "Tablet", "500mg + 1mg",
         115.00, 99.00, 65, "GG-1022", exp_2028, 1,
         "Combination oral antidiabetic therapy by Lupin Ltd.",
         "Hypoglycemic episodes if meal skipped.",
         "1 tablet with morning breakfast.",
         "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=300"),

        ("Cetapin XR 500", "Metformin Hydrochloride", cat_map["diabetes"], "Sanofi India", "Tablet", "500mg XR",
         52.00, 45.00, 0, "CT-5001", exp_2027, 1, # OUT OF STOCK
         "Extended release metformin by Sanofi. Out of stock.",
         "Nausea, mild diarrhea.",
         "Take with meal. (Out of stock - see Obimet 500 or Glycomet).",
         "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=300"),

        ("Telekast-L Tablet", "Montelukast + Levocetirizine", cat_map["respiratory"], "Lupin Ltd", "Tablet", "10mg + 5mg",
         175.00, 155.00, 50, "TL-9901", exp_2028, 1,
         "Allergy and asthma symptom reliever formulated by Lupin Ltd.",
         "Drowsiness, fatigue.",
         "1 tablet at bedtime.",
         "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=300"),

        ("Montek-LC Tablet", "Montelukast + Levocetirizine", cat_map["respiratory"], "Sun Pharma", "Tablet", "10mg + 5mg",
         185.00, 162.00, 0, "ML-1002", exp_2027, 1, # OUT OF STOCK
         "Allergy tablet from Sun Pharma. Currently out of stock.",
         "Sleepiness, dry mouth.",
         "Take at night. (Out of stock - see Montair-LC or Telekast-L as alternate).",
         "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=300"),

        ("Foracort 200 Synchrobreathe Inhaler", "Formoterol + Budesonide", cat_map["respiratory"], "Cipla Ltd", "Inhaler", "120 MDI",
         420.00, 375.00, 35, "FC-2001", exp_2027, 1,
         "Breath-actuated dual controller inhaler by Cipla for chronic asthma and COPD maintenance.",
         "Throat irritation, hoarseness of voice.",
         "1 to 2 puffs inhaled twice daily. Always rinse mouth thoroughly with water after use.",
         "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=300"),

        ("Budecort 200 Inhaler", "Budesonide", cat_map["respiratory"], "Cipla Ltd", "Inhaler", "200 Doses",
         280.00, 245.00, 0, "BD-2001", exp_2027, 1, # OUT OF STOCK
         "Corticosteroid preventive inhaler from Cipla. Currently out of stock.",
         "Oral candidiasis, cough.",
         "Use regularly as prescribed. (Out of stock - see Foracort or Asthalin).",
         "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=300"),

        ("Maxiflo 250 Inhaler", "Fluticasone + Formoterol", cat_map["respiratory"], "Lupin Ltd", "Inhaler", "120 Doses",
         450.00, 395.00, 0, "MF-2501", exp_2027, 1, # OUT OF STOCK
         "Asthma controller inhaler by Lupin Ltd. Out of stock.",
         "Headache, throat tickle.",
         "Inhale twice daily. (Out of stock - see Foracort 200).",
         "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=300"),

        ("Cipcal 500 Tablet", "Calcium + Vitamin D3", cat_map["wellness-devices"], "Cipla Ltd", "Tablet", "Strip of 15",
         110.00, 95.00, 80, "CC-5001", exp_2028, 0,
         "Essential calcium supplement by Cipla enriched with vitamin D3 for bone and joint strength.",
         "Mild constipation if water intake is inadequate.",
         "1 tablet daily after food.",
         "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=300"),

        ("Calcimax 500 Tablet", "Calcium + Magnesium + Zinc + Vitamin D3", cat_map["wellness-devices"], "Meyer Organics", "Tablet", "Strip of 30",
         230.00, 199.00, 0, "CM-5001", exp_2027, 0, # OUT OF STOCK
         "Comprehensive bone mineral complex by Meyer Organics. Currently out of stock.",
         "Mild nausea.",
         "Take 1 tablet daily. (Out of stock - see Shelcal 500 or Cipcal 500).",
         "https://images.unsplash.com/photo-1584017911766-d451b3d0e843?w=300"),

        ("Zincovit Multivitamin & Minerals", "Multivitamins + Multiminerals + Grape Seed", cat_map["wellness-devices"], "Apex Laboratories", "Tablet", "Strip of 15",
         115.00, 99.00, 100, "ZV-1501", exp_2028, 0,
         "Popular immunity builder and nutritional supplement containing essential zinc and antioxidants.",
         "None reported under recommended dosage.",
         "1 tablet once daily after breakfast or lunch.",
         "https://images.unsplash.com/photo-1577401239170-897942555fb3?w=300"),

        ("Supradyn Daily Multivitamin", "Multivitamins with Minerals & Trace Elements", cat_map["wellness-devices"], "Bayer Healthcare", "Tablet", "Strip of 15",
         65.00, 56.00, 0, "SD-1502", exp_2027, 0, # OUT OF STOCK
         "Classic daily multivitamin for fatigue and tiredness from Bayer. Out of stock.",
         "Mild stomach warmth.",
         "1 tablet daily. (Out of stock - see Zincovit or Becosules Z as alternate).",
         "https://images.unsplash.com/photo-1577401239170-897942555fb3?w=300")
    ]

    cursor.executemany("""
    INSERT INTO medicines (
        name, generic_name, category_id, manufacturer, dosage_form, strength,
        price, discount_price, stock_quantity, batch_no, expiry_date, requires_prescription,
        description, side_effects, usage_instructions, image_url
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, medicines)

    # Seed Default Users (Pharmacist & Customer)
    users = [
        ("Dr. Balaji (Chief Pharmacist)", "pharmacist@balajimedical.com", "9876543210", generate_password_hash("admin123"), "pharmacist"),
        ("Adhiraj (Customer)", "adhiraj@example.com", "9876500001", generate_password_hash("user123"), "customer")
    ]

    cursor.executemany("""
    INSERT OR IGNORE INTO users (name, email, phone, password_hash, role)
    VALUES (?, ?, ?, ?, ?)
    """, users)

if __name__ == "__main__":
    init_db(force_reseed=True)
    print(f"Database initialized and seeded successfully at: {DB_FILE}")
