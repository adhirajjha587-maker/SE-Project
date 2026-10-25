"""
BuildPulse - Construction Management System (CMS)
Main Flask Application and Route Controllers
"""

import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, date
import json

from database_buildpulse import init_db
import models

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "buildpulse-construction-secret-2026")

# Ensure database is created on startup
init_db(force_reseed=False)


# Custom Jinja filters for currency and formatting
@app.template_filter('currency')
def currency_filter(value):
    try:
        val = float(value)
        # Indian/Global formatted currency: $ or ₹ depending on preference; let's format nicely with $
        return f"${val:,.2f}"
    except (ValueError, TypeError):
        return "$0.00"


@app.template_filter('currency_compact')
def currency_compact_filter(value):
    try:
        val = float(value)
        if val >= 1_000_000:
            return f"${val / 1_000_000:.2f}M"
        elif val >= 1_000:
            return f"${val / 1_000:.1f}k"
        return f"${val:,.0f}"
    except (ValueError, TypeError):
        return "$0"


@app.template_filter('date_format')
def date_format_filter(value):
    if not value:
        return ""
    try:
        dt = datetime.strptime(str(value)[:10], "%Y-%m-%d")
        return dt.strftime("%b %d, %Y")
    except Exception:
        return str(value)


# Global context processor
@app.context_processor
def inject_global_data():
    kpis = models.get_kpis()
    all_projects = models.get_all_projects()
    return {
        "global_kpis": kpis,
        "global_projects": all_projects,
        "now_year": datetime.now().year
    }


# ==========================================
# 1. Executive Operations Dashboard
# ==========================================
@app.route('/')
@app.route('/dashboard')
def dashboard():
    kpis = models.get_kpis()
    projects = models.get_all_projects()
    recent_logs = models.get_site_logs(limit=5)
    low_stock_materials = models.get_all_materials(low_stock_only=True)
    pending_requisitions = models.get_material_requisitions(status='Pending')
    equipment_in_use = models.get_all_equipment(status='In Use')
    recent_incidents = models.get_safety_incidents()[:4]
    financial_data = models.get_financial_breakdown()

    # Chart datasets
    chart_project_names = [p['name'][:18] + '..' if len(p['name']) > 18 else p['name'] for p in projects[:5]]
    chart_project_budgets = [p['total_budget'] for p in projects[:5]]
    chart_project_spends = [p['current_spend'] for p in projects[:5]]
    chart_project_progress = [p['progress_pct'] for p in projects[:5]]

    category_labels = [c['category'] for c in financial_data['by_category']]
    category_totals = [c['total'] for c in financial_data['by_category']]

    return render_template(
        'buildpulse_dashboard.html',
        active_page='dashboard',
        kpis=kpis,
        projects=projects,
        recent_logs=recent_logs,
        low_stock_materials=low_stock_materials,
        pending_requisitions=pending_requisitions,
        equipment_in_use=equipment_in_use,
        recent_incidents=recent_incidents,
        chart_data=json.dumps({
            "project_names": chart_project_names,
            "project_budgets": chart_project_budgets,
            "project_spends": chart_project_spends,
            "project_progress": chart_project_progress,
            "category_labels": category_labels,
            "category_totals": category_totals
        })
    )


# ==========================================
# 2. Projects Module
# ==========================================
@app.route('/projects')
def projects_list():
    status_filter = request.args.get('status', 'All')
    type_filter = request.args.get('type', 'All')
    search_query = request.args.get('search', '').strip()

    projects = models.get_all_projects(
        status=status_filter,
        project_type=type_filter,
        search=search_query
    )
    return render_template(
        'projects.html',
        active_page='projects',
        projects=projects,
        current_status=status_filter,
        current_type=type_filter,
        search_query=search_query
    )


@app.route('/projects/new', methods=['POST'])
def project_create():
    # Auto-generate a code if not provided
    code = request.form.get('code', '').strip().upper()
    if not code:
        code = f"PRJ-{datetime.now().strftime('%Y')}-{int(datetime.now().timestamp()) % 1000:03d}"

    data = {
        'code': code,
        'name': request.form.get('name'),
        'client_name': request.form.get('client_name'),
        'project_type': request.form.get('project_type'),
        'location': request.form.get('location'),
        'manager_name': request.form.get('manager_name'),
        'start_date': request.form.get('start_date'),
        'target_completion': request.form.get('target_completion'),
        'total_budget': request.form.get('total_budget', 0),
        'current_spend': 0,
        'status': request.form.get('status', 'In Progress'),
        'progress_pct': int(request.form.get('progress_pct', 0)),
        'description': request.form.get('description', ''),
        'banner_url': request.form.get('banner_url') or 'https://images.unsplash.com/photo-1541888946425-d0fbb18086f7?auto=format&fit=crop&w=1200&q=80'
    }

    try:
        new_id = models.create_project(data)
        flash(f"Project '{data['name']}' ({data['code']}) created successfully!", "success")
        return redirect(url_for('project_detail', project_id=new_id))
    except Exception as e:
        flash(f"Error creating project: {str(e)}", "danger")
        return redirect(url_for('projects_list'))


@app.route('/projects/<int:project_id>')
def project_detail(project_id):
    project = models.get_project_by_id(project_id)
    if not project:
        flash("Project not found.", "danger")
        return redirect(url_for('projects_list'))

    tab = request.args.get('tab', 'overview')
    milestones = models.get_project_milestones(project_id)
    requisitions = models.get_material_requisitions(project_id=project_id)
    equipment = models.get_all_equipment(project_id=project_id)
    workforce = models.get_all_workforce(project_id=project_id)
    subcontractors = models.get_all_subcontractors(project_id=project_id)
    site_logs = models.get_site_logs(project_id=project_id, limit=30)
    safety_incidents = models.get_safety_incidents(project_id=project_id)
    expenses = models.get_expenses(project_id=project_id)
    all_materials = models.get_all_materials()

    return render_template(
        'project_detail.html',
        active_page='projects',
        project=project,
        active_tab=tab,
        milestones=milestones,
        requisitions=requisitions,
        equipment=equipment,
        workforce=workforce,
        subcontractors=subcontractors,
        site_logs=site_logs,
        safety_incidents=safety_incidents,
        expenses=expenses,
        all_materials=all_materials
    )


@app.route('/projects/<int:project_id>/update', methods=['POST'])
def project_update(project_id):
    data = {
        'name': request.form.get('name'),
        'client_name': request.form.get('client_name'),
        'project_type': request.form.get('project_type'),
        'location': request.form.get('location'),
        'manager_name': request.form.get('manager_name'),
        'target_completion': request.form.get('target_completion'),
        'total_budget': request.form.get('total_budget'),
        'status': request.form.get('status'),
        'progress_pct': request.form.get('progress_pct', 0),
        'description': request.form.get('description', '')
    }
    models.update_project(project_id, data)
    flash("Project details updated successfully.", "success")
    return redirect(url_for('project_detail', project_id=project_id, tab='overview'))


@app.route('/projects/<int:project_id>/milestones/new', methods=['POST'])
def milestone_create(project_id):
    data = {
        'project_id': project_id,
        'phase_name': request.form.get('phase_name'),
        'title': request.form.get('title'),
        'due_date': request.form.get('due_date'),
        'status': request.form.get('status', 'Pending'),
        'completion_pct': int(request.form.get('completion_pct', 0))
    }
    models.add_milestone(data)
    flash("New milestone added.", "success")
    return redirect(url_for('project_detail', project_id=project_id, tab='milestones'))


# ==========================================
# 3. Materials & Procurement
# ==========================================
@app.route('/materials')
def materials_list():
    category_filter = request.args.get('category', 'All')
    low_stock = request.args.get('low_stock') == '1'
    tab = request.args.get('tab', 'inventory')

    materials = models.get_all_materials(low_stock_only=low_stock, category=category_filter)
    requisitions = models.get_material_requisitions()
    projects = models.get_all_projects()

    return render_template(
        'materials.html',
        active_page='materials',
        materials=materials,
        requisitions=requisitions,
        projects=projects,
        current_category=category_filter,
        is_low_stock=low_stock,
        active_tab=tab
    )


@app.route('/materials/new', methods=['POST'])
def material_create():
    code = request.form.get('item_code', '').strip().upper()
    if not code:
        code = f"MAT-{int(datetime.now().timestamp()) % 10000:04d}"

    data = {
        'item_code': code,
        'name': request.form.get('name'),
        'category': request.form.get('category'),
        'unit': request.form.get('unit'),
        'unit_cost': request.form.get('unit_cost', 0),
        'current_stock': request.form.get('current_stock', 0),
        'min_threshold': request.form.get('min_threshold', 10),
        'location': request.form.get('location', 'Central Yard')
    }
    models.add_material(data)
    flash(f"Material item '{data['name']}' added to inventory.", "success")
    return redirect(url_for('materials_list', tab='inventory'))


@app.route('/materials/requisitions/new', methods=['POST'])
def requisition_create():
    code = f"REQ-{datetime.now().strftime('%Y')}-{int(datetime.now().timestamp()) % 1000:03d}"
    project_id = int(request.form.get('project_id'))
    data = {
        'requisition_code': code,
        'project_id': project_id,
        'material_id': int(request.form.get('material_id')),
        'quantity': float(request.form.get('quantity')),
        'requested_by': request.form.get('requested_by'),
        'request_date': request.form.get('request_date', date.today().isoformat()),
        'approval_notes': request.form.get('approval_notes', '')
    }
    models.create_requisition(data)
    flash(f"Material requisition {code} submitted successfully.", "success")

    redirect_to = request.form.get('redirect_to')
    if redirect_to == 'project':
        return redirect(url_for('project_detail', project_id=project_id, tab='materials'))
    return redirect(url_for('materials_list', tab='requisitions'))


@app.route('/api/requisitions/<int:req_id>/status', methods=['POST'])
def requisition_status_update(req_id):
    status = request.form.get('status')
    notes = request.form.get('notes')
    success = models.update_requisition_status(req_id, status, notes)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({"success": success, "status": status})
    flash(f"Requisition status updated to {status}.", "success")
    return redirect(request.referrer or url_for('materials_list', tab='requisitions'))


# ==========================================
# 4. Equipment & Fleet Management
# ==========================================
@app.route('/equipment')
def equipment_list():
    status_filter = request.args.get('status', 'All')
    equipment = models.get_all_equipment(status=status_filter)
    projects = models.get_all_projects()

    return render_template(
        'equipment.html',
        active_page='equipment',
        equipment=equipment,
        projects=projects,
        current_status=status_filter
    )


@app.route('/equipment/new', methods=['POST'])
def equipment_create():
    code = request.form.get('equipment_code', '').strip().upper()
    if not code:
        code = f"EQP-{int(datetime.now().timestamp()) % 1000:03d}"

    data = {
        'equipment_code': code,
        'name': request.form.get('name'),
        'type': request.form.get('type'),
        'current_project_id': request.form.get('current_project_id') or None,
        'operator_name': request.form.get('operator_name', 'Unassigned'),
        'status': request.form.get('status', 'Available'),
        'hours_operated': request.form.get('hours_operated', 0),
        'next_service_date': request.form.get('next_service_date')
    }
    models.add_equipment(data)
    flash(f"Equipment '{data['name']}' added to fleet.", "success")
    return redirect(url_for('equipment_list'))


@app.route('/api/equipment/<int:eq_id>/status', methods=['POST'])
def equipment_status_update(eq_id):
    status = request.form.get('status')
    project_id = request.form.get('project_id')
    operator_name = request.form.get('operator_name')

    project_id = int(project_id) if project_id and project_id != 'None' else None
    models.update_equipment(eq_id, status, project_id, operator_name)
    flash("Equipment status updated.", "success")
    return redirect(request.referrer or url_for('equipment_list'))


# ==========================================
# 5. Workforce & Subcontractors
# ==========================================
@app.route('/workforce')
def workforce_list():
    trade_filter = request.args.get('trade', 'All')
    tab = request.args.get('tab', 'workers')

    workers = models.get_all_workforce(trade=trade_filter)
    subcontractors = models.get_all_subcontractors()
    projects = models.get_all_projects()

    return render_template(
        'workforce.html',
        active_page='workforce',
        workers=workers,
        subcontractors=subcontractors,
        projects=projects,
        current_trade=trade_filter,
        active_tab=tab
    )


@app.route('/workforce/new', methods=['POST'])
def workforce_create():
    code = request.form.get('worker_code', '').strip().upper()
    if not code:
        code = f"WRK-{int(datetime.now().timestamp()) % 10000:04d}"

    data = {
        'worker_code': code,
        'full_name': request.form.get('full_name'),
        'trade': request.form.get('trade'),
        'daily_rate': request.form.get('daily_rate', 0),
        'phone': request.form.get('phone', ''),
        'assigned_project_id': request.form.get('assigned_project_id') or None,
        'status': request.form.get('status', 'Active'),
        'safety_cert_valid': 1 if request.form.get('safety_cert_valid') else 0
    }
    models.add_workforce(data)
    flash(f"Worker '{data['full_name']}' registered successfully.", "success")
    return redirect(url_for('workforce_list', tab='workers'))


@app.route('/subcontractors/new', methods=['POST'])
def subcontractor_create():
    data = {
        'company_name': request.form.get('company_name'),
        'specialty': request.form.get('specialty'),
        'contact_person': request.form.get('contact_person'),
        'phone': request.form.get('phone'),
        'email': request.form.get('email', ''),
        'contract_value': request.form.get('contract_value', 0),
        'current_project_id': request.form.get('current_project_id') or None,
        'rating': request.form.get('rating', 4.5),
        'status': 'Active'
    }
    models.add_subcontractor(data)
    flash(f"Subcontractor '{data['company_name']}' added.", "success")
    return redirect(url_for('workforce_list', tab='subcontractors'))


# ==========================================
# 6. Site Progress Logs
# ==========================================
@app.route('/site-logs')
def site_logs_list():
    project_id = request.args.get('project_id')
    project_id = int(project_id) if project_id and project_id != 'All' else None

    logs = models.get_site_logs(project_id=project_id)
    projects = models.get_all_projects()

    return render_template(
        'site_logs.html',
        active_page='site_logs',
        logs=logs,
        projects=projects,
        current_project_id=project_id
    )


@app.route('/site-logs/new', methods=['POST'])
def site_log_create():
    project_id = int(request.form.get('project_id'))
    data = {
        'project_id': project_id,
        'log_date': request.form.get('log_date', date.today().isoformat()),
        'weather': request.form.get('weather', 'Sunny'),
        'temp_c': request.form.get('temp_c', 28),
        'manpower_count': request.form.get('manpower_count', 0),
        'summary_of_work': request.form.get('summary_of_work'),
        'delays_or_issues': request.form.get('delays_or_issues', ''),
        'recorded_by': request.form.get('recorded_by')
    }
    models.add_site_log(data)
    flash("Daily site diary log recorded.", "success")

    redirect_to = request.form.get('redirect_to')
    if redirect_to == 'project':
        return redirect(url_for('project_detail', project_id=project_id, tab='logs'))
    return redirect(url_for('site_logs_list'))


# ==========================================
# 7. Safety & Defect Inspections (HSE)
# ==========================================
@app.route('/safety')
def safety_list():
    status_filter = request.args.get('status', 'All')
    project_id = request.args.get('project_id')
    project_id = int(project_id) if project_id and project_id != 'All' else None

    incidents = models.get_safety_incidents(project_id=project_id, status=status_filter)
    projects = models.get_all_projects()

    return render_template(
        'safety.html',
        active_page='safety',
        incidents=incidents,
        projects=projects,
        current_status=status_filter,
        current_project_id=project_id
    )


@app.route('/safety/new', methods=['POST'])
def safety_create():
    project_id = int(request.form.get('project_id'))
    code = f"HSE-{datetime.now().strftime('%Y')}-{int(datetime.now().timestamp()) % 1000:03d}"

    data = {
        'ticket_code': code,
        'project_id': project_id,
        'title': request.form.get('title'),
        'severity': request.form.get('severity', 'Medium'),
        'category': request.form.get('category'),
        'description': request.form.get('description'),
        'corrective_action': request.form.get('corrective_action', ''),
        'reported_date': request.form.get('reported_date', date.today().isoformat())
    }
    models.add_safety_incident(data)
    flash(f"Safety hazard ticket {code} logged.", "warning")

    redirect_to = request.form.get('redirect_to')
    if redirect_to == 'project':
        return redirect(url_for('project_detail', project_id=project_id, tab='safety'))
    return redirect(url_for('safety_list'))


@app.route('/api/safety/<int:incident_id>/resolve', methods=['POST'])
def safety_resolve(incident_id):
    action = request.form.get('corrective_action', 'Corrective action implemented and site re-inspected.')
    models.resolve_safety_incident(incident_id, action)
    flash("Safety incident marked as resolved.", "success")
    return redirect(request.referrer or url_for('safety_list'))


# ==========================================
# 8. Financials & Budget Tracking
# ==========================================
@app.route('/financials')
def financials_view():
    category_filter = request.args.get('category', 'All')
    project_id = request.args.get('project_id')
    project_id = int(project_id) if project_id and project_id != 'All' else None

    breakdown = models.get_financial_breakdown()
    expenses = models.get_expenses(project_id=project_id, category=category_filter)
    projects = models.get_all_projects()
    kpis = models.get_kpis()

    return render_template(
        'financials.html',
        active_page='financials',
        breakdown=breakdown,
        expenses=expenses,
        projects=projects,
        kpis=kpis,
        current_category=category_filter,
        current_project_id=project_id
    )


@app.route('/expenses/new', methods=['POST'])
def expense_create():
    project_id = int(request.form.get('project_id'))
    data = {
        'project_id': project_id,
        'category': request.form.get('category'),
        'amount': float(request.form.get('amount')),
        'invoice_ref': request.form.get('invoice_ref', ''),
        'description': request.form.get('description'),
        'expense_date': request.form.get('expense_date', date.today().isoformat())
    }
    models.add_expense(data)
    flash(f"Expense of ${data['amount']:,.2f} recorded.", "success")

    redirect_to = request.form.get('redirect_to')
    if redirect_to == 'project':
        return redirect(url_for('project_detail', project_id=project_id, tab='financials'))
    return redirect(url_for('financials_view'))


# ==========================================
# 9. Client Transparency Portal
# ==========================================
@app.route('/client-portal')
def client_portal():
    search_code = request.args.get('code', '').strip()
    selected_project = None
    milestones = []
    recent_logs = []

    if search_code:
        selected_project = models.get_project_by_code(search_code)
        if selected_project:
            milestones = models.get_project_milestones(selected_project['id'])
            recent_logs = models.get_site_logs(project_id=selected_project['id'], limit=4)
        else:
            flash(f"No project found matching tracking code '{search_code}'.", "warning")

    public_projects = models.get_all_projects()[:6]

    return render_template(
        'client_portal.html',
        active_page='client_portal',
        search_code=search_code,
        project=selected_project,
        milestones=milestones,
        recent_logs=recent_logs,
        public_projects=public_projects
    )


# ==========================================
# 10. Printable Executive Project Report
# ==========================================
@app.route('/projects/<int:project_id>/report')
def project_report(project_id):
    project = models.get_project_by_id(project_id)
    if not project:
        flash("Project not found.", "danger")
        return redirect(url_for('projects_list'))

    milestones = models.get_project_milestones(project_id)
    site_logs = models.get_site_logs(project_id=project_id, limit=10)
    expenses = models.get_expenses(project_id=project_id)
    safety_incidents = models.get_safety_incidents(project_id=project_id)
    equipment = models.get_all_equipment(project_id=project_id)

    total_spent = sum(e['amount'] for e in expenses)
    remaining = project['total_budget'] - total_spent

    return render_template(
        'report_print.html',
        project=project,
        milestones=milestones,
        site_logs=site_logs,
        expenses=expenses,
        safety_incidents=safety_incidents,
        equipment=equipment,
        total_spent=total_spent,
        remaining=remaining,
        today_date=date.today().strftime("%B %d, %Y")
    )


# Milestone update API
@app.route('/api/milestones/<int:milestone_id>/update', methods=['POST'])
def milestone_update(milestone_id):
    status = request.form.get('status')
    pct = int(request.form.get('completion_pct', 0))
    models.update_milestone_status(milestone_id, status, pct)
    flash("Milestone progress updated.", "success")
    return redirect(request.referrer or url_for('projects_list'))


if __name__ == '__main__':
    print("=========================================================")
    print("  BUILDPULSE - ENTERPRISE CONSTRUCTION MANAGEMENT SYSTEM  ")
    print("  Running at: http://127.0.0.1:5000/                      ")
    print("=========================================================")
    app.run(host='0.0.0.0', port=5000, debug=True)
