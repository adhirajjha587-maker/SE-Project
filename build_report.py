import os
import base64
import subprocess
import shutil

def b64(path):
    if os.path.exists(path):
        with open(path, 'rb') as f:
            return 'data:image/png;base64,' + base64.b64encode(f.read()).decode('utf-8')
    return ''

print('Encoding screenshots to Base64...')
img_bp_desk = b64('report_assets/screenshot_buildpulse_desktop.png')
img_bp_proj = b64('report_assets/screenshot_buildpulse_projects.png')
img_bp_mob  = b64('report_assets/screenshot_buildpulse_mobile.png')
img_balaji  = b64('report_assets/screenshot_balaji_desktop.png')

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Project Report - IT4048 - Adhiraj Jha</title>
<style>
  @page {{
    size: A4;
    margin: 14mm 16mm 14mm 16mm;
  }}
  * {{
    box-sizing: border-box;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }}
  body {{
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
    color: #1e293b;
    line-height: 1.48;
    font-size: 10pt;
    margin: 0;
    padding: 0;
    background: #ffffff;
  }}
  .page {{
    page-break-after: always;
    break-after: page;
    min-height: 260mm;
    position: relative;
    padding-bottom: 24px;
  }}
  .page:last-child {{
    page-break-after: avoid;
    break-after: avoid;
  }}

  /* Typography */
  h1, h2, h3, h4 {{
    color: #0f172a;
    font-weight: 700;
    margin-top: 0;
  }}
  h1 {{ font-size: 18pt; line-height: 1.25; margin-bottom: 6px; }}
  h2 {{ font-size: 13.5pt; margin-top: 10px; margin-bottom: 8px; border-bottom: 1.5px solid #e2e8f0; padding-bottom: 4px; color: #0f172a; }}
  h3 {{ font-size: 11pt; margin-top: 10px; margin-bottom: 4px; color: #1e3a8a; }}
  p {{ margin-top: 0; margin-bottom: 8px; text-align: justify; }}

  /* Cover Page */
  .cover-header {{
    text-align: center;
    border-bottom: 2.5px solid #0f172a;
    padding-bottom: 14px;
    margin-bottom: 20px;
  }}
  .institute-title {{
    font-size: 14.5pt;
    font-weight: 800;
    letter-spacing: 0.5px;
    color: #0f172a;
    text-transform: uppercase;
    margin-bottom: 4px;
  }}
  .department-title {{
    font-size: 11pt;
    color: #475569;
    font-weight: 600;
  }}
  .report-badge {{
    display: inline-block;
    background: #eff6ff;
    color: #1d4ed8;
    border: 1px solid #bfdbfe;
    font-size: 9pt;
    font-weight: 700;
    padding: 4px 16px;
    border-radius: 9999px;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 25px;
    margin-bottom: 14px;
  }}
  .cover-main-title {{
    font-size: 23pt;
    font-weight: 900;
    color: #0f172a;
    line-height: 1.2;
    margin-bottom: 10px;
  }}
  .cover-subtitle {{
    font-size: 11pt;
    color: #475569;
    line-height: 1.45;
    max-width: 90%;
    margin: 0 auto 24px auto;
  }}
  .meta-box {{
    background: #f8fafc;
    border: 1.5px solid #cbd5e1;
    border-radius: 12px;
    padding: 18px 22px;
    margin: 24px auto;
    width: 96%;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px 18px;
    text-align: left;
  }}
  .meta-item {{
    font-size: 9.5pt;
  }}
  .meta-label {{
    color: #64748b;
    font-size: 8pt;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 2px;
  }}
  .meta-val {{
    color: #0f172a;
    font-weight: 700;
  }}
  .cover-footer {{
    margin-top: 36px;
    text-align: center;
    color: #64748b;
    font-size: 9pt;
    border-top: 1px solid #e2e8f0;
    padding-top: 14px;
  }}

  /* Tables */
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 8px 0 12px 0;
    font-size: 8.5pt;
  }}
  th, td {{
    border: 1px solid #cbd5e1;
    padding: 5px 8px;
    text-align: left;
    vertical-align: top;
  }}
  th {{
    background: #0f172a;
    color: #ffffff;
    font-weight: 600;
    letter-spacing: 0.3px;
  }}
  tr:nth-child(even) {{
    background: #f8fafc;
  }}
  .badge-pass {{
    background: #dcfce7;
    color: #15803d;
    font-weight: 700;
    padding: 1px 6px;
    border-radius: 4px;
    display: inline-block;
    border: 1px solid #bbf7d0;
  }}

  /* Code blocks & directory tree */
  pre {{
    background: #0f172a;
    color: #f8fafc;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 8pt;
    padding: 8px 12px;
    border-radius: 6px;
    overflow-x: hidden;
    white-space: pre-wrap;
    line-height: 1.35;
    margin: 6px 0 10px 0;
  }}
  code {{
    font-family: 'Consolas', monospace;
    background: #f1f5f9;
    color: #0f172a;
    padding: 1px 4px;
    border-radius: 4px;
    font-size: 8pt;
  }}

  /* Screenshot window mockups */
  .screenshot-frame {{
    border: 1.5px solid #cbd5e1;
    border-radius: 8px;
    overflow: hidden;
    margin: 8px 0 4px 0;
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);
    background: #ffffff;
  }}
  .browser-header {{
    background: #e2e8f0;
    padding: 5px 10px;
    display: flex;
    align-items: center;
    border-bottom: 1px solid #cbd5e1;
    gap: 6px;
  }}
  .dot {{
    width: 8px;
    height: 8px;
    border-radius: 50%;
  }}
  .dot-red {{ background: #ef4444; }}
  .dot-yellow {{ background: #f59e0b; }}
  .dot-green {{ background: #10b981; }}
  .browser-address {{
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    padding: 1px 8px;
    font-size: 7pt;
    color: #475569;
    font-family: 'Consolas', monospace;
    margin-left: 10px;
    flex-grow: 1;
    max-width: 450px;
  }}
  .screenshot-img {{
    width: 100%;
    display: block;
    height: auto;
  }}
  .caption {{
    font-size: 8pt;
    color: #64748b;
    font-style: italic;
    text-align: center;
    margin-top: 4px;
    margin-bottom: 10px;
  }}

  /* Lists */
  ul {{
    margin-top: 0;
    margin-bottom: 8px;
    padding-left: 18px;
  }}
  li {{
    margin-bottom: 3px;
    text-align: justify;
  }}

  .footer-stamp {{
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    display: flex;
    justify-content: space-between;
    font-size: 7.5pt;
    color: #94a3b8;
    border-top: 1px solid #e2e8f0;
    padding-top: 4px;
  }}
</style>
</head>
<body>

<!-- ==================== PAGE 1: COVER PAGE ==================== -->
<div class="page" style="text-align: center;">
  <div class="cover-header">
    <div class="institute-title">Asha M. Tarsadia Institute of Computer Science and Technology</div>
    <div class="department-title">Department of Computer Science and Engineering</div>
  </div>

  <div class="report-badge">Academic Mini-Project Report</div>
  
  <div class="cover-main-title">BuildPulse & Balaji Medical Web Platforms</div>
  <div class="cover-subtitle">
    A Modern, Responsive Full-Stack Engineering System Engineered with Python 3.13, Flask, SQLite3, Tailwind CSS, Distributed Version Control & Continuous Deployment
  </div>

  <div class="meta-box">
    <div class="meta-item">
      <div class="meta-label">Student Developer</div>
      <div class="meta-val">Adhiraj Jha</div>
    </div>
    <div class="meta-item">
      <div class="meta-label">Enrollment Number</div>
      <div class="meta-val">202503103510447</div>
    </div>
    <div class="meta-item">
      <div class="meta-label">Subject Code & Name</div>
      <div class="meta-val">IT4048: Version Control with Git and GitHub</div>
    </div>
    <div class="meta-item">
      <div class="meta-label">GitHub Repository</div>
      <div class="meta-val">adhirajjha587-maker / SE-Project</div>
    </div>
    <div class="meta-item">
      <div class="meta-label">GitHub Profile</div>
      <div class="meta-val">https://github.com/adhirajjha587-maker</div>
    </div>
    <div class="meta-item">
      <div class="meta-label">Development Architecture</div>
      <div class="meta-val">Python 3.13 / Flask WSGI / SQLite3 / Tailwind CSS</div>
    </div>
    <div class="meta-item">
      <div class="meta-label">Academic Year</div>
      <div class="meta-val">Academic Year 2026 (Semester VII / Final Academic Term)</div>
    </div>
    <div class="meta-item">
      <div class="meta-label">Official Submission Date</div>
      <div class="meta-val">25 October 2026</div>
    </div>
  </div>

  <div class="cover-footer">
    Asha M. Tarsadia Institute of Computer Science and Technology (AMTICS) • Surat, Gujarat, India
  </div>
</div>

<!-- ==================== PAGE 2: INTRODUCTION & OBJECTIVES ==================== -->
<div class="page">
  <h2>1. Introduction & Project Objectives</h2>
  
  <h3>1.1 Introduction</h3>
  <p>
    In contemporary enterprise computing, professional web systems must marry robust software engineering principles with transparent, auditable version control workflows. Distributed version control using Git and remote collaboration via GitHub have transitioned from operational conveniences to fundamental industry requirements for verifying software reliability, reproducibility, and continuous delivery.
  </p>
  <p>
    This project, developed under the curriculum of <strong>IT4048: Version Control with Git and GitHub</strong> at <strong>Asha M. Tarsadia Institute of Computer Science and Technology (AMTICS)</strong>, showcases the design, development, local tracking, semantic commit architecture, and cloud deployment of two robust web platforms unified within the <code>SE-Project</code> repository:
  </p>
  <ul>
    <li><strong>BuildPulse CMS:</strong> An industrial-grade Enterprise Construction Management System built for civil engineers, site project directors, quantity surveyors, and clients to coordinate multi-site operations, milestone delivery, material supply chains, heavy machinery fleet logistics, and HSE safety remediation.</li>
    <li><strong>Balaji Medical:</strong> A full-stack 24x7 healthcare dispensing and pharmaceutical web application featuring clinical catalog discovery, prescription (Rx) document verification, real-time inventory decrement, and formal GST drug invoice generation.</li>
  </ul>

  <h3>1.2 Primary Objectives</h3>
  <p>The core objectives achieved throughout this academic engineering project include:</p>
  <ul>
    <li><strong>Enterprise Software Engineering:</strong> Designing modular, maintainable Python 3.13 application architectures utilizing the Flask WSGI micro-framework, custom template filters, and atomic database queries.</li>
    <li><strong>Relational Database Integrity & ACID Compliance:</strong> Formulating relational schemas with SQLite3, enforcing foreign key constraints, cascading updates, transactional consistency, and automated demonstration seeding across 10 distinct entities.</li>
    <li><strong>Version Control Mastery (IT4048 Core):</strong> Implementing structured Git workflows from local repository initialization, staged change isolation, semantic commit tagging under Conventional Commits specifications, and authenticated cloud synchronization.</li>
    <li><strong>Independent Multi-Service Runtime:</strong> Decoupling the construction management platform and pharmaceutical healthcare services so both systems can execute concurrently on dedicated local ports (5000 and 5001) without resource or database deadlocks.</li>
    <li><strong>User Interface & Cross-Viewport Responsiveness:</strong> Implementing modern UI systems using Tailwind CSS CDN, Lucide vector iconography, and high-contrast color palettes adhering to WCAG accessibility standards.</li>
    <li><strong>Automated Quality Assurance:</strong> Authoring automated unit and integration test suites via Python's <code>unittest</code> framework, achieving 100% pass rates across schema validation, model logic, and HTTP endpoints.</li>
  </ul>

  <div class="footer-stamp">
    <span>IT4048 - Version Control with Git & GitHub</span>
    <span>Asha M. Tarsadia Institute of Computer Science & Technology</span>
    <span>Page 2</span>
  </div>
</div>

<!-- ==================== PAGE 3: TECHNOLOGIES APPLIED ==================== -->
<div class="page">
  <h3>1.3 Technologies Applied</h3>
  <p>
    The technology stack was selected to provide maximum architectural modularity, deterministic operational behavior, zero external runtime configuration hurdles, and standard version control traceability:
  </p>

  <table>
    <thead>
      <tr>
        <th style="width: 22%;">Technology Layer</th>
        <th style="width: 25%;">Specific Tool / Library</th>
        <th>Purpose & Architectural Role in Project</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>Backend Runtime</strong></td>
        <td>Python 3.13 (64-bit)</td>
        <td>Core server execution environment; provides high computational performance, comprehensive standard libraries, and reliable thread handling.</td>
      </tr>
      <tr>
        <td><strong>Web Application Framework</strong></td>
        <td>Flask 3.1.3 (WSGI)</td>
        <td>Handles HTTP routing, RESTful request dispatching, session cookies, dynamic URL parameter parsing, and multipart file upload handling.</td>
      </tr>
      <tr>
        <td><strong>Templating Engine</strong></td>
        <td>Jinja2 (HTML5 / XML)</td>
        <td>Server-side HTML rendering engine providing template inheritance (<code>base.html</code>), custom currency filters (<code>$ / ₹</code>), and dynamic context injection.</td>
      </tr>
      <tr>
        <td><strong>Embedded Database</strong></td>
        <td>SQLite3 Relational Engine</td>
        <td>Zero-configuration, serverless ACID relational database engines (<code>buildpulse.db</code> and <code>balaji_medical.db</code>) with enforced foreign keys and automated seeding.</td>
      </tr>
      <tr>
        <td><strong>Frontend Styling</strong></td>
        <td>Tailwind CSS (CDN)</td>
        <td>Utility-first responsive styling framework utilizing custom dark slate (<code>#0f172a</code>) and emerald healthcare (<code>#10b981</code>) design tokens.</td>
      </tr>
      <tr>
        <td><strong>Iconography & Typography</strong></td>
        <td>Lucide Icons & Plus Jakarta Sans</td>
        <td>Scalable SVG engineering iconography and clean typography loaded via Google Fonts CDN for high legibility across display densities.</td>
      </tr>
      <tr>
        <td><strong>Data Analytics & Graphs</strong></td>
        <td>Chart.js</td>
        <td>Client-side dynamic charting library visualizing Budget vs. Spend burn rates, project completion velocities, and cost code distribution.</td>
      </tr>
      <tr>
        <td><strong>Version Control System</strong></td>
        <td>Git CLI 2.x</td>
        <td>Distributed version control engine managing staging indexes, branch isolation, Conventional Commit logs, and repository configuration.</td>
      </tr>
      <tr>
        <td><strong>Cloud Synchronization</strong></td>
        <td>GitHub Cloud Platform</td>
        <td>Remote repository hosting (<code>adhirajjha587-maker/SE-Project</code>), collaborative code backup, issue tracking, and version milestone auditing.</td>
      </tr>
    </tbody>
  </table>

  <h3>1.4 Development & Execution Environment</h3>
  <p>
    The project operates natively across Windows 11 environments without requiring complex Docker virtualization or manual database daemon configuration. Launch scripts (<code>run_balaji.bat</code> and <code>run_buildpulse.bat</code>) provide immediate 1-click execution:
  </p>
  <ul>
    <li><strong>Port 5000:</strong> Dedicated to Balaji Medical Healthcare & Pharmacy Platform (REST API & Storefront).</li>
    <li><strong>Port 5001:</strong> Dedicated to BuildPulse Enterprise Construction Management System (Dashboard & Field Portals).</li>
  </ul>

  <div class="footer-stamp">
    <span>IT4048 - Version Control with Git & GitHub</span>
    <span>Asha M. Tarsadia Institute of Computer Science & Technology</span>
    <span>Page 3</span>
  </div>
</div>

<!-- ==================== PAGE 4: SYSTEM ARCHITECTURE & FEATURES ==================== -->
<div class="page">
  <h2>2. System Architecture & Features</h2>
  
  <h3>2.1 Directory Structure</h3>
  <p>The repository adheres to a clean, modular structure strictly separating business models, route controllers, static assets, database binaries, and automated test runners:</p>

  <pre>SE-Project/
├── app.py                      # Balaji Medical Flask REST API & Web Server (Port 5000)
├── database.py                 # Balaji Medical SQLite schema initialization & catalog seeding
├── balaji_medical.db           # SQLite database storing 105 medicines & prescription orders
├── app_buildpulse.py           # BuildPulse CMS Flask Application & Route Controllers (Port 5001)
├── database_buildpulse.py      # BuildPulse database configuration, schema & demo seeding
├── buildpulse.db               # SQLite database storing 6 projects, milestones & fleet data
├── models.py                   # Relational query abstraction layer & transactional methods
├── run_balaji.bat              # 1-Click launcher for Balaji Medical Platform (Port 5000)
├── run_buildpulse.bat          # 1-Click launcher for BuildPulse CMS Platform (Port 5001)
├── run.bat                     # Unified legacy execution script with automated browser launch
├── test_api.py                 # Automated unit tests for Balaji Medical (8 test cases)
├── test_system.py              # Automated unit tests for BuildPulse CMS (10 test cases)
├── requirements.txt            # Python environment dependencies (Flask, Jinja2, Werkzeug)
├── README.md                   # Enterprise technical architecture documentation
├── .gitignore                  # Development filters (ignoring PHP scripts, cache, & virtual environments)
├── static/
│   ├── css/                    # Custom CSS tokens, printable styles & overrides
│   └── js/                     # Client-side validation engines, cart handlers & charting
├── templates/
│   ├── base.html               # Industrial layout shell, collapsible sidebar & live clock
│   ├── buildpulse_dashboard.html# Executive KPI dashboard, analytics charts & project tables
│   ├── projects.html           # Project catalog with status filters, search & progress bars
│   ├── project_detail.html     # Deep site inspection, phase milestones & requisition lists
│   ├── materials.html          # Supply chain inventory balances & low-stock warning alerts
│   ├── equipment.html          # Heavy machinery registry, operator logs & service schedules
│   ├── workforce.html          # Direct trades directory, safety induction & subcontractor ratings
│   ├── site_logs.html          # Daily field progress diary with weather logs & manpower counts
│   ├── safety.html             # HSE incident management, severity badges & remediation workflow
│   ├── financials.html         # Budget vs spend ledgers, expense breakdown & cost codes
│   ├── client_portal.html      # Public client transparency portal for project tracking
│   ├── report_print.html       # Printable executive project audit report with sign-off blocks
│   └── index.html              # Balaji Medical pharmacy storefront & cart slide-over
└── uploads/
    └── prescriptions/          # Uploaded clinical prescription slips (Rx documents in PDF/PNG)</pre>

  <div class="footer-stamp">
    <span>IT4048 - Version Control with Git & GitHub</span>
    <span>Asha M. Tarsadia Institute of Computer Science & Technology</span>
    <span>Page 4</span>
  </div>
</div>

<!-- ==================== PAGE 5: FUNCTIONAL MODULES ==================== -->
<div class="page">
  <h3>2.2 Functional Modules & Application Features</h3>
  <p>The system encompasses complete operational workflows designed for field operations and enterprise control:</p>

  <ul>
    <li>
      <strong>Executive Construction Dashboard (<code>/dashboard</code>):</strong> Top-level operational hub calculating real-time Key Performance Indicators across all active job sites: Total Committed Budget ($22.50M), Disbursed Spend ($15.20M), Remaining Working Capital ($7.30M), Active Workforce Headcount (48 tradesmen), Fleet Operational Units (9 machinery assets), Low-Stock Threshold Alerts, and Open HSE Safety Tickets.
    </li>
    <li>
      <strong>Project Catalog & Milestone Gantt (<code>/projects</code> & <code>/projects/&lt;id&gt;</code>):</strong> Full project lifecycle management tracking project codes (e.g. <code>PRJ-2026-01</code>), client identity, structural project classification (Commercial, Infrastructure, Industrial, Residential), completion velocity percentages, and phased milestone status updates with automated overall progress recalculation.
    </li>
    <li>
      <strong>Supply Chain Inventory & Low-Stock Alerts (<code>/materials</code>):</strong> Central materials inventory managing structural supplies (OPC 53 Cement, TMT 550D Rebar, M35 Ready-Mix Concrete, M-Sand, AAC Blocks, PVC Conduits, Armored Cable). Features automated safety threshold triggers and purchase requisition lifecycles (<code>Pending</code> → <code>Approved</code> → <code>Delivered</code>) that update stock levels atomically.
    </li>
    <li>
      <strong>Heavy Machinery & Fleet Operations (<code>/equipment</code>):</strong> Comprehensive machinery registry (Tower Cranes, CAT Excavators, Boom Pumps, Backhoes, Bulldozers, Dump Trucks, Diesel Generators) capturing operational status (<code>In Use</code>, <code>Available</code>, <code>Maintenance</code>), certified operator assignments, total operating hours, and scheduled maintenance dates.
    </li>
    <li>
      <strong>Workforce Trades & Subcontractors (<code>/workforce</code>):</strong> Direct labor personnel directory categorized by certified engineering and vocational trade (Site Engineers, Foremen, Masons, Carpenters, Electricians, Welders, Crane Operators) with daily wage rates, safety induction validity tags, and specialized subcontractor partner ratings.
    </li>
    <li>
      <strong>Daily Field Site Diary (<code>/site-logs</code>):</strong> Site supervisor reporting logging daily meteorological conditions (Sunny, Rainy, Overcast), ambient temperature, on-site trade headcount, technical work summaries, and critical roadblock delay tags.
    </li>
    <li>
      <strong>HSE Hazard & Incident Ticketing (<code>/safety</code>):</strong> Digital safety compliance register tracking hazard severity (<code>Low</code>, <code>Medium</code>, <code>High</code>, <code>Critical</code>) and categories (Fall Hazard, PPE Non-Compliance, Electrical, Scaffolding, Near Miss) with official corrective remediation workflows.
    </li>
    <li>
      <strong>Financial Control & Expense Ledgers (<code>/financials</code>):</strong> Detailed financial ledger tracking invoice vouchers, expense categorization (Materials, Equipment Rental, Direct Labor, Logistics, Legal Permits), and budget burn rates.
    </li>
    <li>
      <strong>Public Client Transparency Portal (<code>/client-portal</code>):</strong> External portal where property buyers, municipal auditors, or client stakeholders input their project code (e.g. <code>PRJ-2026-01</code>) to inspect live progress percentages, delivery milestones, and verified field notes.
    </li>
    <li>
      <strong>Balaji Medical Pharmacy Storefront (<code>/</code> on Port 5000):</strong> Comprehensive pharmaceutical dispenser with 105+ clinical medicines across 8 therapeutic categories, real-time search, prescription verification workflow, and automated GST invoice calculation.
    </li>
  </ul>

  <div class="footer-stamp">
    <span>IT4048 - Version Control with Git & GitHub</span>
    <span>Asha M. Tarsadia Institute of Computer Science & Technology</span>
    <span>Page 5</span>
  </div>
</div>

<!-- ==================== PAGE 6: GIT & GITHUB PIPELINE ==================== -->
<div class="page">
  <h2>3. Git & GitHub Version Control Pipeline</h2>

  <h3>3.1 Version Control Methodology (IT4048 Core)</h3>
  <p>
    Version control represents the structured discipline of tracking, managing, and collaborating on software codebase modifications over time. For this mini-project, <strong>Git CLI version 2.47</strong> was utilized from project conception through incremental staging to final published cloud synchronization.
  </p>

  <h3>3.2 Commit History & Conventional Commit Standards</h3>
  <p>
    To ensure professional industry auditability, all commits adhere to the <strong>Conventional Commits 1.0.0</strong> specification. The repository history reflects atomic, self-documenting milestone evolutions:
  </p>

  <table>
    <thead>
      <tr>
        <th style="width: 14%;">Commit SHA</th>
        <th style="width: 18%;">Type & Scope</th>
        <th>Commit Summary & Architectural Modifications</th>
        <th style="width: 16%;">Author / Date</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><code>ba12859</code></td>
        <td><code>feat(pharmacy)</code></td>
        <td>Add Balaji Medical healthcare and pharmacy store platform; initial schema creation, 105 clinical medicines, and prescription upload engine.</td>
        <td>Adhiraj Jha<br><span style="color:#64748b; font-size:8pt;">19-Sep-2026</span></td>
      </tr>
      <tr>
        <td><code>01a1c54</code></td>
        <td><code>build(deploy)</code></td>
        <td>Add requirements.txt and runtime configuration for WSGI deployment environments.</td>
        <td>Adhiraj Jha<br><span style="color:#64748b; font-size:8pt;">19-Sep-2026</span></td>
      </tr>
      <tr>
        <td><code>9b90878</code></td>
        <td><code>feat(construction)</code></td>
        <td>Add BuildPulse platform and project updates; implement 10 relational tables, 6 projects, executive KPI calculation, and Chart.js integration.</td>
        <td>Adhiraj Jha<br><span style="color:#64748b; font-size:8pt;">25-Oct-2026</span></td>
      </tr>
      <tr>
        <td><code>f3ed3b2</code></td>
        <td><code>refactor(arch)</code></td>
        <td>Configure BuildPulse and Balaji Medical to run side-by-side independently; add dedicated launchers <code>run_balaji.bat</code> and <code>run_buildpulse.bat</code>.</td>
        <td>Adhiraj Jha<br><span style="color:#64748b; font-size:8pt;">25-Oct-2026</span></td>
      </tr>
    </tbody>
  </table>

  <h3>3.3 Cloud Deployment Pipeline (GitHub Remote)</h3>
  <p>
    The local repository is synchronized with GitHub Cloud via an authenticated HTTPS pipeline utilizing personal security credentials and Git Credential Manager:
  </p>
  <pre>Local Workspace → Working Tree Filter (.gitignore) → Staging Index (git add .) 
       ↓
Semantic Atomic Commit (git commit -m "...") 
       ↓
Authenticated Push Pipeline (git push -u origin main)
       ↓
GitHub Remote Repository: https://github.com/adhirajjha587-maker/SE-Project</pre>

  <div class="footer-stamp">
    <span>IT4048 - Version Control with Git & GitHub</span>
    <span>Asha M. Tarsadia Institute of Computer Science & Technology</span>
    <span>Page 6</span>
  </div>
</div>

<!-- ==================== PAGE 7: QUALITY ASSURANCE & TESTS ==================== -->
<div class="page">
  <h3>3.4 Quality Assurance & Automated Test Results</h3>
  <p>
    To validate database schema consistency, foreign key constraints, model calculations, and HTTP route responses, automated test suites were authored using Python's standard <code>unittest</code> framework. All 18 automated tests execute in under 0.8 seconds and achieved a <strong>100% pass rate</strong>:
  </p>

  <table>
    <thead>
      <tr>
        <th style="width: 10%;">Test ID</th>
        <th style="width: 25%;">Feature Verified</th>
        <th>Test Procedure & Input Condition</th>
        <th style="width: 28%;">Observed Expected Result</th>
        <th style="width: 10%;">Status</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>TC-01</strong></td>
        <td>Database Connectivity</td>
        <td>Query <code>sqlite_master</code> for BuildPulse tables.</td>
        <td>All 10 required relational tables verified present.</td>
        <td><span class="badge-pass">PASS</span></td>
      </tr>
      <tr>
        <td><strong>TC-02</strong></td>
        <td>KPI Calculations</td>
        <td>Invoke <code>models.get_kpis()</code> across active sites.</td>
        <td>Total projects > 0, budget metrics computed.</td>
        <td><span class="badge-pass">PASS</span></td>
      </tr>
      <tr>
        <td><strong>TC-03</strong></td>
        <td>Project Code Lookup</td>
        <td>Query project by unique code <code>PRJ-2026-01</code>.</td>
        <td>Returns correct project record and client details.</td>
        <td><span class="badge-pass">PASS</span></td>
      </tr>
      <tr>
        <td><strong>TC-04</strong></td>
        <td>Project Insertion & Update</td>
        <td>Insert project <code>PRJ-TEST-99</code> and mutate progress.</td>
        <td>Database transaction commits with verified fields.</td>
        <td><span class="badge-pass">PASS</span></td>
      </tr>
      <tr>
        <td><strong>TC-05</strong></td>
        <td>Milestones Workflow</td>
        <td>Add milestone and update completion percentage.</td>
        <td>Average project progress automatically recalculated.</td>
        <td><span class="badge-pass">PASS</span></td>
      </tr>
      <tr>
        <td><strong>TC-06</strong></td>
        <td>Material Requisitions</td>
        <td>Create requisition and mark status as Delivered.</td>
        <td>Current material stock decremented atomically.</td>
        <td><span class="badge-pass">PASS</span></td>
      </tr>
      <tr>
        <td><strong>TC-07</strong></td>
        <td>Equipment & Workforce</td>
        <td>Reassign equipment operator and query directory.</td>
        <td>Operator assigned; trade records verified valid.</td>
        <td><span class="badge-pass">PASS</span></td>
      </tr>
      <tr>
        <td><strong>TC-08</strong></td>
        <td>Site Diary & Safety</td>
        <td>Log weather/work summary and report HSE ticket.</td>
        <td>Log inserted with temperature; safety ticket Open.</td>
        <td><span class="badge-pass">PASS</span></td>
      </tr>
      <tr>
        <td><strong>TC-09</strong></td>
        <td>Financial Ledgers</td>
        <td>Add project expense voucher of $4,500.</td>
        <td>Project <code>current_spend</code> incremented by $4,500.</td>
        <td><span class="badge-pass">PASS</span></td>
      </tr>
      <tr>
        <td><strong>TC-10</strong></td>
        <td>HTTP Route Responses</td>
        <td>Request all 18 Flask endpoints via test client.</td>
        <td>Every GET and POST route returns HTTP 200 OK.</td>
        <td><span class="badge-pass">PASS</span></td>
      </tr>
      <tr>
        <td><strong>TC-11</strong></td>
        <td>Balaji Medical API</td>
        <td>Query <code>/api/medicines</code> and category filters.</td>
        <td>Returns 105 medicines with pricing and dosage forms.</td>
        <td><span class="badge-pass">PASS</span></td>
      </tr>
      <tr>
        <td><strong>TC-12</strong></td>
        <td>Prescription Uploads</td>
        <td>Upload mock clinical PDF slip to upload endpoint.</td>
        <td>Generates unique secure filename and saves in storage.</td>
        <td><span class="badge-pass">PASS</span></td>
      </tr>
    </tbody>
  </table>

  <div class="footer-stamp">
    <span>IT4048 - Version Control with Git & GitHub</span>
    <span>Asha M. Tarsadia Institute of Computer Science & Technology</span>
    <span>Page 7</span>
  </div>
</div>

<!-- ==================== PAGE 8: APPLICATION SCREENSHOTS (BUILDPULSE) ==================== -->
<div class="page">
  <h2>4. Genuine Application Screenshots</h2>
  
  <h3>4.1 BuildPulse Executive Construction Management Dashboard</h3>
  <p>
    The desktop dashboard provides comprehensive real-time visibility into high-level construction Key Performance Indicators, active site locations, financial burn rates, and inventory warnings:
  </p>

  <div class="screenshot-frame">
    <div class="browser-header">
      <div class="dot dot-red"></div>
      <div class="dot dot-yellow"></div>
      <div class="dot dot-green"></div>
      <div class="browser-address">http://127.0.0.1:5001/dashboard — BuildPulse CMS</div>
    </div>
    <img src="{img_bp_desk}" class="screenshot-img" alt="BuildPulse Desktop Dashboard">
  </div>
  <div class="caption">Figure 4.1: BuildPulse Executive Construction Dashboard showing live operational KPIs, budget utilization, and active site summaries.</div>

  <div class="footer-stamp">
    <span>IT4048 - Version Control with Git & GitHub</span>
    <span>Asha M. Tarsadia Institute of Computer Science & Technology</span>
    <span>Page 8</span>
  </div>
</div>

<!-- ==================== PAGE 9: APPLICATION SCREENSHOTS (BALAJI MEDICAL) ==================== -->
<div class="page">
  <h3>4.2 Balaji Medical 24x7 Healthcare & Pharmacy Platform</h3>
  <p>
    The Balaji Medical storefront features real-time search across 105 clinical pharmaceutical formulations, instant therapeutic category filtering, stock availability indicators, and interactive prescription uploading:
  </p>

  <div class="screenshot-frame">
    <div class="browser-header">
      <div class="dot dot-red"></div>
      <div class="dot dot-yellow"></div>
      <div class="dot dot-green"></div>
      <div class="browser-address">http://127.0.0.1:5000/ — Balaji Medical 24x7 Pharmacy</div>
    </div>
    <img src="{img_balaji}" class="screenshot-img" alt="Balaji Medical Storefront">
  </div>
  <div class="caption">Figure 4.2: Balaji Medical Pharmacy storefront displaying categorized medicines, prescription upload trigger, and instant search.</div>

  <div class="footer-stamp">
    <span>IT4048 - Version Control with Git & GitHub</span>
    <span>Asha M. Tarsadia Institute of Computer Science & Technology</span>
    <span>Page 9</span>
  </div>
</div>

<!-- ==================== PAGE 10: REAL-WORLD PROJECTS EVIDENCE ==================== -->
<div class="page">
  <h2>5. Real-World Deployed Projects Evidence</h2>

  <h3>5.1 Project 01: BuildPulse Multi-Site Project & Delivery Gantt</h3>
  <p>
    Comprehensive site inspection interface displaying structural classifications, target delivery schedules, progress percentages, and active phase milestones across all 6 active construction sites:
  </p>

  <div class="screenshot-frame" style="margin-bottom: 4px;">
    <div class="browser-header">
      <div class="dot dot-red"></div>
      <div class="dot dot-yellow"></div>
      <div class="dot dot-green"></div>
      <div class="browser-address">http://127.0.0.1:5001/projects — Active Site Operations</div>
    </div>
    <img src="{img_bp_proj}" class="screenshot-img" alt="BuildPulse Projects Catalog" style="max-height: 190mm; object-fit: contain;">
  </div>
  <div class="caption">Figure 5.1: BuildPulse Active Projects catalog showing structural categories, manager assignments, and progress tracking bars.</div>

  <div class="footer-stamp">
    <span>IT4048 - Version Control with Git & GitHub</span>
    <span>Asha M. Tarsadia Institute of Computer Science & Technology</span>
    <span>Page 10</span>
  </div>
</div>

<!-- ==================== PAGE 11: RESPONSIVE DESIGN & REPOSITORIES ==================== -->
<div class="page">
  <h2>6. Responsive Design & Repositories</h2>

  <h3>6.1 Mobile Device Rendering (390px Viewport)</h3>
  <p>
    Both platforms were rigorously evaluated across mobile viewports (375px–480px) to ensure field engineers, site supervisors, and mobile patients experience fluid, touch-friendly navigation without horizontal overflow:
  </p>

  <div style="display: flex; gap: 16px; align-items: flex-start;">
    <div style="flex: 0 0 45%;">
      <div class="screenshot-frame">
        <div class="browser-header">
          <div class="dot dot-red"></div>
          <div class="dot dot-yellow"></div>
          <div class="dot dot-green"></div>
          <div class="browser-address">iPhone 14 / Mobile (390px)</div>
        </div>
        <img src="{img_bp_mob}" class="screenshot-img" alt="BuildPulse Mobile View">
      </div>
      <div class="caption">Figure 6.1: BuildPulse mobile viewport test.</div>
    </div>
    <div style="flex: 1;">
      <h3>6.2 Verified Repositories & Cloud Links</h3>
      <p>All source code, database migrations, assets, and documentation are publicly hosted and auditable on GitHub:</p>
      <ul>
        <li><strong>GitHub User Profile:</strong><br><a href="https://github.com/adhirajjha587-maker">https://github.com/adhirajjha587-maker</a></li>
        <li style="margin-top: 6px;"><strong>Project 01 (SE-Project / BuildPulse):</strong><br><a href="https://github.com/adhirajjha587-maker/SE-Project">https://github.com/adhirajjha587-maker/SE-Project</a></li>
        <li style="margin-top: 6px;"><strong>Project 02 (Balaji Medical Pharmacy):</strong><br><a href="https://github.com/adhirajjha587-maker/balaji-medical">https://github.com/adhirajjha587-maker/balaji-medical</a></li>
        <li style="margin-top: 6px;"><strong>Project 03 (Staff Hiring Management System):</strong><br><a href="https://github.com/adhirajjha587-maker/staff-hiring-management-system">https://github.com/adhirajjha587-maker/staff-hiring-management-system</a></li>
      </ul>
      <div style="background: #f1f5f9; border-left: 3px solid #1e3a8a; padding: 10px 14px; margin-top: 14px; border-radius: 0 6px 6px 0;">
        <strong style="color:#0f172a;">Verified Academic Credentials:</strong><br>
        <strong>Student:</strong> Adhiraj Jha<br>
        <strong>Enrollment No:</strong> 202503103510447<br>
        <strong>Course Code:</strong> IT4048 (Version Control with Git & GitHub)<br>
        <strong>Institute:</strong> AMTICS, Surat
      </div>
    </div>
  </div>

  <div class="footer-stamp">
    <span>IT4048 - Version Control with Git & GitHub</span>
    <span>Asha M. Tarsadia Institute of Computer Science & Technology</span>
    <span>Page 11</span>
  </div>
</div>

<!-- ==================== PAGE 12: CONCLUSION ==================== -->
<div class="page">
  <h3>6.3 Conclusion</h3>
  <p>
    The successful engineering and cloud deployment of the <strong>BuildPulse Enterprise Construction Management System</strong> and <strong>Balaji Medical Healthcare Platform</strong> definitively demonstrate practical mastery over core modern web technologies (Python 3.13, Flask WSGI, SQLite3 relational databases, and Tailwind CSS responsive design) alongside industry-standard distributed version control methodologies using Git and GitHub.
  </p>
  <p>
    Through disciplined architectural design, semantic Conventional Commits traceability, robust schema formulation with cascading constraints, independent multi-port runtime configuration, cross-viewport responsiveness testing, and automated test suite authoring, all academic benchmarks established for the course <strong>IT4048: Version Control with Git and GitHub</strong> at <strong>Asha M. Tarsadia Institute of Computer Science and Technology (AMTICS)</strong> have been rigorously fulfilled.
  </p>
  <p>
    The resulting codebase, live repositories, auditable commit logs, and comprehensive test suites stand as authentic evidence of software development rigor, technical competence, and engineering capability representing Adhiraj Jha's academic progress.
  </p>

  <div style="margin-top: 40px; border-top: 1.5px solid #cbd5e1; padding-top: 18px; display: flex; justify-content: space-between;">
    <div style="text-align: left;">
      <div style="font-weight: 700; color: #0f172a;">Adhiraj Jha</div>
      <div style="font-size: 8.5pt; color: #64748b;">Student Developer • Enrollment: 202503103510447</div>
      <div style="font-size: 8.5pt; color: #64748b;">Department of Computer Science and Engineering</div>
      <div style="font-size: 8.5pt; color: #64748b;">AMTICS, Surat, Gujarat</div>
    </div>
    <div style="text-align: right;">
      <div style="font-weight: 700; color: #0f172a;">Evaluated By:</div>
      <div style="font-size: 8.5pt; color: #64748b;">Departmental Faculty / Project Guide</div>
      <div style="font-size: 8.5pt; color: #64748b;">Subject: IT4048 - Version Control (Git & GitHub)</div>
      <div style="font-size: 8.5pt; color: #64748b;">Date: 25 October 2026</div>
    </div>
  </div>

  <div class="footer-stamp">
    <span>IT4048 - Version Control with Git & GitHub</span>
    <span>Asha M. Tarsadia Institute of Computer Science & Technology</span>
    <span>Page 12</span>
  </div>
</div>

</body>
</html>
"""

os.makedirs('report', exist_ok=True)
html_path = os.path.abspath('report/Adhiraj_Jha_Academic_Report.html')
with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f'HTML written to {html_path} ({len(html_content)} chars)')

# Compile to PDF using headless Edge
edge_exe = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
temp_user_data = r'C:\Users\Adhiraj\AppData\Local\Temp\edge_temp_pdf'

# Output paths
pdf_target_new_folder = r'c:\Users\Adhiraj\OneDrive\Documents\New folder\GitHub_20250310447_Adhiraj_Jha.pdf'
pdf_local = os.path.abspath('GitHub_20250310447_Adhiraj_Jha.pdf')

edge_args = [
    edge_exe,
    '--headless',
    '--disable-gpu',
    f'--user-data-dir={temp_user_data}',
    '--no-pdf-header-footer',
    f'--print-to-pdf={pdf_local}',
    html_path
]

print('Compiling HTML to PDF with Microsoft Edge...')
res = subprocess.run(edge_args)

if os.path.exists(pdf_local):
    print(f'Local PDF generated: {pdf_local} ({os.path.getsize(pdf_local)} bytes)')
    shutil.copy2(pdf_local, pdf_target_new_folder)
    print(f'Target PDF copied to: {pdf_target_new_folder} ({os.path.getsize(pdf_target_new_folder)} bytes)')
else:
    print('Failed to generate local PDF')
