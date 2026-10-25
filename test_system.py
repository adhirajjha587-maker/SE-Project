"""
BuildPulse - Automated Test Suite
Validates database queries, model methods, and all Flask HTTP routes.
"""

import unittest
from datetime import date
from app import app
import models
from database import get_db_connection, init_db


class BuildPulseTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db(force_reseed=False)
        cls.client = app.test_client()

    def test_01_database_connectivity_and_tables(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row['name'] for row in cursor.fetchall()]
        conn.close()

        required_tables = [
            'projects', 'milestones', 'materials', 'material_requisitions',
            'equipment', 'workforce', 'subcontractors', 'site_logs',
            'safety_incidents', 'expenses'
        ]
        for tbl in required_tables:
            self.assertIn(tbl, tables, f"Missing table: {tbl}")

    def test_02_kpis_calculation(self):
        kpis = models.get_kpis()
        self.assertGreater(kpis['total_projects'], 0)
        self.assertGreater(kpis['total_budget'], 0)
        self.assertGreater(kpis['active_workforce_count'], 0)
        self.assertIsInstance(kpis['remaining_budget'], (int, float))

    def test_03_projects_query_and_code_lookup(self):
        projects = models.get_all_projects()
        self.assertGreaterEqual(len(projects), 5)

        # Test code lookup
        p1 = models.get_project_by_code("PRJ-2026-01")
        self.assertIsNotNone(p1)
        self.assertEqual(p1['code'], "PRJ-2026-01")

        # Test id lookup
        p_by_id = models.get_project_by_id(p1['id'])
        self.assertEqual(p_by_id['name'], p1['name'])

    def test_04_create_and_update_project(self):
        new_project_data = {
            'code': 'PRJ-TEST-99',
            'name': 'Test Aerocity Terminal Extension',
            'client_name': 'Test Aviation Authority',
            'project_type': 'Infrastructure',
            'location': 'Terminal 4, New Delhi',
            'manager_name': 'Er. Test Engineer',
            'start_date': '2026-05-01',
            'target_completion': '2027-10-31',
            'total_budget': 15000000.0,
            'current_spend': 0.0,
            'status': 'In Progress',
            'progress_pct': 10,
            'description': 'Automated test project suite'
        }
        new_id = models.create_project(new_project_data)
        self.assertIsInstance(new_id, int)

        fetched = models.get_project_by_id(new_id)
        self.assertEqual(fetched['code'], 'PRJ-TEST-99')

        # Update test
        new_project_data['name'] = 'Test Aerocity Terminal Phase 2'
        new_project_data['progress_pct'] = 25
        models.update_project(new_id, new_project_data)

        updated = models.get_project_by_id(new_id)
        self.assertEqual(updated['name'], 'Test Aerocity Terminal Phase 2')
        self.assertEqual(updated['progress_pct'], 25)

    def test_05_milestones_workflow(self):
        ms_id = models.add_milestone({
            'project_id': 1,
            'phase_name': 'Phase 9 - Quality Testing',
            'title': 'Core wall ultrasound structural integrity test',
            'due_date': '2026-12-15',
            'status': 'Pending',
            'completion_pct': 0
        })
        self.assertIsInstance(ms_id, int)

        models.update_milestone_status(ms_id, 'Completed', 100)
        milestones = models.get_project_milestones(1)
        updated_ms = next((m for m in milestones if m['id'] == ms_id), None)
        self.assertIsNotNone(updated_ms)
        self.assertEqual(updated_ms['status'], 'Completed')
        self.assertEqual(updated_ms['completion_pct'], 100)

    def test_06_material_requisitions_lifecycle(self):
        initial_materials = models.get_all_materials()
        mat1 = initial_materials[0]
        initial_stock = mat1['current_stock']

        # Create requisition
        req_id = models.create_requisition({
            'requisition_code': 'REQ-TEST-001',
            'project_id': 1,
            'material_id': mat1['id'],
            'quantity': 50.0,
            'requested_by': 'Test Foreman',
            'approval_notes': 'Automated test requisition'
        })
        self.assertIsInstance(req_id, int)

        # Approve
        models.update_requisition_status(req_id, 'Approved', 'Approved in test')

        # Deliver (should increment stock by 50)
        models.update_requisition_status(req_id, 'Delivered', 'Delivered to yard')
        refreshed_mat = next(m for m in models.get_all_materials() if m['id'] == mat1['id'])
        self.assertEqual(refreshed_mat['current_stock'], initial_stock + 50.0)

    def test_07_equipment_and_workforce(self):
        equipment = models.get_all_equipment()
        self.assertGreater(len(equipment), 0)

        # Update equipment status
        eq = equipment[0]
        models.update_equipment(eq['id'], 'Available', None, 'Spare Operator')

        workforce = models.get_all_workforce()
        self.assertGreater(len(workforce), 0)

    def test_08_site_logs_and_safety_incidents(self):
        # Add site log
        log_id = models.add_site_log({
            'project_id': 1,
            'log_date': date.today().isoformat(),
            'weather': 'Sunny',
            'temp_c': 29,
            'manpower_count': 55,
            'summary_of_work': 'Completed automated testing log',
            'delays_or_issues': 'None',
            'recorded_by': 'Test Supervisor'
        })
        self.assertIsInstance(log_id, int)

        # Add safety incident
        inc_id = models.add_safety_incident({
            'ticket_code': 'HSE-TEST-01',
            'project_id': 1,
            'title': 'Test Hazard: Loose wiring',
            'severity': 'Medium',
            'category': 'Electrical',
            'description': 'Temporary wire unshielded',
            'reported_date': date.today().isoformat()
        })
        self.assertIsInstance(inc_id, int)

        # Resolve safety incident
        models.resolve_safety_incident(inc_id, 'Installed rubber safety shield.')
        inc = next(i for i in models.get_safety_incidents(1) if i['id'] == inc_id)
        self.assertEqual(inc['status'], 'Resolved')

    def test_09_expenses_and_financials(self):
        p1 = models.get_project_by_id(1)
        initial_spend = p1['current_spend']

        models.add_expense({
            'project_id': 1,
            'category': 'Materials',
            'amount': 25000.0,
            'invoice_ref': 'INV-TEST-EXP',
            'description': 'Test cement order payment'
        })

        p1_refreshed = models.get_project_by_id(1)
        self.assertEqual(p1_refreshed['current_spend'], initial_spend + 25000.0)

        breakdown = models.get_financial_breakdown()
        self.assertGreater(len(breakdown['by_category']), 0)
        self.assertGreater(len(breakdown['project_financials']), 0)

    def test_10_http_views_get_responses(self):
        routes = [
            '/',
            '/dashboard',
            '/projects',
            '/projects/1',
            '/projects/1?tab=milestones',
            '/projects/1?tab=materials',
            '/projects/1?tab=equipment',
            '/projects/1?tab=workforce',
            '/projects/1?tab=logs',
            '/projects/1?tab=safety',
            '/projects/1?tab=financials',
            '/materials',
            '/materials?tab=requisitions',
            '/equipment',
            '/workforce',
            '/site-logs',
            '/safety',
            '/financials',
            '/client-portal',
            '/client-portal?code=PRJ-2026-01',
            '/projects/1/report'
        ]

        for route in routes:
            resp = self.client.get(route)
            self.assertEqual(resp.status_code, 200, f"Route {route} returned status {resp.status_code}")
            # Ensure HTML content is rendered
            self.assertIn(b'BUILDPULSE', resp.data)


if __name__ == '__main__':
    unittest.main()
