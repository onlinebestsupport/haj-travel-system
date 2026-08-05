from flask import Blueprint, request, jsonify, session, current_app, send_file
from app.database import get_db, release_db
from datetime import datetime, timedelta
import json
import traceback
import io
import csv

bp = Blueprint('invoices', __name__, url_prefix='/api/invoices')

# ============================================================
# DATABASE MIGRATION - Create invoices table if not exists
# ============================================================
def migrate_invoices_table():
    """Create invoices table if it doesn't exist"""
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        
        # Check if invoices table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'invoices'
            )
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            print("🔄 Creating invoices table...")
            cursor.execute("""
                CREATE TABLE invoices (
                    id SERIAL PRIMARY KEY,
                    invoice_number VARCHAR(50) UNIQUE NOT NULL,
                    traveler_id INTEGER REFERENCES travelers(id) ON DELETE CASCADE,
                    batch_id INTEGER REFERENCES batches(id) ON DELETE SET NULL,
                    amount DECIMAL(10,2) NOT NULL,
                    base_amount DECIMAL(10,2) DEFAULT 0,
                    gst_percent DECIMAL(5,2) DEFAULT 5,
                    gst_amount DECIMAL(10,2) DEFAULT 0,
                    tcs_percent DECIMAL(5,2) DEFAULT 1,
                    tcs_amount DECIMAL(10,2) DEFAULT 0,
                    status VARCHAR(20) DEFAULT 'pending',
                    due_date DATE,
                    invoice_date DATE DEFAULT CURRENT_DATE,
                    description TEXT,
                    notes TEXT,
                    items JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            print("✅ invoices table created successfully!")
        else:
            # Check for missing columns and add them
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'invoices'
            """)
            existing_columns = [row[0] for row in cursor.fetchall()]
            
            columns_to_add = {
                'base_amount': 'DECIMAL(10,2) DEFAULT 0',
                'gst_percent': 'DECIMAL(5,2) DEFAULT 5',
                'gst_amount': 'DECIMAL(10,2) DEFAULT 0',
                'tcs_percent': 'DECIMAL(5,2) DEFAULT 1',
                'tcs_amount': 'DECIMAL(10,2) DEFAULT 0',
                'items': 'JSONB',
                'description': 'TEXT',
                'invoice_date': 'DATE DEFAULT CURRENT_DATE'
            }
            
            for col_name, col_type in columns_to_add.items():
                if col_name not in existing_columns:
                    print(f"🔄 Adding column: {col_name}")
                    cursor.execute(f"ALTER TABLE invoices ADD COLUMN {col_name} {col_type}")
                    conn.commit()
                    print(f"✅ Column {col_name} added!")
            
            print("✅ invoices table verified!")
            
    except Exception as e:
        print(f"⚠️ Migration error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            release_db(conn, cursor)

# Run migration on import
try:
    migrate_invoices_table()
except Exception as e:
    print(f"⚠️ Migration failed: {e}")

# ============================================================
# ROUTES
# ============================================================

@bp.route('', methods=['GET'])
def get_invoices():
    """Get all invoices with traveler and batch details"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        cursor.execute("""
            SELECT 
                i.*,
                t.first_name,
                t.last_name,
                t.passport_no,
                t.email,
                t.mobile,
                b.batch_name,
                b.price as batch_price
            FROM invoices i
            LEFT JOIN travelers t ON i.traveler_id = t.id
            LEFT JOIN batches b ON i.batch_id = b.id
            ORDER BY i.created_at DESC
        """)
        invoices = cursor.fetchall()
        
        result = []
        for inv in invoices:
            inv_dict = dict(inv)
            # Convert Decimal to float for JSON
            if inv_dict.get('amount'):
                inv_dict['amount'] = float(inv_dict['amount'])
            if inv_dict.get('base_amount'):
                inv_dict['base_amount'] = float(inv_dict['base_amount'])
            if inv_dict.get('gst_amount'):
                inv_dict['gst_amount'] = float(inv_dict['gst_amount'])
            if inv_dict.get('tcs_amount'):
                inv_dict['tcs_amount'] = float(inv_dict['tcs_amount'])
            
            # Parse items JSON
            if inv_dict.get('items'):
                try:
                    if isinstance(inv_dict['items'], str):
                        inv_dict['items'] = json.loads(inv_dict['items'])
                except:
                    inv_dict['items'] = {}
            
            inv_dict['traveler_name'] = f"{inv_dict.get('first_name', '')} {inv_dict.get('last_name', '')}".strip()
            result.append(inv_dict)
        
        return jsonify({'success': True, 'invoices': result})
    except Exception as e:
        print(f"❌ Error in get_invoices: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/stats', methods=['GET'])
def get_invoice_stats():
    """Get invoice statistics"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        cursor.execute("""
            SELECT 
                COUNT(*) as total_invoices,
                SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END) as paid_count,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_count,
                COALESCE(SUM(amount), 0) as total_amount
            FROM invoices
        """)
        stats = cursor.fetchone()
        
        stats_dict = {
            'total_invoices': stats['total_invoices'] or 0,
            'paid_count': stats['paid_count'] or 0,
            'pending_count': stats['pending_count'] or 0,
            'total_amount': float(stats['total_amount'] or 0)
        }
        
        return jsonify({'success': True, 'stats': stats_dict})
    except Exception as e:
        print(f"❌ Error in get_invoice_stats: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('', methods=['POST'])
def create_invoice():
    """Create new invoice with GST/TCS calculation"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    data = request.json
    print(f"📝 Creating invoice with data: {data}")

    # Validate required fields
    if not data.get('traveler_id'):
        return jsonify({'success': False, 'error': 'traveler_id is required'}), 400
    
    # Get amount (this could be base amount or total)
    amount = float(data.get('amount', 0))
    if amount <= 0:
        return jsonify({'success': False, 'error': 'Valid amount is required'}), 400

    # Get or calculate GST and TCS
    gst_percent = float(data.get('gst_percent', 5))
    tcs_percent = float(data.get('tcs_percent', 1))
    
    # Calculate taxes
    gst_amount = amount * (gst_percent / 100)
    subtotal = amount + gst_amount
    tcs_amount = subtotal * (tcs_percent / 100)
    total_amount = subtotal + tcs_amount
    
    # Store all tax details in items JSON
    items_data = {
        'base_amount': amount,
        'gst_percent': gst_percent,
        'gst_amount': gst_amount,
        'tcs_percent': tcs_percent,
        'tcs_amount': tcs_amount,
        'total_amount': total_amount,
        'description': data.get('description', 'Travel Package'),
        'notes': data.get('notes', '')
    }
    
    # Generate invoice number
    timestamp = int(datetime.now().timestamp()) % 10000
    invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{data['traveler_id']}-{timestamp}"
    
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        
        cursor.execute("""
            INSERT INTO invoices (
                invoice_number, traveler_id, batch_id, amount, 
                base_amount, gst_percent, gst_amount, tcs_percent, tcs_amount,
                due_date, status, items, invoice_date, description, notes,
                created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            invoice_number,
            data['traveler_id'],
            data.get('batch_id'),
            total_amount,  # Store total amount with taxes
            amount,        # Store base amount
            gst_percent,
            gst_amount,
            tcs_percent,
            tcs_amount,
            data.get('due_date'),
            data.get('status', 'pending'),
            json.dumps(items_data),
            data.get('invoice_date', datetime.now().date()),
            data.get('description', 'Travel Package'),
            data.get('notes', ''),
            datetime.now(),
            datetime.now()
        ))
        
        result = cursor.fetchone()
        invoice_id = result['id'] if result else None
        conn.commit()
        
        return jsonify({
            'success': True,
            'invoice_id': invoice_id,
            'invoice_number': invoice_number,
            'total_amount': total_amount,
            'message': 'Invoice created successfully'
        })
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ Error creating invoice: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/<int:invoice_id>', methods=['GET'])
def get_invoice(invoice_id):
    """Get single invoice details"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        cursor.execute("""
            SELECT 
                i.*,
                t.first_name,
                t.last_name,
                t.passport_no,
                t.email,
                t.mobile,
                b.batch_name,
                b.price as batch_price
            FROM invoices i
            LEFT JOIN travelers t ON i.traveler_id = t.id
            LEFT JOIN batches b ON i.batch_id = b.id
            WHERE i.id = %s
        """, (invoice_id,))
        
        invoice = cursor.fetchone()
        if not invoice:
            return jsonify({'success': False, 'error': 'Invoice not found'}), 404
        
        inv_dict = dict(invoice)
        # Convert Decimal to float
        for key in ['amount', 'base_amount', 'gst_amount', 'tcs_amount']:
            if inv_dict.get(key):
                inv_dict[key] = float(inv_dict[key])
        
        if inv_dict.get('items'):
            try:
                if isinstance(inv_dict['items'], str):
                    inv_dict['items'] = json.loads(inv_dict['items'])
            except:
                inv_dict['items'] = {}
        
        inv_dict['traveler_name'] = f"{inv_dict.get('first_name', '')} {inv_dict.get('last_name', '')}".strip()
        
        return jsonify({'success': True, 'invoice': inv_dict})
    except Exception as e:
        print(f"❌ Error getting invoice: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/<int:invoice_id>', methods=['PUT'])
def update_invoice(invoice_id):
    """Update invoice"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    data = request.json
    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        
        cursor.execute('SELECT id FROM invoices WHERE id = %s', (invoice_id,))
        if not cursor.fetchone():
            return jsonify({'success': False, 'error': 'Invoice not found'}), 404
        
        update_fields = []
        params = []
        
        field_mapping = {
            'amount': data.get('amount'),
            'due_date': data.get('due_date'),
            'status': data.get('status'),
            'notes': data.get('notes'),
            'description': data.get('description')
        }
        
        for field, value in field_mapping.items():
            if value is not None:
                update_fields.append(f"{field} = %s")
                params.append(value)
        
        if not update_fields:
            return jsonify({'success': False, 'error': 'No fields to update'}), 400
        
        update_fields.append("updated_at = %s")
        params.append(datetime.now())
        params.append(invoice_id)
        
        query = f"UPDATE invoices SET {', '.join(update_fields)} WHERE id = %s"
        cursor.execute(query, params)
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Invoice updated successfully'})
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ Error updating invoice: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/<int:invoice_id>', methods=['DELETE'])
def delete_invoice(invoice_id):
    """Delete invoice"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        cursor.execute('DELETE FROM invoices WHERE id = %s RETURNING id', (invoice_id,))
        result = cursor.fetchone()
        conn.commit()
        
        if result:
            return jsonify({'success': True, 'message': 'Invoice deleted successfully'})
        else:
            return jsonify({'success': False, 'error': 'Invoice not found'}), 404
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ Error deleting invoice: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/traveler/<int:traveler_id>', methods=['GET'])
def get_traveler_invoices(traveler_id):
    """Get all invoices for a specific traveler"""
    if 'user_id' not in session and 'traveler_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
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
        result = []
        for inv in invoices:
            inv_dict = dict(inv)
            if inv_dict.get('amount'):
                inv_dict['amount'] = float(inv_dict['amount'])
            result.append(inv_dict)
        
        return jsonify({'success': True, 'invoices': result})
    except Exception as e:
        print(f"❌ Error getting traveler invoices: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/batch/<int:batch_id>', methods=['GET'])
def get_batch_invoices(batch_id):
    """Get all invoices for a specific batch"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        cursor.execute("""
            SELECT 
                i.*,
                t.first_name,
                t.last_name,
                t.passport_no
            FROM invoices i
            LEFT JOIN travelers t ON i.traveler_id = t.id
            WHERE i.batch_id = %s
            ORDER BY i.created_at DESC
        """, (batch_id,))
        
        invoices = cursor.fetchall()
        result = []
        for inv in invoices:
            inv_dict = dict(inv)
            if inv_dict.get('amount'):
                inv_dict['amount'] = float(inv_dict['amount'])
            result.append(inv_dict)
        
        return jsonify({'success': True, 'invoices': result})
    except Exception as e:
        print(f"❌ Error getting batch invoices: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

@bp.route('/export', methods=['GET'])
def export_invoices():
    """Export invoices to CSV"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        cursor.execute("""
            SELECT 
                i.invoice_number,
                i.invoice_date,
                i.amount,
                i.base_amount,
                i.gst_percent,
                i.gst_amount,
                i.tcs_percent,
                i.tcs_amount,
                i.status,
                i.due_date,
                i.description,
                t.first_name,
                t.last_name,
                t.passport_no,
                b.batch_name
            FROM invoices i
            LEFT JOIN travelers t ON i.traveler_id = t.id
            LEFT JOIN batches b ON i.batch_id = b.id
            ORDER BY i.created_at DESC
        """)
        
        invoices = cursor.fetchall()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            'Invoice Number', 'Date', 'Traveler', 'Passport', 'Batch',
            'Base Amount', 'GST %', 'GST Amount', 'TCS %', 'TCS Amount',
            'Total Amount', 'Status', 'Due Date', 'Description'
        ])
        
        for inv in invoices:
            writer.writerow([
                inv['invoice_number'],
                inv['invoice_date'].isoformat() if inv['invoice_date'] else '',
                f"{inv['first_name'] or ''} {inv['last_name'] or ''}".strip(),
                inv['passport_no'] or '',
                inv['batch_name'] or '',
                float(inv['base_amount'] or 0),
                float(inv['gst_percent'] or 5),
                float(inv['gst_amount'] or 0),
                float(inv['tcs_percent'] or 1),
                float(inv['tcs_amount'] or 0),
                float(inv['amount'] or 0),
                inv['status'] or '',
                inv['due_date'].isoformat() if inv['due_date'] else '',
                inv['description'] or ''
            ])
        
        output.seek(0)
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'invoices_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
    except Exception as e:
        print(f"❌ Error exporting invoices: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn:
            release_db(conn, cursor)

print("✅ invoices.py loaded successfully with GST/TCS support!")
