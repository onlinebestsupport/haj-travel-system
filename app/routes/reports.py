from flask import Blueprint, request, jsonify, session
from app.database import get_db
from datetime import datetime
import json

bp = Blueprint('reports', __name__, url_prefix='/api/reports')

@bp.route('/generate', methods=['POST'])
def generate_report():
    """Generate report based on parameters"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.json
    report_type = data.get('type')
    start_date = data.get('startDate')
    end_date = data.get('endDate')
    batch_id = data.get('batchId')
    status = data.get('status')
    
    conn, cursor = get_db()
    
    try:
        # Traveler Report
        if report_type == 'traveler':
            query = """
                SELECT t.*, b.batch_name
                FROM travelers t
                LEFT JOIN batches b ON t.batch_id = b.id
                WHERE 1=1
            """
            params = []
            
            if start_date and end_date:
                query += " AND t.created_at BETWEEN %s AND %s"
                params.extend([start_date, end_date])
            
            if batch_id and batch_id != 'all':
                query += " AND t.batch_id = %s"
                params.append(batch_id)
            
            if status and status != 'all':
                query += " AND t.passport_status = %s"
                params.append(status)
            
            query += " ORDER BY t.created_at DESC"
            cursor.execute(query, params)
            travelers = cursor.fetchall()
            
            # Get summary statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(DISTINCT batch_id) as total_batches,
                    SUM(CASE WHEN passport_status = 'Active' THEN 1 ELSE 0 END) as active_count
                FROM travelers
                WHERE 1=1
            """ + (" AND created_at BETWEEN %s AND %s" if start_date and end_date else "") + 
            (f" AND batch_id = {batch_id}" if batch_id and batch_id != 'all' else ""), 
            (params if start_date and end_date else []))
            
            summary = cursor.fetchone()
            
            return jsonify({
                'success': True,
                'report': {
                    'travelers': travelers,
                    'summary': {
                        'total': len(travelers),
                        'total_batches': summary['total_batches'] if summary else 0,
                        'active_count': summary['active_count'] if summary else 0
                    }
                }
            })
        
        # Payment Report
        elif report_type == 'payment':
            query = """
                SELECT 
                    p.*,
                    t.first_name,
                    t.last_name,
                    t.passport_no,
                    b.batch_name
                FROM payments p
                JOIN travelers t ON p.traveler_id = t.id
                JOIN batches b ON p.batch_id = b.id
                WHERE 1=1
            """
            params = []
            
            if start_date and end_date:
                query += " AND p.payment_date BETWEEN %s AND %s"
                params.extend([start_date, end_date])
            
            if batch_id and batch_id != 'all':
                query += " AND p.batch_id = %s"
                params.append(batch_id)
            
            if status and status != 'all':
                query += " AND p.status = %s"
                params.append(status)
            
            query += " ORDER BY p.payment_date DESC"
            cursor.execute(query, params)
            payments = cursor.fetchall()
            
            # Get payment summary by method
            cursor.execute("""
                SELECT 
                    payment_method,
                    COUNT(*) as count,
                    COALESCE(SUM(amount), 0) as total
                FROM payments
                WHERE 1=1
            """ + (" AND payment_date BETWEEN %s AND %s" if start_date and end_date else "") + 
            (f" AND batch_id = {batch_id}" if batch_id and batch_id != 'all' else "") +
            " GROUP BY payment_method",
            (params if start_date and end_date else []))
            
            by_method = cursor.fetchall()
            
            # Get totals
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(CASE WHEN status = 'completed' THEN amount ELSE 0 END), 0) as collected,
                    COALESCE(SUM(CASE WHEN status = 'pending' THEN amount ELSE 0 END), 0) as pending
                FROM payments
                WHERE 1=1
            """ + (" AND payment_date BETWEEN %s AND %s" if start_date and end_date else "") + 
            (f" AND batch_id = {batch_id}" if batch_id and batch_id != 'all' else ""),
            (params if start_date and end_date else []))
            
            totals = cursor.fetchone()
            
            return jsonify({
                'success': True,
                'report': {
                    'payments': payments,
                    'by_method': by_method,
                    'totals': {
                        'collected': float(totals['collected']) if totals['collected'] else 0,
                        'pending': float(totals['pending']) if totals['pending'] else 0
                    }
                }
            })
        
        # Batch Report
        elif report_type == 'batch':
            query = """
                SELECT 
                    b.*,
                    (SELECT COUNT(*) FROM travelers WHERE batch_id = b.id) as booked_seats,
                    (b.total_seats - (SELECT COUNT(*) FROM travelers WHERE batch_id = b.id)) as available_seats,
                    (SELECT COALESCE(SUM(amount), 0) FROM payments WHERE batch_id = b.id) as total_collected
                FROM batches b
                WHERE 1=1
            """
            params = []
            
            if status and status != 'all':
                query += " AND b.status = %s"
                params.append(status)
            
            cursor.execute(query, params)
            batches = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'report': {
                    'batches': batches,
                    'summary': {
                        'total': len(batches),
                        'total_seats': sum(b['total_seats'] for b in batches),
                        'booked_seats': sum(b['booked_seats'] for b in batches),
                        'total_collected': sum(float(b['total_collected']) for b in batches)
                    }
                }
            })
        
        # Daily/Summary Report
        else:
            # Get counts from all tables
            cursor.execute("SELECT COUNT(*) as count FROM travelers")
            traveler_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM batches")
            batch_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COALESCE(SUM(amount), 0) as total FROM payments WHERE status = 'completed'")
            payment_total = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as count FROM payments WHERE status = 'pending'")
            pending_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM users WHERE is_active = true")
            active_users = cursor.fetchone()['count']
            
            # Get recent activity
            cursor.execute("""
                (SELECT 'traveler' as type, first_name || ' ' || last_name as name, created_at as date 
                 FROM travelers ORDER BY created_at DESC LIMIT 5)
                UNION ALL
                (SELECT 'payment' as type, CONCAT(t.first_name, ' ', t.last_name) as name, p.created_at as date 
                 FROM payments p JOIN travelers t ON p.traveler_id = t.id 
                 ORDER BY p.created_at DESC LIMIT 5)
                ORDER BY date DESC LIMIT 10
            """)
            recent_activity = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'report': {
                    'summary': {
                        'totalTravelers': traveler_count,
                        'totalBatches': batch_count,
                        'totalPayments': float(payment_total),
                        'pendingPayments': pending_count,
                        'activeUsers': active_users
                    },
                    'recentActivity': recent_activity
                }
            })
        
    except Exception as e:
        print(f"❌ Report generation error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@bp.route('/export/<format>', methods=['POST'])
def export_report(format):
    """Export report in specified format"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.json
    report_data = data.get('reportData', {})
    
    # This endpoint would handle different export formats
    # For now, return success as frontend handles exports
    return jsonify({
        'success': True,
        'message': f'Report exported as {format}'
    })
