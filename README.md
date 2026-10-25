# BuildPulse - Enterprise Construction Management System (CMS)

A full-stack, responsive construction management web platform engineered in **Python 3.13**, **Flask**, **SQLite3**, and **Tailwind CSS**. Built for civil engineers, site project directors, quantity surveyors, safety officers, and clients to streamline site operations, resource allocation, inventory supply chain, financial control, and project delivery.

---

## 🏗️ System Architecture & Stack

| Layer | Technology | Details |
|---|---|---|
| **Backend Runtime** | **Python 3.13 / Flask** | Lightweight, modular Python application with Jinja2 templating, custom currency/date filters, and RESTful API endpoints. |
| **Database** | **SQLite3 (`buildpulse.db`)** | Embedded ACID relational database with foreign key constraints, cascading updates, and automated seeding. Zero external database configuration required. |
| **Frontend Framework** | **Tailwind CSS (CDN)** | Utility-first responsive design featuring industrial dark slate (`#0f172a`), safety amber (`#f59e0b`), and crisp status indicators. |
| **Icons & Typography** | **Lucide Icons & Google Fonts** | Vector engineering iconography and Plus Jakarta Sans typography. |
| **Analytics & Visuals** | **Chart.js** | Dynamic client-side graphs for Budget vs. Spend burn rates, project progress velocities, and cost code distributions. |
| **Reporting & Export** | **Print CSS & HTML5** | High-definition printable Executive Progress Audit Reports with printable letterhead, signature blocks, and financial statements. |

---

## 🗄️ Relational Database Schema (`buildpulse.db`)

```
projects (id, code, name, client_name, project_type, location, manager_name,
          start_date, target_completion, total_budget, current_spend, status,
          progress_pct, description, banner_url, created_at)
     │
     ├──< milestones (id, project_id, phase_name, title, due_date, status, completion_pct)
     │
     ├──< material_requisitions (id, requisition_code, project_id, material_id,
     │                          quantity, requested_by, status, request_date, approval_notes)
     │
     ├──< equipment (id, equipment_code, name, type, current_project_id, operator_name,
     │               status, hours_operated, next_service_date)
     │
     ├──< workforce (id, worker_code, full_name, trade, daily_rate, phone,
     │               assigned_project_id, status, safety_cert_valid)
     │
     ├──< subcontractors (id, company_name, specialty, contact_person, phone,
     │                    email, contract_value, current_project_id, rating, status)
     │
     ├──< site_logs (id, project_id, log_date, weather, temp_c, manpower_count,
     │               summary_of_work, delays_or_issues, recorded_by, created_at)
     │
     ├──< safety_incidents (id, ticket_code, project_id, title, severity, category,
     │                      description, corrective_action, status, reported_date, resolved_date)
     │
     └──< expenses (id, project_id, category, amount, invoice_ref, description, expense_date)

materials (id, item_code, name, category, unit, unit_cost, current_stock, min_threshold, location)
```

---

## 🚀 Key Modules & Capabilities

### 1. 📊 Executive Operations Command Center (`/dashboard`)
- Real-time KPI summary widgets: Active Construction Sites, Total Capital Committed, Material Inventory Valuation, Workforce On-Site, and Open Safety Incidents.
- Interactive Chart.js graphs:
  - **Budget vs. Current Spend**: Visual burn rate across active civil projects.
  - **Cost Code Distribution**: Breakdown by Materials, Direct Labor, Equipment Lease, Subcontractor Packages, and Statutory Permits.
- Quick Status Feed: Latest field diary logs, pending material requisitions, and critical low-stock warnings.

### 2. 🏢 Projects Portfolio & Command Center (`/projects` & `/projects/<id>`)
- Portfolio directory with search and filtering by project type (*Commercial, Residential, Infrastructure, Industrial*) and operational status (*In Progress, Planning, Completed, On Hold*).
- Tabbed Project Command Center:
  - **Overview**: Engineering scope, key milestones, budget spend utilization bar, and site leadership details.
  - **WBS & Milestones**: Phase tracking (Substructure, Superstructure, MEP, Façade, Handover) with progress sliders and status toggles.
  - **Requisitions**: Indents filed specifically for this site with 1-click approvals.
  - **Machinery Fleet**: Heavy machinery units currently deployed at this site.
  - **Workforce**: Skilled trades and laborers allocated to the project.
  - **Daily Site Diary**: Chronological field diary entries with weather, manpower count, and work executed.
  - **HSE & Safety**: Hazard tickets with severity levels and corrective action tracking.
  - **Cost Ledger**: Disbursed expense vouchers against the project budget.

### 3. 📦 Material Stock & Procurement (`/materials`)
- Master inventory catalog of materials (*OPC 53 Cement, TMT 550D Rebar, M35 Ready-Mix Concrete, M-Sand, AAC Blocks, PVC Conduits, Armored Cable*).
- Automated Low-Stock Alert System with visual warnings when stock falls below safety buffer thresholds.
- Complete purchase requisition lifecycle: `Pending` ➔ `Approved` ➔ `Delivered` *(automatically updates inventory balances)*.

### 4. 🚜 Heavy Machinery & Fleet Operations (`/equipment`)
- Registry of heavy machinery (*Liebherr Tower Cranes, CAT Hydraulic Excavators, Schwing Stetter Boom Pumps, JCB Backhoes, Komatsu Bulldozers, Volvo Dump Trucks, Diesel Generators*).
- Real-time tracking of operational status (*In Use, Available, Maintenance, Overhaul*), certified operators, operating hours, and service dates.

### 5. 👷 Workforce Trades & Specialist Subcontractors (`/workforce`)
- Direct labor directory categorized by trade (*Site Engineers, Foremen, Masons, Carpenters, Electricians, Welders, Crane Operators*).
- Safety induction compliance badges and daily wage calculation.
- Subcontractor partner registry with performance ratings (1–5 stars), trade specialties (*Glazing, Piling, HVAC, Fire Protection*), and contract values.

### 6. 📝 Daily Site Diary & Field Progress (`/site-logs`)
- Detailed field reports capturing daily weather (*Sunny, Rainy, Windy, Overcast*), temperature, on-site manpower counts, technical work summary, and delay roadblocks.
- Filterable by specific construction site.

### 7. 🛡️ Health, Safety & Environmental (HSE) Compliance (`/safety`)
- Digital hazard reporting and ticket tracking with severity ratings (*Low, Medium, High, Critical*) and categories (*Fall Hazard, PPE Non-Compliance, Electrical, Scaffolding, Near Miss, Material Defect*).
- Remediation workflow: log corrective actions and officially resolve safety tickets.

### 8. 💰 Budgeting, Cost Codes & Expenses (`/financials`)
- Comprehensive financial variance tracking: Total Budget vs. Disbursed Spend vs. Remaining Working Capital.
- Categorized expense ledger with invoice references and transaction descriptions.

### 9. 🌐 Public Client Transparency Portal (`/client-portal`)
- Dedicated external portal where clients, property buyers, or authorities can input their project code (e.g. `PRJ-2026-01`) to inspect real-time progress percentages, milestone delivery timelines, and official site updates.

### 10. 🖨️ Printable Executive Project Audit Report (`/projects/<id>/report`)
- Clean, corporate-styled printable project report ready for board presentations or municipal audits with dedicated engineer, safety officer, and client sign-off blocks.

---

## ⚡ How to Run the Application

### Option 1: 1-Click Launch (Windows)
Double-click **`run.bat`** in the project folder. The batch file will:
1. Verify Python 3.
2. Initialize and seed `buildpulse.db` if not already created.
3. Automatically launch your browser at `http://127.0.0.1:5000/`.
4. Keep the development server running with live reloading.

### Option 2: Command Line (Windows / macOS / Linux)
```bash
# 1. Initialize and seed database
py database.py

# 2. Run the Flask server
py app.py
```
Open **`http://127.0.0.1:5000/`** in your browser.

---

## 🧪 Automated Testing
Run the complete automated unit and integration test suite:
```bash
py test_system.py
```
Validates database schema, foreign key constraints, model transactions, stock deductions, and all HTTP GET and POST route endpoints.
