"""
BuildPulse - Database Models & Query Abstraction Layer
"""

from database import get_db_connection
from datetime import datetime, date


def get_kpis():
    """Calculates top-level operational and financial KPIs across all active sites."""
    conn = get_db_connection()
    c = conn.cursor()

    # Project counts
    c.execute("SELECT COUNT(*) FROM projects")
    total_projects = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM projects WHERE status = 'In Progress'")
    active_projects = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM projects WHERE status = 'Completed'")
    completed_projects = c.fetchone()[0]

    # Financials
    c.execute("SELECT COALESCE(SUM(total_budget), 0), COALESCE(SUM(current_spend), 0) FROM projects")
    budget_row = c.fetchone()
    total_budget = budget_row[0]
    total_spend = budget_row[1]

    # Material stock warnings
    c.execute("SELECT COUNT(*) FROM materials WHERE current_stock <= min_threshold")
    low_stock_count = c.fetchone()[0]

    # Active equipment
    c.execute("SELECT COUNT(*) FROM equipment WHERE status = 'In Use'")
    active_equipment_count = c.fetchone()[0]

    # Total workforce
    c.execute("SELECT COUNT(*) FROM workforce WHERE status = 'Active'")
    active_workforce_count = c.fetchone()[0]

    # Open safety incidents
    c.execute("SELECT COUNT(*) FROM safety_incidents WHERE status != 'Resolved'")
    open_incidents_count = c.fetchone()[0]

    # Pending requisitions
    c.execute("SELECT COUNT(*) FROM material_requisitions WHERE status = 'Pending'")
    pending_requisitions_count = c.fetchone()[0]

    conn.close()

    return {
        "total_projects": total_projects,
        "active_projects": active_projects,
        "completed_projects": completed_projects,
        "total_budget": total_budget,
        "total_spend": total_spend,
        "remaining_budget": total_budget - total_spend,
        "low_stock_count": low_stock_count,
        "active_equipment_count": active_equipment_count,
        "active_workforce_count": active_workforce_count,
        "open_incidents_count": open_incidents_count,
        "pending_requisitions_count": pending_requisitions_count
    }


def get_all_projects(status=None, project_type=None, search=None):
    """Retrieves projects with optional filters."""
    conn = get_db_connection()
    c = conn.cursor()

    query = "SELECT * FROM projects WHERE 1=1"
    params = []

    if status and status != 'All':
        query += " AND status = ?"
        params.append(status)

    if project_type and project_type != 'All':
        query += " AND project_type = ?"
        params.append(project_type)

    if search:
        query += " AND (name LIKE ? OR code LIKE ? OR location LIKE ? OR client_name LIKE ?)"
        s = f"%{search}%"
        params.extend([s, s, s, s])

    query += " ORDER BY id DESC"
    c.execute(query, params)
    projects = [dict(row) for row in c.fetchall()]
    conn.close()
    return projects


def get_project_by_id(project_id):
    """Fetches single project with full details."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def get_project_by_code(code):
    """Fetches single project by its unique code (e.g. PRJ-2026-01)."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM projects WHERE UPPER(code) = UPPER(?)", (code.strip(),))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def create_project(data):
    """Inserts a new project into the database."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO projects (code, name, client_name, project_type, location, manager_name,
                              start_date, target_completion, total_budget, current_spend,
                              status, progress_pct, description, banner_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data['code'],
        data['name'],
        data['client_name'],
        data['project_type'],
        data['location'],
        data['manager_name'],
        data['start_date'],
        data['target_completion'],
        float(data.get('total_budget', 0)),
        float(data.get('current_spend', 0)),
        data.get('status', 'Planning'),
        int(data.get('progress_pct', 0)),
        data.get('description', ''),
        data.get('banner_url', 'https://images.unsplash.com/photo-1541888946425-d0fbb18086f7?auto=format&fit=crop&w=1200&q=80')
    ))
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    return new_id


def update_project(project_id, data):
    """Updates project general details."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        UPDATE projects SET
            name = ?,
            client_name = ?,
            project_type = ?,
            location = ?,
            manager_name = ?,
            target_completion = ?,
            total_budget = ?,
            status = ?,
            progress_pct = ?,
            description = ?
        WHERE id = ?
    """, (
        data['name'],
        data['client_name'],
        data['project_type'],
        data['location'],
        data['manager_name'],
        data['target_completion'],
        float(data['total_budget']),
        data['status'],
        int(data['progress_pct']),
        data.get('description', ''),
        project_id
    ))
    conn.commit()
    conn.close()


def get_project_milestones(project_id):
    """Returns all milestones for a given project ordered by due_date."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM milestones WHERE project_id = ? ORDER BY due_date ASC", (project_id,))
    milestones = [dict(row) for row in c.fetchall()]
    conn.close()
    return milestones


def add_milestone(data):
    """Creates a new milestone for a project."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO milestones (project_id, phase_name, title, due_date, status, completion_pct)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        data['project_id'],
        data['phase_name'],
        data['title'],
        data['due_date'],
        data.get('status', 'Pending'),
        int(data.get('completion_pct', 0))
    ))
    new_id = c.lastrowid
    conn.commit()

    # Recalculate average progress for parent project
    c.execute("SELECT AVG(completion_pct) FROM milestones WHERE project_id = ?", (data['project_id'],))
    avg_pct = c.fetchone()[0]
    if avg_pct is not None:
        c.execute("UPDATE projects SET progress_pct = ? WHERE id = ?", (int(avg_pct), data['project_id']))
        conn.commit()

    conn.close()
    return new_id


def update_milestone_status(milestone_id, status, completion_pct):
    """Updates a milestone's progress and status."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE milestones SET status = ?, completion_pct = ? WHERE id = ?", (status, completion_pct, milestone_id))
    
    # Update project progress
    c.execute("SELECT project_id FROM milestones WHERE id = ?", (milestone_id,))
    row = c.fetchone()
    if row:
        project_id = row[0]
        c.execute("SELECT AVG(completion_pct) FROM milestones WHERE project_id = ?", (project_id,))
        avg_pct = c.fetchone()[0]
        if avg_pct is not None:
            c.execute("UPDATE projects SET progress_pct = ? WHERE id = ?", (int(avg_pct), project_id))

    conn.commit()
    conn.close()


def get_all_materials(low_stock_only=False, category=None):
    """Returns materials catalog."""
    conn = get_db_connection()
    c = conn.cursor()
    query = "SELECT * FROM materials WHERE 1=1"
    params = []
    if low_stock_only:
        query += " AND current_stock <= min_threshold"
    if category and category != 'All':
        query += " AND category = ?"
        params.append(category)
    query += " ORDER BY name ASC"
    c.execute(query, params)
    materials = [dict(row) for row in c.fetchall()]
    conn.close()
    return materials


def add_material(data):
    """Adds a new stock item."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO materials (item_code, name, category, unit, unit_cost, current_stock, min_threshold, location)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data['item_code'],
        data['name'],
        data['category'],
        data['unit'],
        float(data['unit_cost']),
        float(data.get('current_stock', 0)),
        float(data.get('min_threshold', 10)),
        data.get('location', 'Central Yard')
    ))
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    return new_id


def get_material_requisitions(project_id=None, status=None):
    """Returns material requisitions joined with project & material names."""
    conn = get_db_connection()
    c = conn.cursor()
    query = """
        SELECT r.*, p.name AS project_name, p.code AS project_code,
               m.name AS material_name, m.item_code AS material_code, m.unit AS material_unit,
               m.unit_cost AS material_unit_cost, (r.quantity * m.unit_cost) AS estimated_cost
        FROM material_requisitions r
        JOIN projects p ON r.project_id = p.id
        JOIN materials m ON r.material_id = m.id
        WHERE 1=1
    """
    params = []
    if project_id:
        query += " AND r.project_id = ?"
        params.append(project_id)
    if status and status != 'All':
        query += " AND r.status = ?"
        params.append(status)
    query += " ORDER BY r.id DESC"
    c.execute(query, params)
    reqs = [dict(row) for row in c.fetchall()]
    conn.close()
    return reqs


def create_requisition(data):
    """Creates a new procurement requisition."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO material_requisitions (requisition_code, project_id, material_id, quantity, requested_by, status, request_date, approval_notes)
        VALUES (?, ?, ?, ?, ?, 'Pending', ?, ?)
    """, (
        data['requisition_code'],
        data['project_id'],
        data['material_id'],
        float(data['quantity']),
        data['requested_by'],
        data.get('request_date', date.today().isoformat()),
        data.get('approval_notes', '')
    ))
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    return new_id


def update_requisition_status(req_id, status, notes=None):
    """Approves, delivers, or rejects requisition, adjusting stock if Delivered."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT material_id, quantity, status FROM material_requisitions WHERE id = ?", (req_id,))
    req = c.fetchone()
    if not req:
        conn.close()
        return False

    old_status = req['status']
    material_id = req['material_id']
    quantity = req['quantity']

    # Update requisition
    if notes:
        c.execute("UPDATE material_requisitions SET status = ?, approval_notes = ? WHERE id = ?", (status, notes, req_id))
    else:
        c.execute("UPDATE material_requisitions SET status = ? WHERE id = ?", (status, req_id))

    # If status transitioned to 'Delivered' from anything else, adjust stock
    if status == 'Delivered' and old_status != 'Delivered':
        c.execute("UPDATE materials SET current_stock = current_stock + ? WHERE id = ?", (quantity, material_id))

    conn.commit()
    conn.close()
    return True


def get_all_equipment(status=None, project_id=None):
    """Fetches equipment fleet with optional project relation."""
    conn = get_db_connection()
    c = conn.cursor()
    query = """
        SELECT e.*, p.name AS project_name, p.code AS project_code
        FROM equipment e
        LEFT JOIN projects p ON e.current_project_id = p.id
        WHERE 1=1
    """
    params = []
    if status and status != 'All':
        query += " AND e.status = ?"
        params.append(status)
    if project_id:
        query += " AND e.current_project_id = ?"
        params.append(project_id)
    query += " ORDER BY e.id ASC"
    c.execute(query, params)
    eq_list = [dict(row) for row in c.fetchall()]
    conn.close()
    return eq_list


def add_equipment(data):
    """Registers a new heavy machinery unit."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO equipment (equipment_code, name, type, current_project_id, operator_name, status, hours_operated, next_service_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data['equipment_code'],
        data['name'],
        data['type'],
        data.get('current_project_id') or None,
        data.get('operator_name', 'Unassigned'),
        data.get('status', 'Available'),
        float(data.get('hours_operated', 0)),
        data.get('next_service_date')
    ))
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    return new_id


def update_equipment(eq_id, status, project_id=None, operator_name=None):
    """Updates deployment and operational status of machinery."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        UPDATE equipment SET
            status = ?,
            current_project_id = ?,
            operator_name = COALESCE(?, operator_name)
        WHERE id = ?
    """, (status, project_id, operator_name, eq_id))
    conn.commit()
    conn.close()


def get_all_workforce(project_id=None, trade=None):
    """Retrieves labor workforce with assigned project names."""
    conn = get_db_connection()
    c = conn.cursor()
    query = """
        SELECT w.*, p.name AS project_name, p.code AS project_code
        FROM workforce w
        LEFT JOIN projects p ON w.assigned_project_id = p.id
        WHERE 1=1
    """
    params = []
    if project_id:
        query += " AND w.assigned_project_id = ?"
        params.append(project_id)
    if trade and trade != 'All':
        query += " AND w.trade = ?"
        params.append(trade)
    query += " ORDER BY w.full_name ASC"
    c.execute(query, params)
    workers = [dict(row) for row in c.fetchall()]
    conn.close()
    return workers


def add_workforce(data):
    """Enrolls a new worker in the register."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO workforce (worker_code, full_name, trade, daily_rate, phone, assigned_project_id, status, safety_cert_valid)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data['worker_code'],
        data['full_name'],
        data['trade'],
        float(data['daily_rate']),
        data.get('phone', ''),
        data.get('assigned_project_id') or None,
        data.get('status', 'Active'),
        int(data.get('safety_cert_valid', 1))
    ))
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    return new_id


def get_all_subcontractors(project_id=None):
    """Retrieves subcontractors list."""
    conn = get_db_connection()
    c = conn.cursor()
    query = """
        SELECT s.*, p.name AS project_name, p.code AS project_code
        FROM subcontractors s
        LEFT JOIN projects p ON s.current_project_id = p.id
        WHERE 1=1
    """
    params = []
    if project_id:
        query += " AND s.current_project_id = ?"
        params.append(project_id)
    query += " ORDER BY s.rating DESC"
    c.execute(query, params)
    subs = [dict(row) for row in c.fetchall()]
    conn.close()
    return subs


def add_subcontractor(data):
    """Enlists a new subcontractor partner."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO subcontractors (company_name, specialty, contact_person, phone, email, contract_value, current_project_id, rating, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data['company_name'],
        data['specialty'],
        data['contact_person'],
        data['phone'],
        data.get('email', ''),
        float(data.get('contract_value', 0)),
        data.get('current_project_id') or None,
        float(data.get('rating', 4.5)),
        data.get('status', 'Active')
    ))
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    return new_id


def get_site_logs(project_id=None, limit=50):
    """Fetches daily site logs."""
    conn = get_db_connection()
    c = conn.cursor()
    query = """
        SELECT sl.*, p.name AS project_name, p.code AS project_code
        FROM site_logs sl
        JOIN projects p ON sl.project_id = p.id
        WHERE 1=1
    """
    params = []
    if project_id:
        query += " AND sl.project_id = ?"
        params.append(project_id)
    query += " ORDER BY sl.log_date DESC, sl.id DESC LIMIT ?"
    params.append(limit)
    c.execute(query, params)
    logs = [dict(row) for row in c.fetchall()]
    conn.close()
    return logs


def add_site_log(data):
    """Appends a new daily site log."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO site_logs (project_id, log_date, weather, temp_c, manpower_count, summary_of_work, delays_or_issues, recorded_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data['project_id'],
        data['log_date'],
        data.get('weather', 'Sunny'),
        int(data.get('temp_c', 28)),
        int(data.get('manpower_count', 0)),
        data['summary_of_work'],
        data.get('delays_or_issues', ''),
        data['recorded_by']
    ))
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    return new_id


def get_safety_incidents(project_id=None, status=None):
    """Returns HSE incident reports."""
    conn = get_db_connection()
    c = conn.cursor()
    query = """
        SELECT si.*, p.name AS project_name, p.code AS project_code
        FROM safety_incidents si
        JOIN projects p ON si.project_id = p.id
        WHERE 1=1
    """
    params = []
    if project_id:
        query += " AND si.project_id = ?"
        params.append(project_id)
    if status and status != 'All':
        query += " AND si.status = ?"
        params.append(status)
    query += " ORDER BY si.id DESC"
    c.execute(query, params)
    incidents = [dict(row) for row in c.fetchall()]
    conn.close()
    return incidents


def add_safety_incident(data):
    """Registers a safety incident / quality hazard ticket."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO safety_incidents (ticket_code, project_id, title, severity, category, description, corrective_action, status, reported_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'Open', ?)
    """, (
        data['ticket_code'],
        data['project_id'],
        data['title'],
        data['severity'],
        data['category'],
        data['description'],
        data.get('corrective_action', ''),
        data.get('reported_date', date.today().isoformat())
    ))
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    return new_id


def resolve_safety_incident(incident_id, action_taken):
    """Marks safety incident as resolved with remediation summary."""
    conn = get_db_connection()
    c = conn.cursor()
    today_str = date.today().isoformat()
    c.execute("""
        UPDATE safety_incidents SET
            status = 'Resolved',
            corrective_action = ?,
            resolved_date = ?
        WHERE id = ?
    """, (action_taken, today_str, incident_id))
    conn.commit()
    conn.close()


def get_expenses(project_id=None, category=None):
    """Fetches expenses ledger."""
    conn = get_db_connection()
    c = conn.cursor()
    query = """
        SELECT e.*, p.name AS project_name, p.code AS project_code
        FROM expenses e
        JOIN projects p ON e.project_id = p.id
        WHERE 1=1
    """
    params = []
    if project_id:
        query += " AND e.project_id = ?"
        params.append(project_id)
    if category and category != 'All':
        query += " AND e.category = ?"
        params.append(category)
    query += " ORDER BY e.expense_date DESC"
    c.execute(query, params)
    records = [dict(row) for row in c.fetchall()]
    conn.close()
    return records


def add_expense(data):
    """Records a project expense and updates project's current_spend."""
    conn = get_db_connection()
    c = conn.cursor()
    amount = float(data['amount'])
    c.execute("""
        INSERT INTO expenses (project_id, category, amount, invoice_ref, description, expense_date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        data['project_id'],
        data['category'],
        amount,
        data.get('invoice_ref', ''),
        data['description'],
        data.get('expense_date', date.today().isoformat())
    ))
    new_id = c.lastrowid

    # Update project current_spend
    c.execute("UPDATE projects SET current_spend = current_spend + ? WHERE id = ?", (amount, data['project_id']))
    conn.commit()
    conn.close()
    return new_id


def get_financial_breakdown():
    """Returns expense breakdowns by category and project budget utilization."""
    conn = get_db_connection()
    c = conn.cursor()

    # Category totals
    c.execute("""
        SELECT category, SUM(amount) AS total
        FROM expenses
        GROUP BY category
        ORDER BY total DESC
    """)
    by_category = [dict(row) for row in c.fetchall()]

    # Project spend vs budget
    c.execute("""
        SELECT id, name, code, total_budget, current_spend,
               (total_budget - current_spend) AS remaining_budget,
               ROUND((current_spend / total_budget) * 100, 1) AS burn_pct
        FROM projects
        ORDER BY total_budget DESC
    """)
    project_financials = [dict(row) for row in c.fetchall()]

    conn.close()
    return {
        "by_category": by_category,
        "project_financials": project_financials
    }
