"""
invoices.py - Invoice Management API Routes
Handles CRUD operations for invoices with GST/TCS calculations
For Python/Flask backend
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import mysql.connector
from mysql.connector import Error

# Create blueprint
invoices_bp = Blueprint('invoices', __name__)

# Database connection function
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='alhudha_haj',
            user='root',
            password=''
        )
        return connection
    except Error as e:
        print(f"Error connecting to database: {e}")
        return None

# ====== HELPER FUNCTIONS ======
def generate_invoice_number(cursor):
    """Generate unique invoice number"""
    cursor.execute("SELECT COUNT(*) as count FROM invoices")
    result = cursor.fetchone()
    count = result['count'] if result else 0
    return f"INV-{str(count + 1).zfill(6)}"

def update_traveler_total_paid(cursor, traveler_id, amount):
    """Update traveler's total paid amount"""
    cursor.execute("""
        UPDATE travelers 
        SET total_paid = COALESCE(total_paid, 0) + %s 
        WHERE id = %s
    """, (amount, traveler_id))

# ====== GET ALL INVOICES ======
@invoices_bp.route('/api/invoices', methods=['GET'])
def get_invoices():
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                i.*,
                CONCAT(t.first_name, ' ', t.last_name) AS traveler_name,
                t.first_name,
                t.last_name,
                t.passport_no,
                t.phone,
                b.batch_name,
                b.price AS batch_price
            FROM invoices i
            LEFT JOIN travelers t ON i.traveler_id = t.id
            LEFT JOIN batches b ON i.batch_id = b.id
            ORDER BY i.created_at DESC
        """)
        
        invoices = cursor.fetchall()
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'invoices': invoices,
            'count': len(invoices)
        })
        
    except Error as e:
        print(f"Error fetching invoices: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ====== GET SINGLE INVOICE ======
@invoices_bp.route('/api/invoices/<int:invoice_id>', methods=['GET'])
def get_invoice(invoice_id):
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                i.*,
                CONCAT(t.first_name, ' ', t.last_name) AS traveler_name,
                t.first_name,
                t.last_name,
                t.passport_no,
                t.phone,
                t.email,
                b.batch_name,
                b.price AS batch_price,
                b.departure_date,
                b.return_date
            FROM invoices i
            LEFT JOIN travelers t ON i.traveler_id = t.id
            LEFT JOIN batches b ON i.batch_id = b.id
            WHERE i.id = %s
        """, (invoice_id,))
        
        invoice = cursor.fetchone()
        cursor.close()
        connection.close()
        
        if not invoice:
            return jsonify({'success': False, 'message': 'Invoice not found'}), 404
        
        return jsonify({'success': True, 'invoice': invoice})
        
    except Error as e:
        print(f"Error fetching invoice: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ====== GET INVOICES BY TRAVELER ======
@invoices_bp.route('/api/invoices/traveler/<int:traveler_id>', methods=['GET'])
def get_traveler_invoices(traveler_id):
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                i.*,
                b.batch_name
            FROM invoices i
            LEFT JOIN batches b ON i.batch_id = b.id
            WHERE i.traveler_id = %s
            ORDER BY i.created_at DESC
        """, (traveler_id,))
        
        invoices = cursor.fetchall()
        cursor.close()
        connection.close()
        
        return jsonify({'success': True, 'invoices': invoices})
        
    except Error as e:
        print(f"Error fetching traveler invoices: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ====== CREATE INVOICE ======
@invoices_bp.route('/api/invoices', methods=['POST'])
def create_invoice():
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('traveler_id'):
            return jsonify({'success': False, 'message': 'Traveler ID is required'}), 400
        
        traveler_id = data['traveler_id']
        base_amount = float(data.get('base_amount', 0))
        
        if base_amount <= 0:
            return jsonify({'success': False, 'message': 'Base amount must be greater than 0'}), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        cursor = connection.cursor(dictionary=True)
        
        # Check if traveler exists
        cursor.execute("SELECT id FROM travelers WHERE id = %s", (traveler_id,))
        traveler = cursor.fetchone()
        
        if not traveler:
            cursor.close()
            connection.close()
            return jsonify({'success': False, 'message': 'Traveler not found'}), 404
        
        # Generate invoice number
        invoice_number = generate_invoice_number(cursor)
        
        # Calculate amounts
        gst_percent = float(data.get('gst_percent', 5))
        gst_amount = data.get('gst_amount', (base_amount * gst_percent / 100))
        subtotal = base_amount + gst_amount
        tcs_percent = float(data.get('tcs_percent', 1))
        tcs_amount = data.get('tcs_amount', (subtotal * tcs_percent / 100))
        total_amount = data.get('total_amount', (subtotal + tcs_amount))
        
        status = data.get('status', 'pending')
        due_date = data.get('due_date')
        notes = data.get('notes')
        invoice_date = data.get('invoice_date', datetime.now().strftime('%Y-%m-%d'))
        
        # Insert invoice
        cursor.execute("""
            INSERT INTO invoices (
                invoice_number,
                traveler_id,
                batch_id,
                base_amount,
                gst_percent,
                gst_amount,
                tcs_percent,
                tcs_amount,
                total_amount,
                status,
                due_date,
                notes,
                invoice_date,
                created_at,
                updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """, (
            invoice_number,
            traveler_id,
            data.get('batch_id') or None,
            base_amount,
            gst_percent,
            gst_amount,
            tcs_percent,
            tcs_amount,
            total_amount,
            status,
            due_date,
            notes,
            invoice_date
        ))
        
        invoice_id = cursor.lastrowid
        
        # Update traveler's total_paid if status is 'paid'
        if status == 'paid':
            update_traveler_total_paid(cursor, traveler_id, total_amount)
        
        connection.commit()
        
        # Get the created invoice
        cursor.execute("""
            SELECT 
                i.*,
                CONCAT(t.first_name, ' ', t.last_name) AS traveler_name
            FROM invoices i
            LEFT JOIN travelers t ON i.traveler_id = t.id
            WHERE i.id = %s
        """, (invoice_id,))
        
        new_invoice = cursor.fetchone()
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'message': 'Invoice created successfully',
            'invoice': new_invoice
        }), 201
        
    except Error as e:
        print(f"Error creating invoice: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ====== UPDATE INVOICE ======
@invoices_bp.route('/api/invoices/<int:invoice_id>', methods=['PUT'])
def update_invoice(invoice_id):
    try:
        data = request.get_json()
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        cursor = connection.cursor(dictionary=True)
        
        # Get current invoice data
        cursor.execute("""
            SELECT traveler_id, total_amount, status 
            FROM invoices WHERE id = %s
        """, (invoice_id,))
        
        current = cursor.fetchone()
        
        if not current:
            cursor.close()
            connection.close()
            return jsonify({'success': False, 'message': 'Invoice not found'}), 404
        
        old_status = current['status']
        old_amount = float(current['total_amount'] or 0)
        traveler_id = current['traveler_id']
        
        # Build update query dynamically
        update_fields = []
        update_values = []
        
        if 'total_amount' in data:
            update_fields.append("total_amount = %s")
            update_values.append(data['total_amount'])
        if 'status' in data:
            update_fields.append("status = %s")
            update_values.append(data['status'])
        if 'due_date' in data:
            update_fields.append("due_date = %s")
            update_values.append(data['due_date'])
        if 'notes' in data:
            update_fields.append("notes = %s")
            update_values.append(data['notes'])
        if 'gst_percent' in data:
            update_fields.append("gst_percent = %s")
            update_values.append(data['gst_percent'])
        if 'gst_amount' in data:
            update_fields.append("gst_amount = %s")
            update_values.append(data['gst_amount'])
        if 'tcs_percent' in data:
            update_fields.append("tcs_percent = %s")
            update_values.append(data['tcs_percent'])
        if 'tcs_amount' in data:
            update_fields.append("tcs_amount = %s")
            update_values.append(data['tcs_amount'])
        if 'base_amount' in data:
            update_fields.append("base_amount = %s")
            update_values.append(data['base_amount'])
        
        if not update_fields:
            cursor.close()
            connection.close()
            return jsonify({'success': False, 'message': 'No fields to update'}), 400
        
        update_fields.append("updated_at = NOW()")
        update_values.append(invoice_id)
        
        query = f"UPDATE invoices SET {', '.join(update_fields)} WHERE id = %s"
        cursor.execute(query, update_values)
        
        # Update traveler's total_paid based on status change
        new_status = data.get('status')
        new_amount = float(data.get('total_amount', current['total_amount'] or 0))
        
        if old_status != new_status:
            if new_status == 'paid':
                update_traveler_total_paid(cursor, traveler_id, new_amount)
            elif old_status == 'paid':
                cursor.execute("""
                    UPDATE travelers 
                    SET total_paid = COALESCE(total_paid, 0) - %s 
                    WHERE id = %s
                """, (old_amount, traveler_id))
        elif new_status == 'paid' and 'total_amount' in data and float(data['total_amount']) != old_amount:
            diff = float(data['total_amount']) - old_amount
            cursor.execute("""
                UPDATE travelers 
                SET total_paid = COALESCE(total_paid, 0) + %s 
                WHERE id = %s
            """, (diff, traveler_id))
        
        connection.commit()
        
        # Get updated invoice
        cursor.execute("""
            SELECT 
                i.*,
                CONCAT(t.first_name, ' ', t.last_name) AS traveler_name
            FROM invoices i
            LEFT JOIN travelers t ON i.traveler_id = t.id
            WHERE i.id = %s
        """, (invoice_id,))
        
        updated = cursor.fetchone()
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'message': 'Invoice updated successfully',
            'invoice': updated
        })
        
    except Error as e:
        print(f"Error updating invoice: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ====== DELETE INVOICE ======
@invoices_bp.route('/api/invoices/<int:invoice_id>', methods=['DELETE'])
def delete_invoice(invoice_id):
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        cursor = connection.cursor(dictionary=True)
        
        # Get invoice data before deleting
        cursor.execute("""
            SELECT traveler_id, total_amount, status 
            FROM invoices WHERE id = %s
        """, (invoice_id,))
        
        invoice = cursor.fetchone()
        
        if not invoice:
            cursor.close()
            connection.close()
            return jsonify({'success': False, 'message': 'Invoice not found'}), 404
        
        # If invoice was paid, subtract from traveler's total_paid
        if invoice['status'] == 'paid':
            cursor.execute("""
                UPDATE travelers 
                SET total_paid = COALESCE(total_paid, 0) - %s 
                WHERE id = %s
            """, (float(invoice['total_amount'] or 0), invoice['traveler_id']))
        
        # Delete the invoice
        cursor.execute("DELETE FROM invoices WHERE id = %s", (invoice_id,))
        connection.commit()
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'message': 'Invoice deleted successfully'
        })
        
    except Error as e:
        print(f"Error deleting invoice: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ====== GET INVOICE STATISTICS ======
@invoices_bp.route('/api/invoices/stats', methods=['GET'])
def get_invoice_stats():
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                COUNT(*) as total_invoices,
                SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END) as paid_count,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_count,
                SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled_count,
                COALESCE(SUM(CASE WHEN status = 'paid' THEN total_amount ELSE 0 END), 0) as total_revenue,
                COALESCE(SUM(CASE WHEN status = 'pending' THEN total_amount ELSE 0 END), 0) as pending_revenue
            FROM invoices
        """)
        
        stats = cursor.fetchone()
        cursor.close()
        connection.close()
        
        return jsonify({'success': True, 'stats': stats})
        
    except Error as e:
        print(f"Error fetching invoice stats: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ====== GET INVOICE BY NUMBER ======
@invoices_bp.route('/api/invoices/number/<string:invoice_number>', methods=['GET'])
def get_invoice_by_number(invoice_number):
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                i.*,
                CONCAT(t.first_name, ' ', t.last_name) AS traveler_name,
                t.passport_no,
                b.batch_name
            FROM invoices i
            LEFT JOIN travelers t ON i.traveler_id = t.id
            LEFT JOIN batches b ON i.batch_id = b.id
            WHERE i.invoice_number = %s
        """, (invoice_number,))
        
        invoice = cursor.fetchone()
        cursor.close()
        connection.close()
        
        if not invoice:
            return jsonify({'success': False, 'message': 'Invoice not found'}), 404
        
        return jsonify({'success': True, 'invoice': invoice})
        
    except Error as e:
        print(f"Error fetching invoice: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
