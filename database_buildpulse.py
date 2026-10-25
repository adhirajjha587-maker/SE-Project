"""
BuildPulse - Construction Management System (CMS)
Database configuration, schema creation, and realistic seed data.
"""

import sqlite3
import os
from datetime import datetime, date, timedelta

DB_NAME = "buildpulse.db"
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_NAME)


def get_db_connection():
    """Returns a connection to the SQLite database with row factory enabled."""
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(force_reseed=False):
    """Initializes tables and optionally seeds demo data if empty or forced."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create tables
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        client_name TEXT NOT NULL,
        project_type TEXT NOT NULL, -- Commercial, Residential, Infrastructure, Industrial
        location TEXT NOT NULL,
        manager_name TEXT NOT NULL,
        start_date DATE NOT NULL,
        target_completion DATE NOT NULL,
        total_budget REAL NOT NULL,
        current_spend REAL DEFAULT 0.0,
        status TEXT NOT NULL DEFAULT 'In Progress', -- Planning, In Progress, On Hold, Completed
        progress_pct INTEGER DEFAULT 0,
        description TEXT,
        banner_url TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS milestones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        phase_name TEXT NOT NULL, -- Excavation, Foundation, Structural, MEP, Finishing, Handover
        title TEXT NOT NULL,
        due_date DATE NOT NULL,
        status TEXT NOT NULL DEFAULT 'Pending', -- Pending, In Progress, Completed, Delayed
        completion_pct INTEGER DEFAULT 0,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS materials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        category TEXT NOT NULL, -- Structural, Aggregates, Electrical, Plumbing, Finishing
        unit TEXT NOT NULL, -- Bags, Tons, m3, Meters, Units
        unit_cost REAL NOT NULL,
        current_stock REAL NOT NULL DEFAULT 0,
        min_threshold REAL NOT NULL DEFAULT 10,
        location TEXT NOT NULL DEFAULT 'Central Yard'
    );

    CREATE TABLE IF NOT EXISTS material_requisitions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        requisition_code TEXT UNIQUE NOT NULL,
        project_id INTEGER NOT NULL,
        material_id INTEGER NOT NULL,
        quantity REAL NOT NULL,
        requested_by TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Pending', -- Pending, Approved, Delivered, Rejected
        request_date DATE NOT NULL,
        approval_notes TEXT,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
        FOREIGN KEY (material_id) REFERENCES materials(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS equipment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        equipment_code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        type TEXT NOT NULL, -- Earthmoving, Lifting, Concrete, Transport, Power
        current_project_id INTEGER,
        operator_name TEXT,
        status TEXT NOT NULL DEFAULT 'Available', -- Available, In Use, Maintenance, Out of Service
        hours_operated REAL DEFAULT 0,
        next_service_date DATE,
        FOREIGN KEY (current_project_id) REFERENCES projects(id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS workforce (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        worker_code TEXT UNIQUE NOT NULL,
        full_name TEXT NOT NULL,
        trade TEXT NOT NULL, -- Site Engineer, Foreman, Mason, Carpenter, Electrician, Welder, Crane Operator
        daily_rate REAL NOT NULL,
        phone TEXT,
        assigned_project_id INTEGER,
        status TEXT NOT NULL DEFAULT 'Active', -- Active, On Leave, Inactive
        safety_cert_valid INTEGER DEFAULT 1, -- 1 = Valid, 0 = Expired
        FOREIGN KEY (assigned_project_id) REFERENCES projects(id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS subcontractors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT NOT NULL,
        specialty TEXT NOT NULL, -- HVAC, Structural Steel, Glazing, Fire Protection, Piling
        contact_person TEXT NOT NULL,
        phone TEXT NOT NULL,
        email TEXT,
        contract_value REAL NOT NULL,
        current_project_id INTEGER,
        rating REAL DEFAULT 4.5,
        status TEXT NOT NULL DEFAULT 'Active',
        FOREIGN KEY (current_project_id) REFERENCES projects(id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS site_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        log_date DATE NOT NULL,
        weather TEXT NOT NULL, -- Sunny, Clear, Rainy, Windy, Extreme Heat
        temp_c INTEGER DEFAULT 28,
        manpower_count INTEGER NOT NULL,
        summary_of_work TEXT NOT NULL,
        delays_or_issues TEXT,
        recorded_by TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS safety_incidents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_code TEXT UNIQUE NOT NULL,
        project_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        severity TEXT NOT NULL, -- Low, Medium, High, Critical
        category TEXT NOT NULL, -- Fall Hazard, PPE Violation, Electrical, Scaffolding, Near Miss, Defect
        description TEXT NOT NULL,
        corrective_action TEXT,
        status TEXT NOT NULL DEFAULT 'Open', -- Open, Investigating, Resolved
        reported_date DATE NOT NULL,
        resolved_date DATE,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        category TEXT NOT NULL, -- Materials, Labor, Equipment Rental, Subcontractor, Permits/Inspections
        amount REAL NOT NULL,
        invoice_ref TEXT,
        description TEXT NOT NULL,
        expense_date DATE NOT NULL,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
    );
    """)
    conn.commit()

    # Check if seed data exists
    cursor.execute("SELECT COUNT(*) FROM projects")
    count = cursor.fetchone()[0]

    if count == 0 or force_reseed:
        if force_reseed and count > 0:
            # Clear existing data
            cursor.executescript("""
                DELETE FROM expenses;
                DELETE FROM safety_incidents;
                DELETE FROM site_logs;
                DELETE FROM subcontractors;
                DELETE FROM workforce;
                DELETE FROM equipment;
                DELETE FROM material_requisitions;
                DELETE FROM materials;
                DELETE FROM milestones;
                DELETE FROM projects;
            """)
            conn.commit()

        seed_data(conn)

    conn.close()


def seed_data(conn):
    """Populates realistic, high-fidelity sample data across all construction modules."""
    cursor = conn.cursor()

    # 1. Projects
    projects = [
        (
            1,
            "PRJ-2026-01",
            "Apex Horizon Sky Tower",
            "Metropolis Development Corp",
            "Commercial",
            "Sector 42, Financial District, New Delhi",
            "Vikramaditya Sharma, PE",
            "2025-10-15",
            "2027-04-30",
            45000000.0,
            19850000.0,
            "In Progress",
            46,
            "A 38-storey LEED Platinum commercial skyscraper featuring earthquake-resistant shear wall core, triple-glazed facade, and high-speed elevator shafts.",
            "https://images.unsplash.com/photo-1541888946425-d0fbb18086f7?auto=format&fit=crop&w=1200&q=80"
        ),
        (
            2,
            "PRJ-2026-02",
            "Greenfield Eco-Residences",
            "Serene Habitat Developers",
            "Residential",
            "Phase 3, Greater Noida Expressway",
            "Ananya Deshmukh",
            "2026-01-10",
            "2027-11-15",
            18500000.0,
            5200000.0,
            "In Progress",
            32,
            "Gated sustainable villa community with solar power grids, rainwater harvesting reservoirs, and precast insulated concrete masonry.",
            "https://images.unsplash.com/photo-1503387762-592deb58ef4e?auto=format&fit=crop&w=1200&q=80"
        ),
        (
            3,
            "PRJ-2026-03",
            "Urban Metro Overpass & Elevated Corridor",
            "State Transit Infrastructure Authority",
            "Infrastructure",
            "Ring Road Central Corridor, Sector 18",
            "Er. Rajesh Khanna",
            "2025-05-01",
            "2026-12-20",
            32000000.0,
            24500000.0,
            "In Progress",
            78,
            "Elevated dual-track rapid rail viaduct spanning 6.4 km with pre-stressed box girders and 4 multi-modal interchange stations.",
            "https://images.unsplash.com/photo-1517581177682-a085bb7ffb15?auto=format&fit=crop&w=1200&q=80"
        ),
        (
            4,
            "PRJ-2026-04",
            "Lifeline Multi-Specialty Hospital Wing",
            "Apex Healthcare Trust",
            "Commercial",
            "Civic Center Blvd, South Extension",
            "Dr. / Eng. Meera Sen",
            "2026-03-01",
            "2027-08-31",
            22000000.0,
            2800000.0,
            "In Progress",
            18,
            "Modern 400-bed trauma & surgical wing with cleanroom grade HVAC, medical gas piping distribution, and dual backup power substations.",
            "https://images.unsplash.com/photo-1581094794329-c8112a89af12?auto=format&fit=crop&w=1200&q=80"
        ),
        (
            5,
            "PRJ-2026-05",
            "Logistic Park Automated Fulfillment Hub",
            "Zenith Cargo Global",
            "Industrial",
            "National Highway 48 Freight Zone",
            "Arjun Mehta",
            "2025-02-15",
            "2026-05-30",
            14000000.0,
            13400000.0,
            "In Progress",
            94,
            "A 450,000 sq.ft high-bay steel warehouse with laser-leveled superflat concrete flooring, automated docking bays, and ESFR fire suppression.",
            "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?auto=format&fit=crop&w=1200&q=80"
        )
    ]

    cursor.executemany("""
    INSERT INTO projects (id, code, name, client_name, project_type, location, manager_name, start_date, target_completion, total_budget, current_spend, status, progress_pct, description, banner_url)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, projects)
    conn.commit()

    # 2. Milestones
    milestones = [
        # Project 1: Apex Horizon Sky Tower
        (1, "Phase 1 - Substructure", "Deep Piling & Raft Foundation", "2026-01-30", "Completed", 100),
        (1, "Phase 2 - Core Structure", "Concrete Core Slipform up to Floor 24", "2026-06-30", "In Progress", 65),
        (1, "Phase 3 - Façade & Envelope", "Unitized Double Curtain Glass Installation", "2026-11-15", "Pending", 15),
        (1, "Phase 4 - MEP", "Chilled Water Risers & Substation Transformers", "2027-01-30", "Pending", 0),
        (1, "Phase 5 - Fit-out & Handover", "Occupancy Certificate & Client Handover", "2027-04-30", "Pending", 0),

        # Project 2: Greenfield Eco-Residences
        (2, "Phase 1 - Site Prep", "Earthmoving, Grading & Drainage Grids", "2026-03-15", "Completed", 100),
        (2, "Phase 2 - Foundations", "Reinforced Strip Footings for Villas 1-20", "2026-06-15", "In Progress", 70),
        (2, "Phase 3 - Superstructure", "AAC Block Masonry & Precast Slabs", "2026-12-30", "Pending", 10),
        (2, "Phase 4 - Finishing", "Solar Roofing & Interior Millwork", "2027-09-30", "Pending", 0),

        # Project 3: Urban Metro
        (3, "Phase 1 - Pier Construction", "Cast-in-situ Piers 1 through 85", "2025-11-30", "Completed", 100),
        (3, "Phase 2 - Viaduct Girders", "Segmental Box Girder Launching", "2026-04-15", "Completed", 100),
        (3, "Phase 3 - Track Laying", "Ballastless Track Slab & Rail Welding", "2026-08-30", "In Progress", 75),
        (3, "Phase 4 - Traction & Signaling", "Third Rail 750V DC Power & CBTC Signaling", "2026-11-15", "In Progress", 40),

        # Project 4: Lifeline Hospital Wing
        (4, "Phase 1 - Excavation & Basement", "Double Basement Excavation & Shoring", "2026-05-15", "In Progress", 60),
        (4, "Phase 2 - Reinforced Concrete", "RCC Frame Construction Floors 1-6", "2026-10-31", "Pending", 0),

        # Project 5: Logistic Park
        (5, "Phase 1 - Foundation & Slab", "Laser Leveled Post-Tensioned Flooring", "2025-08-30", "Completed", 100),
        (5, "Phase 2 - Pre-engineered Steel", "PEB Rafters & Insulated Sandwich Panels", "2025-12-20", "Completed", 100),
        (5, "Phase 3 - Systems & Docking", "Hydraulic Dock Levelers & Fire Sprinklers", "2026-04-10", "In Progress", 90),
        (5, "Phase 4 - Handover", "Commissioning & Safety Clearance", "2026-05-30", "In Progress", 80)
    ]
    cursor.executemany("""
    INSERT INTO milestones (project_id, phase_name, title, due_date, status, completion_pct)
    VALUES (?, ?, ?, ?, ?, ?)
    """, milestones)

    # 3. Materials
    materials = [
        (1, "MAT-001", "OPC 53 Grade Portland Cement", "Structural", "Bags", 380.0, 3450, 500, "Central Yard A"),
        (2, "MAT-002", "TMT Steel Fe 550D (16mm Rebar)", "Structural", "Tons", 58500.0, 48.5, 15, "Sector 42 Yard"),
        (3, "MAT-003", "Ready-Mix Concrete M35 Grade", "Structural", "m3", 4200.0, 240, 50, "Direct Batching Plant"),
        (4, "MAT-004", "River Sand / Manufactured M-Sand", "Aggregates", "Tons", 1850.0, 310, 80, "Aggregate Stockpile 1"),
        (5, "MAT-005", "Coarse Blue Metal Aggregate 20mm", "Aggregates", "Tons", 1450.0, 420, 100, "Stockpile 2"),
        (6, "MAT-006", "Autoclaved Aerated Concrete (AAC) Blocks", "Finishing", "Units", 75.0, 14200, 2000, "Warehouse Bay B"),
        (7, "MAT-007", "Heavy Gauge Conduit Pipes (25mm PVC)", "Electrical", "Meters", 45.0, 1200, 1500, "Electrical Depot"),
        (8, "MAT-008", "Copper Armored Power Cable 4-Core 16mm", "Electrical", "Meters", 340.0, 850, 400, "Central Stores"),
        (9, "MAT-009", "CPVC High Pressure Water Pipes 1-inch", "Plumbing", "Meters", 120.0, 620, 300, "Plumbing Store"),
        (10, "MAT-010", "Structural Steel I-Beams (ISMB 400)", "Structural", "Tons", 64000.0, 18.2, 20, "Steel Yard 3")
    ]
    cursor.executemany("""
    INSERT INTO materials (id, item_code, name, category, unit, unit_cost, current_stock, min_threshold, location)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, materials)

    # 4. Material Requisitions
    requisitions = [
        ("REQ-2026-081", 1, 2, 12.0, "Eng. Raghav Nair", "Approved", "2026-10-20", "Urgent for floor 18 slab casting"),
        ("REQ-2026-082", 1, 1, 450.0, "Foreman Harish", "Delivered", "2026-10-18", "Received and stored in dry godown"),
        ("REQ-2026-083", 2, 6, 2500.0, "Site Mgr Deshmukh", "Approved", "2026-10-21", "Scheduled dispatch tomorrow"),
        ("REQ-2026-084", 3, 3, 60.0, "Er. Rajesh Khanna", "Pending", "2026-10-22", "Pending procurement authorization"),
        ("REQ-2026-085", 4, 10, 8.5, "Lead Tech Roy", "Pending", "2026-10-23", "Basement soldier pile reinforcement")
    ]
    cursor.executemany("""
    INSERT INTO material_requisitions (requisition_code, project_id, material_id, quantity, requested_by, status, request_date, approval_notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, requisitions)

    # 5. Equipment Fleet
    equipment = [
        ("EQP-01", "Liebherr 280 EC-H Tower Crane", "Lifting", 1, "Mohan Lal (Certified A-Class)", "In Use", 1420.5, "2026-11-15"),
        ("EQP-02", "CAT 320 GC Hydraulic Excavator", "Earthmoving", 4, "Sunil Rawat", "In Use", 2850.0, "2026-11-01"),
        ("EQP-03", "Schwing Stetter Concrete Boom Pump 36m", "Concrete", 1, "Dinesh Yadav", "In Use", 910.0, "2026-12-05"),
        ("EQP-04", "JCB 3DX Super Backhoe Loader", "Earthmoving", 2, "Kishan Chand", "In Use", 3420.5, "2026-10-28"),
        ("EQP-05", "Komatsu D85EX Crawler Bulldozer", "Earthmoving", None, "Unassigned", "Available", 1850.0, "2026-11-20"),
        ("EQP-06", "Kirloskar 250 kVA Silent Diesel Generator", "Power", 3, "Rajesh Kumar", "In Use", 4120.0, "2026-11-10"),
        ("EQP-07", "Volvo FMX 440 Heavy Tipper Dump Truck", "Transport", 3, "Satish Verma", "Maintenance", 5210.0, "2026-10-25")
    ]
    cursor.executemany("""
    INSERT INTO equipment (equipment_code, name, type, current_project_id, operator_name, status, hours_operated, next_service_date)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, equipment)

    # 6. Workforce
    workforce = [
        ("WRK-101", "Deepak Verma", "Site Engineer", 1800.0, "+91 98112 34011", 1, "Active", 1),
        ("WRK-102", "Ram Singh Gujjar", "Foreman", 1400.0, "+91 98223 45122", 1, "Active", 1),
        ("WRK-103", "Babulal Mondal", "Mason", 950.0, "+91 97118 90233", 1, "Active", 1),
        ("WRK-104", "Mohan Lal", "Crane Operator", 1600.0, "+91 99102 77144", 1, "Active", 1),
        ("WRK-105", "Suresh Carpenter", "Carpenter", 900.0, "+91 98334 11255", 2, "Active", 1),
        ("WRK-106", "Ramesh Chand", "Mason", 950.0, "+91 98199 44366", 2, "Active", 1),
        ("WRK-107", "Javed Ali", "Welder", 1100.0, "+91 98711 55677", 3, "Active", 1),
        ("WRK-108", "Santosh K. Tiwari", "Electrician", 1050.0, "+91 98231 66788", 3, "Active", 1),
        ("WRK-109", "Sunil Rawat", "Excavator Operator", 1450.0, "+91 98110 88999", 4, "Active", 1),
        ("WRK-110", "Pravin Solanki", "Safety Officer", 1750.0, "+91 98212 99000", 1, "Active", 1)
    ]
    cursor.executemany("""
    INSERT INTO workforce (worker_code, full_name, trade, daily_rate, phone, assigned_project_id, status, safety_cert_valid)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, workforce)

    # 7. Subcontractors
    subcontractors = [
        ("Apex Façades & Glazing Ltd", "Glazing & Curtain Walls", "Nitin Tandon", "+91 98101 22334", "nitin@apexfacade.com", 6800000.0, 1, 4.8, "Active"),
        ("Precision Piling & Geotech Works", "Deep Foundation & Piling", "Sanjay Aggarwal", "+91 98221 44556", "sanjay@precisionpiling.in", 4200000.0, 4, 4.6, "Active"),
        ("CoolBreeze Industrial HVAC Solutions", "Chillers & Ventilation", "Kavita Rao", "+91 98332 66778", "contact@coolbreezehvac.com", 5500000.0, 1, 4.7, "Active"),
        ("Durashield Fire Safety Systems", "Fire Hydrants & Sprinklers", "Arun Nambiar", "+91 98443 88990", "info@durashield.co.in", 3100000.0, 5, 4.9, "Active")
    ]
    cursor.executemany("""
    INSERT INTO subcontractors (company_name, specialty, contact_person, phone, email, contract_value, current_project_id, rating, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, subcontractors)

    # 8. Site Logs
    site_logs = [
        (1, "2026-10-22", "Sunny", 29, 64, "Completed rebar tying for floor 18 western wing. Concrete pump set up for early morning pour tomorrow.", "Minor wind gust in afternoon; crane operations paused for 45 minutes as safety precaution.", "Vikramaditya Sharma"),
        (1, "2026-10-21", "Clear", 27, 62, "Installed 14 curtain wall panels on levels 9 and 10. Electrical risers extended to floor 15.", "None. Work progressed ahead of milestone schedule.", "Deepak Verma"),
        (2, "2026-10-22", "Sunny", 31, 38, "Excavated footings for Villa cluster D (Units 13-16). Leveling checks approved by municipal inspector.", "Slight delay in water tanker arrival; resolved by 11:00 AM.", "Ananya Deshmukh"),
        (3, "2026-10-22", "Sunny", 28, 55, "Welded rail joints between chainage 4+200 and 4+800. Ultrasonic flaw detection tests passed.", "Traffic diversion on feeder road managed smoothly with traffic marshals.", "Er. Rajesh Khanna"),
        (4, "2026-10-22", "Overcast", 26, 42, "Soldier pile installation continuing on Northern retaining perimeter. 8 out of 12 micropiles drilled.", "High soil moisture encountered at 9m depth; bentonite slurry pumped.", "Meera Sen")
    ]
    cursor.executemany("""
    INSERT INTO site_logs (project_id, log_date, weather, temp_c, manpower_count, summary_of_work, delays_or_issues, recorded_by)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, site_logs)

    # 9. Safety Incidents
    safety = [
        ("HSE-2026-01", 1, "Improper Scaffolding Toe-board on Level 16", "Medium", "Scaffolding", "Inspection found missing toe-boards on the perimeter cantilever scaffolding platform.", "Platform temporarily red-tagged. Toe-boards installed and re-inspected within 3 hours.", "Resolved", "2026-10-19", "2026-10-19"),
        ("HSE-2026-02", 3, "Near-Miss: Overhead Cable Swing during High Gust", "High", "Near Miss", "A secondary power line swung close to crane boom during 40km/h gust.", "Work stopped immediately. Wind speed monitoring protocol re-briefed to all operators.", "Resolved", "2026-10-15", "2026-10-16"),
        ("HSE-2026-03", 4, "Inadequate Trench Shoring in Water Line Excavation", "High", "Fall Hazard", "Deep 2.8m trench showed sign of side wall sloughing without trench box installed.", "Workers evacuated. Shoring hydraulic box placed before work resumed.", "Resolved", "2026-10-12", "2026-10-13"),
        ("HSE-2026-04", 1, "Worker spotted without chin-strap on Hard Hat", "Low", "PPE Violation", "Subcontractor glazier technician working at elevation with loose helmet.", "Worker stood down, given toolbox talk, and re-issued high-impact harness helmet.", "Resolved", "2026-10-21", "2026-10-21"),
        ("HSE-2026-05", 2, "Exposed Temporary Cable near Vehicle Entry Gate", "Medium", "Electrical", "Generator feeder cable crossing dump truck pathway without rubber cable protector.", "Protective heavy-duty rubber cable ramp installed across roadway.", "Resolved", "2026-10-22", "2026-10-22")
    ]
    cursor.executemany("""
    INSERT INTO safety_incidents (ticket_code, project_id, title, severity, category, description, corrective_action, status, reported_date, resolved_date)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, safety)

    # 10. Expenses
    expenses = [
        (1, "Materials", 1420000.0, "INV-STEEL-994", "TMT Rebar 24 Tons delivery from Tata Steel", "2026-10-14"),
        (1, "Subcontractor", 850000.0, "INV-FACADE-02", "Milestone payment for glazing installation batch 2", "2026-10-18"),
        (1, "Equipment Rental", 320000.0, "INV-CRANE-OCT", "Monthly mobile crane and pump rental lease", "2026-10-01"),
        (2, "Materials", 450000.0, "INV-AAC-220", "AAC Block consignment for Villa cluster A & B", "2026-10-10"),
        (2, "Labor", 280000.0, "PAYROLL-WK42", "Bi-weekly direct labor wage disbursement", "2026-10-15"),
        (3, "Materials", 1850000.0, "INV-RAIL-08", "Head hardened rail steel shipments", "2026-09-28"),
        (3, "Subcontractor", 1200000.0, "INV-CBTC-01", "Signaling integration phase advance payment", "2026-10-05"),
        (4, "Equipment Rental", 195000.0, "INV-PILING-RIG", "Piling rig monthly operating lease", "2026-10-08"),
        (5, "Finishing", 760000.0, "INV-DOCK-88", "Industrial dock leveler delivery and mounting", "2026-10-11")
    ]
    cursor.executemany("""
    INSERT INTO expenses (project_id, category, amount, invoice_ref, description, expense_date)
    VALUES (?, ?, ?, ?, ?, ?)
    """, expenses)

    conn.commit()


if __name__ == "__main__":
    print("Initializing BuildPulse Database...")
    init_db(force_reseed=True)
    print("Database successfully initialized and seeded at:", DB_PATH)
