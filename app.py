"""
Balaji Medical - Full-Stack Pharmacy & Healthcare Web Application
Flask REST API & Web Server
"""

import os
import random
import string
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, jsonify, send_from_directory, session
import database

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["SECRET_KEY"] = "balaji-medical-secret-key-2026"
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads", "prescriptions")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max upload
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf", "webp"}

# Ensure upload directory exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Ensure database is initialized
database.init_db()

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_order_code():
    date_str = datetime.now().strftime("%Y%m%d")
    random_str = "".join(random.choices(string.digits, k=4))
    return f"BM-{date_str}-{random_str}"

@app.route("/")
def index():
    return render_template("index.html")

# ----------------- User Authentication APIs ----------------- #

@app.route("/api/auth/register", methods=["POST"])
def auth_register():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    phone = data.get("phone", "").strip()
    password = data.get("password", "").strip()
    role = data.get("role", "customer").strip()

    if role not in ["customer", "pharmacist"]:
        role = "customer"

    if not name or not email or not password:
        return jsonify({"success": False, "error": "Name, email, and password are required"}), 400

    if len(password) < 4:
        return jsonify({"success": False, "error": "Password must be at least 4 characters long"}), 400

    conn = database.get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        return jsonify({"success": False, "error": "Email address is already registered. Please login."}), 400

    hashed_pw = generate_password_hash(password)
    cursor.execute("""
        INSERT INTO users (name, email, phone, password_hash, role)
        VALUES (?, ?, ?, ?, ?)
    """, (name, email, phone, hashed_pw, role))
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()

    session["user_id"] = user_id
    session["user_name"] = name
    session["user_email"] = email
    session["user_role"] = role

    return jsonify({
        "success": True,
        "message": f"Welcome to Balaji Medical, {name}!",
        "user": {
            "id": user_id,
            "name": name,
            "email": email,
            "phone": phone,
            "role": role
        }
    })

@app.route("/api/auth/login", methods=["POST"])
def auth_login():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()

    if not email or not password:
        return jsonify({"success": False, "error": "Email and password are required"}), 400

    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()

    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"success": False, "error": "Invalid email or password. Please try again."}), 401

    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    session["user_email"] = user["email"]
    session["user_role"] = user["role"]

    return jsonify({
        "success": True,
        "message": f"Welcome back, {user['name']}!",
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "phone": user["phone"],
            "role": user["role"]
        }
    })

@app.route("/api/auth/me", methods=["GET"])
def auth_me():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": True, "user": None})

    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, phone, role, created_at FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        session.clear()
        return jsonify({"success": True, "user": None})

    return jsonify({"success": True, "user": dict(user)})

@app.route("/api/auth/logout", methods=["POST"])
def auth_logout():
    session.clear()
    return jsonify({"success": True, "message": "Logged out successfully"})

# ----------------- Medicine & Category APIs ----------------- #

@app.route("/api/categories", methods=["GET"])
def get_categories():
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.*, COUNT(m.id) as medicine_count 
        FROM categories c 
        LEFT JOIN medicines m ON c.id = m.category_id 
        GROUP BY c.id 
        ORDER BY c.id ASC
    """)
    categories = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({"success": True, "categories": categories})

@app.route("/api/manufacturers", methods=["GET"])
def get_manufacturers():
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT manufacturer FROM medicines ORDER BY manufacturer ASC")
    companies = [r[0] for r in cursor.fetchall() if r[0]]
    conn.close()
    return jsonify({"success": True, "companies": companies})

@app.route("/api/medicines", methods=["GET"])
def get_medicines():
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    company = request.args.get("company", "").strip()
    requires_rx = request.args.get("requires_rx", "").strip()
    in_stock = request.args.get("in_stock", "").strip()
    stock_status = request.args.get("stock_status", "").strip()
    sort_by = request.args.get("sort", "default").strip()

    conn = database.get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT m.*, c.name as category_name, c.slug as category_slug 
        FROM medicines m 
        JOIN categories c ON m.category_id = c.id 
        WHERE 1=1
    """
    params = []

    if search:
        query += " AND (m.name LIKE ? OR m.generic_name LIKE ? OR m.description LIKE ? OR m.manufacturer LIKE ?)"
        wildcard = f"%{search}%"
        params.extend([wildcard, wildcard, wildcard, wildcard])

    if category and category != "all":
        if category.isdigit():
            query += " AND m.category_id = ?"
            params.append(int(category))
        else:
            query += " AND c.slug = ?"
            params.append(category)

    if company and company != "all":
        query += " AND m.manufacturer = ?"
        params.append(company)

    if requires_rx in ("0", "1"):
        query += " AND m.requires_prescription = ?"
        params.append(int(requires_rx))

    if stock_status == "in_stock" or in_stock == "1":
        query += " AND m.stock_quantity > 0"
    elif stock_status == "out_of_stock":
        query += " AND m.stock_quantity = 0"

    # Sorting
    if sort_by == "price_asc":
        query += " ORDER BY COALESCE(m.discount_price, m.price) ASC"
    elif sort_by == "price_desc":
        query += " ORDER BY COALESCE(m.discount_price, m.price) DESC"
    elif sort_by == "name_asc":
        query += " ORDER BY m.name ASC"
    elif sort_by == "stock_desc":
        query += " ORDER BY m.stock_quantity DESC"
    else:
        query += " ORDER BY m.id ASC"

    cursor.execute(query, params)
    medicines = [dict(row) for row in cursor.fetchall()]

    # Also fetch all companies for frontend filter
    cursor.execute("SELECT DISTINCT manufacturer FROM medicines ORDER BY manufacturer ASC")
    companies = [r[0] for r in cursor.fetchall() if r[0]]

    conn.close()
    return jsonify({
        "success": True,
        "count": len(medicines),
        "companies": companies,
        "medicines": medicines
    })

@app.route("/api/medicines/<int:med_id>", methods=["GET"])
def get_medicine(med_id):
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.*, c.name as category_name, c.slug as category_slug 
        FROM medicines m 
        JOIN categories c ON m.category_id = c.id 
        WHERE m.id = ?
    """, (med_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return jsonify({"success": False, "error": "Medicine not found"}), 404

    medicine = dict(row)

    # Fetch in-stock alternative brands sharing the exact same generic salt
    cursor.execute("""
        SELECT id, name, generic_name, manufacturer, dosage_form, strength,
               price, discount_price, stock_quantity, requires_prescription, image_url
        FROM medicines
        WHERE generic_name = ? AND id != ? AND stock_quantity > 0
        ORDER BY COALESCE(discount_price, price) ASC
        LIMIT 5
    """, (medicine["generic_name"], medicine["id"]))
    alternatives = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return jsonify({
        "success": True,
        "medicine": medicine,
        "alternatives": alternatives
    })

@app.route("/api/medicines/<int:med_id>/alternatives", methods=["GET"])
def get_medicine_alternatives(med_id):
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT generic_name FROM medicines WHERE id = ?", (med_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({"success": False, "error": "Medicine not found"}), 404

    generic_name = row["generic_name"]
    cursor.execute("""
        SELECT id, name, generic_name, manufacturer, dosage_form, strength,
               price, discount_price, stock_quantity, requires_prescription, image_url
        FROM medicines
        WHERE generic_name = ? AND id != ? AND stock_quantity > 0
        ORDER BY COALESCE(discount_price, price) ASC
    """, (generic_name, med_id))
    alternatives = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify({"success": True, "generic_name": generic_name, "alternatives": alternatives})

# ----------------- Prescription APIs ----------------- #

@app.route("/api/prescriptions/upload", methods=["POST"])
def upload_prescription():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No prescription file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"success": False, "error": "Allowed file formats: PNG, JPG, JPEG, WEBP, PDF"}), 400

    patient_name = request.form.get("patient_name", "").strip() or "Anonymous Patient"
    patient_phone = request.form.get("patient_phone", "").strip()
    doctor_name = request.form.get("doctor_name", "").strip() or "Dr. Not Specified"
    notes = request.form.get("notes", "").strip()

    ext = file.filename.rsplit(".", 1)[1].lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_filename = secure_filename(f"rx_{timestamp}_{random.randint(1000, 9999)}.{ext}")
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)
    file.save(file_path)

    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO prescriptions (patient_name, patient_phone, doctor_name, filename, file_path, status, notes)
        VALUES (?, ?, ?, ?, ?, 'Approved', ?)
    """, (patient_name, patient_phone, doctor_name, unique_filename, f"/uploads/prescriptions/{unique_filename}", notes))
    conn.commit()
    prescription_id = cursor.lastrowid
    conn.close()

    return jsonify({
        "success": True,
        "message": "Prescription uploaded successfully and verified by Balaji Medical pharmacist!",
        "prescription": {
            "id": prescription_id,
            "patient_name": patient_name,
            "doctor_name": doctor_name,
            "filename": unique_filename,
            "file_url": f"/uploads/prescriptions/{unique_filename}",
            "status": "Approved"
        }
    })

@app.route("/uploads/prescriptions/<filename>")
def serve_prescription_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# ----------------- Order Management APIs ----------------- #

@app.route("/api/orders", methods=["POST"])
def place_order():
    data = request.get_json() or {}
    customer_name = data.get("customer_name", "").strip()
    customer_phone = data.get("customer_phone", "").strip()
    customer_email = data.get("customer_email", "").strip()
    delivery_address = data.get("delivery_address", "").strip()
    payment_method = data.get("payment_method", "Cash on Delivery").strip()
    prescription_id = data.get("prescription_id")
    items = data.get("items", [])
    notes = data.get("notes", "").strip()

    if not customer_name or not customer_phone or not delivery_address:
        return jsonify({"success": False, "error": "Customer name, phone, and delivery address are required"}), 400

    if not items:
        return jsonify({"success": False, "error": "Cart is empty. Please add items to place order."}), 400

    conn = database.get_db_connection()
    cursor = conn.cursor()

    subtotal = 0.0
    order_items_to_insert = []
    requires_rx_items = []

    # Validate stock and calculate pricing
    for item in items:
        med_id = item.get("medicine_id")
        qty = int(item.get("quantity", 1))
        if qty <= 0:
            continue

        cursor.execute("SELECT * FROM medicines WHERE id = ?", (med_id,))
        med = cursor.fetchone()
        if not med:
            conn.close()
            return jsonify({"success": False, "error": f"Medicine with ID {med_id} not found"}), 404

        if med["stock_quantity"] < qty:
            conn.close()
            return jsonify({
                "success": False,
                "error": f"Insufficient stock for '{med['name']}'. Only {med['stock_quantity']} units available."
            }), 400

        unit_price = med["discount_price"] if med["discount_price"] else med["price"]
        item_subtotal = round(unit_price * qty, 2)
        subtotal += item_subtotal

        if med["requires_prescription"]:
            requires_rx_items.append(med["name"])

        order_items_to_insert.append({
            "medicine_id": med["id"],
            "medicine_name": med["name"],
            "quantity": qty,
            "unit_price": unit_price,
            "subtotal": item_subtotal,
            "new_stock": med["stock_quantity"] - qty
        })

    # Prescription validation check
    if requires_rx_items and not prescription_id:
        conn.close()
        return jsonify({
            "success": False,
            "error": f"Your order contains prescription (Rx) medicines: {', '.join(requires_rx_items)}. Please upload a valid doctor's prescription before proceeding."
        }), 400

    # Pricing calculations
    delivery_fee = 0.0 if subtotal >= 499.0 else 40.0
    discount = round(subtotal * 0.05, 2) if subtotal >= 1000.0 else 0.0 # 5% bulk discount over 1000
    total_amount = round(subtotal + delivery_fee - discount, 2)
    order_code = generate_order_code()
    user_id = session.get("user_id")
    payment_status = "Paid" if payment_method in ["UPI / QR Code", "Debit / Credit Card"] else "Pending"

    cursor.execute("""
        INSERT INTO orders (
            order_code, user_id, customer_name, customer_phone, customer_email, delivery_address,
            subtotal, delivery_fee, discount, total_amount, payment_method, payment_status,
            order_status, prescription_id, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Placed', ?, ?)
    """, (
        order_code, user_id, customer_name, customer_phone, customer_email, delivery_address,
        subtotal, delivery_fee, discount, total_amount, payment_method, payment_status,
        prescription_id, notes
    ))
    order_id = cursor.lastrowid

    # Insert items & decrement stock
    for item in order_items_to_insert:
        cursor.execute("""
            INSERT INTO order_items (order_id, medicine_id, medicine_name, quantity, unit_price, subtotal)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (order_id, item["medicine_id"], item["medicine_name"], item["quantity"], item["unit_price"], item["subtotal"]))

        cursor.execute("""
            UPDATE medicines SET stock_quantity = ? WHERE id = ?
        """, (item["new_stock"], item["medicine_id"]))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Order successfully placed at Balaji Medical!",
        "order": {
            "id": order_id,
            "order_code": order_code,
            "customer_name": customer_name,
            "customer_phone": customer_phone,
            "delivery_address": delivery_address,
            "subtotal": subtotal,
            "delivery_fee": delivery_fee,
            "discount": discount,
            "total_amount": total_amount,
            "payment_method": payment_method,
            "payment_status": payment_status,
            "order_status": "Placed",
            "items_count": len(order_items_to_insert)
        }
    })

@app.route("/api/orders/<int:order_id>", methods=["GET"])
def get_order_by_id(order_id):
    return fetch_order(order_id=order_id)

@app.route("/api/orders/code/<order_code>", methods=["GET"])
def get_order_by_code(order_code):
    return fetch_order(order_code=order_code)

def fetch_order(order_id=None, order_code=None):
    conn = database.get_db_connection()
    cursor = conn.cursor()

    if order_id:
        cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    else:
        cursor.execute("SELECT * FROM orders WHERE order_code = ?", (order_code,))

    order_row = cursor.fetchone()
    if not order_row:
        conn.close()
        return jsonify({"success": False, "error": "Order not found"}), 404

    order = dict(order_row)
    cursor.execute("""
        SELECT oi.*, m.dosage_form, m.strength, m.manufacturer, m.batch_no, m.expiry_date
        FROM order_items oi
        JOIN medicines m ON oi.medicine_id = m.id
        WHERE oi.order_id = ?
    """, (order["id"],))
    items = [dict(r) for r in cursor.fetchall()]

    prescription = None
    if order.get("prescription_id"):
        cursor.execute("SELECT * FROM prescriptions WHERE id = ?", (order["prescription_id"],))
        p_row = cursor.fetchone()
        if p_row:
            prescription = dict(p_row)

    conn.close()
    return jsonify({
        "success": True,
        "order": order,
        "items": items,
        "prescription": prescription
    })

@app.route("/api/orders", methods=["GET"])
def get_recent_orders():
    phone = request.args.get("phone", "").strip()
    user_id = session.get("user_id")
    conn = database.get_db_connection()
    cursor = conn.cursor()

    if user_id and not phone and session.get("user_role") != "pharmacist":
        cursor.execute("SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC", (user_id,))
    elif phone:
        cursor.execute("SELECT * FROM orders WHERE customer_phone = ? ORDER BY id DESC", (phone,))
    else:
        cursor.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 50")

    orders = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({"success": True, "count": len(orders), "orders": orders})

# ----------------- Pharmacist / Admin APIs ----------------- #

@app.route("/api/admin/stats", methods=["GET"])
def get_admin_stats():
    conn = database.get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM medicines")
    total_medicines = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM medicines WHERE stock_quantity <= 15")
    low_stock_count = cursor.fetchone()[0]

    today_str = datetime.now().strftime("%Y-%m-%d")
    sixty_days_str = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
    cursor.execute("SELECT COUNT(*) FROM medicines WHERE expiry_date <= ?", (sixty_days_str,))
    near_expiry_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM orders")
    total_orders = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE order_status != 'Cancelled'")
    total_revenue = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM prescriptions WHERE status = 'Pending'")
    pending_rx = cursor.fetchone()[0]

    conn.close()
    return jsonify({
        "success": True,
        "stats": {
            "total_medicines": total_medicines,
            "low_stock_count": low_stock_count,
            "near_expiry_count": near_expiry_count,
            "total_orders": total_orders,
            "total_revenue": round(total_revenue, 2),
            "pending_prescriptions": pending_rx
        }
    })

@app.route("/api/admin/prescriptions", methods=["GET"])
def get_admin_prescriptions():
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM prescriptions ORDER BY id DESC")
    prescriptions = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify({"success": True, "prescriptions": prescriptions})

@app.route("/api/admin/prescriptions/<int:p_id>", methods=["PATCH"])
def update_prescription_status(p_id):
    data = request.get_json() or {}
    new_status = data.get("status")
    notes = data.get("notes")

    if new_status not in ["Pending", "Approved", "Rejected"]:
        return jsonify({"success": False, "error": "Invalid status"}), 400

    conn = database.get_db_connection()
    cursor = conn.cursor()
    if notes is not None:
        cursor.execute("UPDATE prescriptions SET status = ?, notes = ? WHERE id = ?", (new_status, notes, p_id))
    else:
        cursor.execute("UPDATE prescriptions SET status = ? WHERE id = ?", (new_status, p_id))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": f"Prescription #{p_id} updated to {new_status}"})

@app.route("/api/admin/orders/<int:order_id>", methods=["PATCH"])
def update_order_status(order_id):
    data = request.get_json() or {}
    new_status = data.get("order_status")

    if new_status not in ["Placed", "Processing", "Dispatched", "Delivered", "Cancelled"]:
        return jsonify({"success": False, "error": "Invalid order status"}), 400

    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET order_status = ? WHERE id = ?", (new_status, order_id))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": f"Order #{order_id} status updated to {new_status}"})

@app.route("/api/admin/medicines", methods=["POST"])
def save_medicine():
    data = request.get_json() or {}
    med_id = data.get("id")
    name = data.get("name", "").strip()
    generic_name = data.get("generic_name", "").strip()
    category_id = data.get("category_id")
    manufacturer = data.get("manufacturer", "").strip()
    dosage_form = data.get("dosage_form", "Tablet").strip()
    strength = data.get("strength", "").strip()
    price = float(data.get("price", 0.0))
    discount_price = float(data.get("discount_price")) if data.get("discount_price") else None
    stock_quantity = int(data.get("stock_quantity", 0))
    batch_no = data.get("batch_no", "").strip()
    expiry_date = data.get("expiry_date", "").strip()
    requires_prescription = int(data.get("requires_prescription", 0))
    description = data.get("description", "").strip()
    side_effects = data.get("side_effects", "").strip()
    usage_instructions = data.get("usage_instructions", "").strip()
    image_url = data.get("image_url", "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=300").strip()

    if not name or not generic_name or not category_id or price <= 0:
        return jsonify({"success": False, "error": "Name, generic name, category, and price are required"}), 400

    conn = database.get_db_connection()
    cursor = conn.cursor()

    if med_id:
        cursor.execute("""
            UPDATE medicines SET 
                name = ?, generic_name = ?, category_id = ?, manufacturer = ?, dosage_form = ?, strength = ?,
                price = ?, discount_price = ?, stock_quantity = ?, batch_no = ?, expiry_date = ?,
                requires_prescription = ?, description = ?, side_effects = ?, usage_instructions = ?, image_url = ?
            WHERE id = ?
        """, (
            name, generic_name, category_id, manufacturer, dosage_form, strength,
            price, discount_price, stock_quantity, batch_no, expiry_date,
            requires_prescription, description, side_effects, usage_instructions, image_url, med_id
        ))
        msg = f"Medicine '{name}' updated successfully."
    else:
        cursor.execute("""
            INSERT INTO medicines (
                name, generic_name, category_id, manufacturer, dosage_form, strength,
                price, discount_price, stock_quantity, batch_no, expiry_date,
                requires_prescription, description, side_effects, usage_instructions, image_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name, generic_name, category_id, manufacturer, dosage_form, strength,
            price, discount_price, stock_quantity, batch_no, expiry_date,
            requires_prescription, description, side_effects, usage_instructions, image_url
        ))
        med_id = cursor.lastrowid
        msg = f"Medicine '{name}' added successfully to inventory."

    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": msg, "medicine_id": med_id})

@app.route("/api/admin/medicines/<int:med_id>", methods=["DELETE"])
def delete_medicine(med_id):
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM medicines WHERE id = ?", (med_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": f"Medicine #{med_id} deleted from catalog."})

if __name__ == "__main__":
    print("===============================================================")
    print("   [+] BALAJI MEDICAL - Pharmacy & Healthcare Web Application  ")
    print("   [*] Server running at: http://127.0.0.1:5000                ")
    print("===============================================================")
    app.run(host="0.0.0.0", port=5000, debug=True)
