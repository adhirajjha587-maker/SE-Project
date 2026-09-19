"""
Balaji Medical - Automated Test Suite
Verifies all REST API endpoints, order workflows, and database updates.
"""

import os
import io
import json
import unittest
from app import app
import database

class BalajiMedicalTestCase(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()
        # Initialize database
        database.init_db()

    def test_01_index_page(self):
        """Test homepage loading"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"BALAJI", response.data)
        self.assertIn(b"MEDICAL", response.data)

    def test_02_get_categories(self):
        """Test fetching categories"""
        response = self.client.get("/api/categories")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertGreaterEqual(len(data["categories"]), 8)

    def test_03_get_medicines(self):
        """Test fetching medicines and search filtering"""
        response = self.client.get("/api/medicines")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertGreaterEqual(data["count"], 30)

        # Search for Paracetamol / Dolo
        search_res = self.client.get("/api/medicines?search=Dolo")
        search_data = json.loads(search_res.data)
        self.assertTrue(search_data["success"])
        self.assertGreaterEqual(search_data["count"], 1)
        self.assertEqual(search_data["medicines"][0]["name"], "Dolo 650 Tablet")

    def test_04_prescription_upload_and_order_flow(self):
        """Test uploading prescription and placing an order with Rx item"""
        # 1. Upload mock prescription
        test_file = (io.BytesIO(b"%PDF-1.4 mock prescription content"), "doctor_rx.pdf")
        upload_res = self.client.post(
            "/api/prescriptions/upload",
            data={
                "file": test_file,
                "patient_name": "Rohan Gupta",
                "patient_phone": "9876501234",
                "doctor_name": "Dr. Sharma, MD",
                "notes": "Take after meals"
            },
            content_type="multipart/form-data"
        )
        self.assertEqual(upload_res.status_code, 200)
        upload_data = json.loads(upload_res.data)
        self.assertTrue(upload_data["success"])
        rx_id = upload_data["prescription"]["id"]
        self.assertIsNotNone(rx_id)

        # 2. Find medicine ID for an Rx drug (e.g. Augmentin 625 Duo)
        meds_res = self.client.get("/api/medicines?search=Augmentin")
        meds_data = json.loads(meds_res.data)
        self.assertGreaterEqual(len(meds_data["medicines"]), 1)
        augmentin = meds_data["medicines"][0]
        initial_stock = augmentin["stock_quantity"]

        # 3. Place order
        order_res = self.client.post(
            "/api/orders",
            json={
                "customer_name": "Rohan Gupta",
                "customer_phone": "9876501234",
                "customer_email": "rohan@example.com",
                "delivery_address": "Flat 102, Shanti Vihar, Delhi 110001",
                "payment_method": "Cash on Delivery",
                "prescription_id": rx_id,
                "items": [{"medicine_id": augmentin["id"], "quantity": 2}]
            }
        )
        self.assertEqual(order_res.status_code, 200)
        order_data = json.loads(order_res.data)
        self.assertTrue(order_data["success"])
        order_code = order_data["order"]["order_code"]

        # 4. Check stock decrement
        updated_med = json.loads(self.client.get(f"/api/medicines/{augmentin['id']}").data)["medicine"]
        self.assertEqual(updated_med["stock_quantity"], initial_stock - 2)

        # 5. Fetch invoice / order by code
        invoice_res = self.client.get(f"/api/orders/code/{order_code}")
        self.assertEqual(invoice_res.status_code, 200)
        invoice_data = json.loads(invoice_res.data)
        self.assertEqual(invoice_data["order"]["customer_name"], "Rohan Gupta")
        self.assertEqual(len(invoice_data["items"]), 1)

    def test_05_admin_operations(self):
        """Test admin stats, status update, and inventory modifications"""
        # Stats
        stats_res = self.client.get("/api/admin/stats")
        self.assertEqual(stats_res.status_code, 200)
        stats = json.loads(stats_res.data)["stats"]
        self.assertIn("total_medicines", stats)
        self.assertIn("total_orders", stats)
        self.assertIn("total_revenue", stats)

        # Add new medicine
        new_med_res = self.client.post(
            "/api/admin/medicines",
            json={
                "name": "Zincovit Multivitamin",
                "generic_name": "Multivitamins & Minerals + Grape Seed Extract",
                "category_id": 8,
                "dosage_form": "Tablet",
                "strength": "Strip of 15",
                "price": 110.00,
                "discount_price": 95.00,
                "stock_quantity": 50,
                "requires_prescription": 0,
                "manufacturer": "Apex Laboratories",
                "batch_no": "ZV-2026",
                "expiry_date": "2028-06-30",
                "description": "Immunity booster and daily essential vitamin.",
                "usage_instructions": "1 tablet daily after food."
            }
        )
        self.assertEqual(new_med_res.status_code, 200)
        new_med_data = json.loads(new_med_res.data)
        self.assertTrue(new_med_data["success"])
        new_med_id = new_med_data["medicine_id"]

        # Delete added test medicine
        del_res = self.client.delete(f"/api/admin/medicines/{new_med_id}")
        self.assertEqual(del_res.status_code, 200)
        self.assertTrue(json.loads(del_res.data)["success"])

    def test_06_user_auth_and_session(self):
        """Test registration, login, session check, and logout"""
        import time
        test_email = f"pooja_{int(time.time())}@example.com"
        # Register new user
        reg_res = self.client.post(
            "/api/auth/register",
            json={
                "name": "Pooja Sharma",
                "email": test_email,
                "phone": "9811223344",
                "password": "password123",
                "role": "customer"
            }
        )
        self.assertEqual(reg_res.status_code, 200)
        reg_data = json.loads(reg_res.data)
        self.assertTrue(reg_data["success"])
        self.assertEqual(reg_data["user"]["email"], test_email)

        # Check me
        me_res = self.client.get("/api/auth/me")
        self.assertEqual(me_res.status_code, 200)
        me_data = json.loads(me_res.data)
        self.assertEqual(me_data["user"]["name"], "Pooja Sharma")

        # Logout
        logout_res = self.client.post("/api/auth/logout")
        self.assertEqual(logout_res.status_code, 200)
        self.assertIsNone(json.loads(self.client.get("/api/auth/me").data)["user"])

        # Login with seeded pharmacist credentials
        login_res = self.client.post(
            "/api/auth/login",
            json={
                "email": "pharmacist@balajimedical.com",
                "password": "admin123"
            }
        )
        self.assertEqual(login_res.status_code, 200)
        login_data = json.loads(login_res.data)
        self.assertTrue(login_data["success"])
        self.assertEqual(login_data["user"]["role"], "pharmacist")

    def test_07_stock_status_and_company_filters(self):
        """Test filtering by stock status (in_stock vs out_of_stock) and pharma company"""
        # Out of stock filter
        oos_res = self.client.get("/api/medicines?stock_status=out_of_stock")
        self.assertEqual(oos_res.status_code, 200)
        oos_data = json.loads(oos_res.data)
        self.assertTrue(oos_data["success"])
        self.assertGreaterEqual(oos_data["count"], 5)
        for med in oos_data["medicines"]:
            self.assertEqual(med["stock_quantity"], 0)

        # In stock filter
        in_stock_res = self.client.get("/api/medicines?stock_status=in_stock")
        self.assertEqual(in_stock_res.status_code, 200)
        in_stock_data = json.loads(in_stock_res.data)
        self.assertGreaterEqual(in_stock_data["count"], 20)
        for med in in_stock_data["medicines"]:
            self.assertGreater(med["stock_quantity"], 0)

        # Company filter for "Cipla Ltd"
        cipla_res = self.client.get("/api/medicines?company=Cipla+Ltd")
        self.assertEqual(cipla_res.status_code, 200)
        cipla_data = json.loads(cipla_res.data)
        self.assertGreaterEqual(cipla_data["count"], 2)
        for med in cipla_data["medicines"]:
            self.assertEqual(med["manufacturer"], "Cipla Ltd")

    def test_08_in_stock_brand_alternatives(self):
        """Test querying alternatives for an out-of-stock medicine (Pacimol 650)"""
        # Find Pacimol 650
        search_res = self.client.get("/api/medicines?search=Pacimol")
        pacimol = json.loads(search_res.data)["medicines"][0]
        self.assertEqual(pacimol["stock_quantity"], 0)

        # Query in-stock alternatives
        alt_res = self.client.get(f"/api/medicines/{pacimol['id']}/alternatives")
        self.assertEqual(alt_res.status_code, 200)
        alt_data = json.loads(alt_res.data)
        self.assertTrue(alt_data["success"])
        self.assertEqual(alt_data["generic_name"], "Paracetamol")
        self.assertGreaterEqual(len(alt_data["alternatives"]), 1)

        # Confirm all returned alternatives are in stock
        for alt in alt_data["alternatives"]:
            self.assertGreater(alt["stock_quantity"], 0)
            self.assertNotEqual(alt["id"], pacimol["id"])

if __name__ == "__main__":
    unittest.main()
