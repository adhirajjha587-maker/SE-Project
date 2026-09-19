# Balaji Medical - 24x7 Pharmacy & Healthcare Web Application

An end-to-end full-stack pharmacy web application designed for retail pharmaceutical dispensing, prescription management, e-commerce ordering, and real-time inventory management.

---

## 🌟 Key Features

### 👤 Customer & Patient Portal
- **Extensive Medical Catalog**: 35+ realistic medicines and healthcare devices across 8 categories (Pain Relief, Antibiotics, Diabetes, Cardiac, Respiratory, Digestion, Skin Care, Wellness & Devices).
- **Clinical Details**: Displays active generic salt composition, manufacturer, strength, dosage form, batch number, expiry date, indications, usage directions, and known side effects.
- **Smart Instant Search & Filter**: Real-time filtering by brand name, generic salt formula, category, Rx requirement, in-stock status, and price sorting.
- **Prescription Upload System (Rx)**: Patients can upload prescriptions (PDF, PNG, JPG) with doctor and patient details, ensuring regulatory compliance.
- **Interactive Shopping Cart**: Cart slide-over with stock validation, quantity adjusters, and automatic Rx validation warnings.
- **Multi-Step Checkout & Mock Payments**: Supports Cash on Delivery (COD), interactive UPI QR Code scanning (`balajimedical@upi`), and Debit/Credit Card.
- **Printable Medical Tax Invoice**: Generates formal drug tax invoices formatted with Balaji Medical pharmacy license numbers, GST details, itemized batch numbers, and pharmacist authorization stamps.
- **Order Tracking**: Track live delivery statuses (`Placed` ➔ `Processing` ➔ `Dispatched` ➔ `Delivered`) via phone number or order ID.

### 🛡️ Pharmacist & Admin Portal
- **Real-Time Analytics Dashboard**: Live metrics for total catalog count, low stock warnings (<15 units), near-expiry warnings (<60 days), total orders, revenue, and pending prescriptions.
- **Inventory Management**: Add new medicines, edit price/stock/batch details, and remove items with automated inventory decrement upon purchase.
- **Prescription Verification Queue**: Review uploaded prescriptions, view patient/doctor notes, inspect documents, and approve or reject slips.
- **Order Fulfillment Tracking**: Update customer order status from `Placed` to `Processing`, `Dispatched`, or `Delivered`.

---

## 🏗️ Architecture & Database Schema

### Tech Stack
- **Backend**: Python 3 (Flask REST API, Werkzeug)
- **Database**: SQLite3 (`balaji_medical.db`) with Foreign Key constraints
- **Frontend**: Responsive Single-Page Layout (HTML5, Tailwind CSS, Lucide Icons, Vanilla ES6+ JavaScript)

### Database Tables
```
categories (id, name, slug, icon, description)
     │
     └──< medicines (id, name, generic_name, category_id, manufacturer, dosage_form,
                     strength, price, discount_price, stock_quantity, batch_no,
                     expiry_date, requires_prescription, description, side_effects,
                     usage_instructions, image_url)
              │
              └──< order_items (id, order_id, medicine_id, medicine_name, quantity, unit_price, subtotal)
                        │
orders (id, order_code, customer_name, customer_phone, delivery_address,
        subtotal, delivery_fee, discount, total_amount, payment_method,
        payment_status, order_status, prescription_id, created_at)
     │
     └──< prescriptions (id, patient_name, patient_phone, doctor_name, filename, file_path, status, notes, uploaded_at)
```

---

## 🚀 How to Run

### Quick Start (Windows)
Double-click `run.bat` or open PowerShell / Command Prompt:

```powershell
# 1. Install dependencies (if not already installed)
py -m pip install -r requirements.txt

# 2. Run the application
py app.py
```

Open your browser and navigate to:
👉 **`http://127.0.0.1:5000`**

---

## 🧪 Running Automated Tests

A comprehensive unit and integration test suite is included:

```powershell
py test_api.py
```

Tests verify homepage rendering, category listing, medicine search, prescription uploads, stock decrements during checkout, and admin CRUD operations.

---

## 📋 REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/categories` | Retrieve all medicine categories with item count |
| `GET` | `/api/medicines` | Search & filter medicines by keyword, category, Rx flag, stock |
| `GET` | `/api/medicines/<id>` | Full clinical medicine details |
| `POST` | `/api/prescriptions/upload` | Upload doctor's prescription file |
| `POST` | `/api/orders` | Place customer order and decrement inventory |
| `GET` | `/api/orders/code/<code>` | Retrieve order details and invoice data |
| `GET` | `/api/orders?phone=<phone>` | Track orders by customer phone number |
| `GET` | `/api/admin/stats` | Dashboard metrics (revenue, low stock, near expiry) |
| `POST` | `/api/admin/medicines` | Add or update inventory items |
| `DELETE` | `/api/admin/medicines/<id>` | Remove medicine from catalog |
| `PATCH` | `/api/admin/orders/<id>` | Update fulfillment status |
| `PATCH` | `/api/admin/prescriptions/<id>` | Approve or reject prescription |

---

## 🏥 Pharmacy Information
- **Store Name**: Balaji Medical & Healthcare Services
- **Drug License Number**: DL-20B/21B-BALAJI-4421
- **GSTIN**: 07AAAAA0000A1Z5
- **Emergency Helpline**: +91 98765 43210 (24x7)
- **Ambulance Helpline**: 108 / 102
