from flask import Blueprint, request, jsonify, session
from app.database import get_db, release_db
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('reports', __name__, url_prefix='/api/reports')

@bp.route('/summary', methods=['GET'])
def summary_report():
    """Generate summary report with key metrics"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    conn = None
    cursor = None
    try:
        conn, cursor = get_db()
        days = request.args.get('days', 30, type=int)
        start_date = datetime.now() - timedelta(days=days)

        # 1. Total travelers
        cursor.execute('SELECT COUNT(*) as count FROM travelers')
        total_travelers = cursor.fetchone()['count']

        # 2. New travelers in period
        cursor.execute('SELECT COUNT(*) as count FROM travelers WHERE created_at >= %s', (start_date,))
        new_travelers = cursor.fetchone()['count']

        # 3. Batches stats
        cursor.execute('SELECT COUNT(*) as count FROM batches')
        total_batches = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM batches WHERE status = 'Open'")
        active_batches = cursor.fetchone()['count']

        # 4. Payments stats (Completed)
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) as total, COUNT(*) as count
            FROM payments
            WHERE status = 'completed'
        """)
        total_payments_data = cursor.fetchone()
        total_collected = float(total_payments_data['total'])

        # 5. Payments stats (Pending)
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) as total
            FROM payments
            WHERE status = 'pending'
        """)
        pending_payments = float(cursor.fetchone()['total'])

        # 6. Payments by method (Grouped)
        cursor.execute("""
            SELECT payment_method, COALESCE(SUM(amount), 0) as total
            FROM payments
            WHERE status = 'completed'
            GROUP BY payment_method
        """)
        payments_by_method_rows = cursor.fetchall()
        payments_by_method = {}
        for row in payments_by_method_rows:
            payments_by_method[row['payment_method']] = float(row['total'])

        # 7. Travelers by batch (for chart)
        cursor.execute("""
            SELECT b.batch_name, COUNT(t.id) as count
            FROM batches b
            LEFT JOIN travelers t ON b.id = t.batch_id
            GROUP BY b.id, b.batch_name
        """)
        travelers_by_batch_rows = cursor.fetchall()
        travelers_by_batch = []
        for row in travelers_by_batch_rows:
            travelers_by_batch.append({
                'batch_name': row['batch_name'] or 'Unassigned',
                'traveler_count': row['count']
            })

        # 8. Occupancy rate
        cursor.execute("SELECT COALESCE(SUM(total_seats), 0) as total_seats FROM batches")
        total_seats = float(cursor.fetchone()['total_seats'])

        cursor.execute("SELECT COALESCE(SUM(booked_seats), 0) as booked_seats FROM batches")
        booked_seats = float(cursor.fetchone()['booked_seats'])

        occupancy_rate = round((booked_seats / total_seats) * 100, 1) if total_seats > 0 else 0

        # 9. Collection rate
        total_expected = total_collected + pending_payments
        collection_rate = round((total_collected / total_expected) * 100, 1) if total_expected > 0 else 0

        # 10. Recent Activity (Last 5)
        cursor.execute("""
            SELECT * FROM activity_log
            ORDER BY created_at DESC
            LIMIT 5
        """)
        recent_activity = cursor.fetchall()

        # ✅ Helper to convert datetime objects to ISO strings
        def serialize_row(row):
            d = dict(row)
            for k, v in list(d.items()):
                if isinstance(v, datetime):
                    d[k] = v.isoformat()
            return d

        # ✅ Normalize response to snake_case expected by frontend
        report_out = {
            'period': f'Last {days} days',
            'start_date': start_date.isoformat(),
            'end_date': datetime.now().isoformat(),
            'total_travelers': int(total_travelers),
            'new_travelers': int(new_travelers),
            'payments': {
                'total': total_collected,
                'count': int(total_payments_data['count'])
            },
            'pending_payments': pending_payments,
            'total_batches': int(total_batches),
            'active_batches': int(active_batches),
            'occupancy_rate': occupancy_rate,
            'collection_rate': collection_rate,
            'payments_by_method': payments_by_method,
            'travelers_by_batch': travelers_by_batch,
            'recent_activity': [serialize_row(r) for r in recent_activity]
        }

        return jsonify({'success': True, 'report': report_out})

    except Exception as e:
        logger.error(f"Summary report error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        release_db(conn, cursor)


@bp.route('/generate', methods=['POST'])
def generate_report():
    """Generate custom report based on parameters"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    data = request.json
    report_type = data.get('type', 'travelers')
    filters_in = data.get('filters', {})
    selected_columns = data.get('columns', [])  # ✅ Get selected columns

    # ✅ Normalize filters
    def get_filter(*keys):
        for k in keys:
            if k in filters_in and filters_in[k] not in (None, ''):
                return filters_in[k]
        return None

    batch_id = get_filter('batchId', 'batch_id')
    status = get_filter('status', 'status')
    start_date = get_filter('startDate', 'start_date')
    end_date = get_filter('endDate', 'end_date')

    conn = None
    cursor = None
    try:
        conn, cursor = get_db()

        # Build query based on report type
        if report_type == 'travelers':
            # ✅ Build SELECT clause dynamically based on selected columns
            if selected_columns and len(selected_columns) > 0:
                # Always include id for record identification
                select_cols = ['id']
                for col in selected_columns:
                    if col != 'id':
                        select_cols.append(col)
                select_clause = ', '.join([f't.{col}' for col in select_cols])
            else:
                # If no columns selected, return all columns
                select_clause = 't.*'

            query = f"""
                SELECT {select_clause}, b.batch_name
                FROM travelers t
                LEFT JOIN batches b ON t.batch_id = b.id
                WHERE 1=1
            """
            params = []
            if batch_id and batch_id != 'all':
                query += ' AND t.batch_id = %s'
                params.append(batch_id)
            if status and status != 'all':
                query += ' AND t.passport_status = %s'
                params.append(status)
            if start_date:
                query += ' AND DATE(t.created_at) >= %s'
                params.append(start_date)
            if end_date:
                query += ' AND DATE(t.created_at) <= %s'
                params.append(end_date)
            query += ' ORDER BY t.created_at DESC LIMIT 500'
            cursor.execute(query, params)
            results = cursor.fetchall()

        elif report_type == 'batches':
            query = """
                SELECT 
                    b.*,
                    COUNT(t.id) as travelers_count,
                    COALESCE(SUM(p.amount), 0) as total_collected
                FROM batches b
                LEFT JOIN travelers t ON b.id = t.batch_id
                LEFT JOIN payments p ON p.batch_id = b.id AND p.status = 'completed'
                WHERE 1=1
            """
            params = []
            if status and status != 'all':
                query += ' AND b.status = %s'
                params.append(status)
            query += ' GROUP BY b.id ORDER BY b.created_at DESC LIMIT 500'
            cursor.execute(query, params)
            results = cursor.fetchall()

        elif report_type == 'financial':
            query = """
                SELECT 
                    DATE_TRUNC('month', payment_date) as month,
                    COUNT(*) as transaction_count,
                    COALESCE(SUM(amount), 0) as total_amount,
                    AVG(amount) as average_amount
                FROM payments
                WHERE status = 'completed'
            """
            params = []
            if start_date:
                query += ' AND DATE(payment_date) >= %s'
                params.append(start_date)
            if end_date:
                query += ' AND DATE(payment_date) <= %s'
                params.append(end_date)
            query += ' GROUP BY DATE_TRUNC(\'month\', payment_date) ORDER BY month DESC LIMIT 500'
            cursor.execute(query, params)
            results = cursor.fetchall()

        else:
            return jsonify({'success': False, 'error': 'Invalid report type'}), 400

        # ✅ Convert rows to dict and serialize datetime objects
        def serialize_row(row):
            d = dict(row)
            for k, v in list(d.items()):
                if isinstance(v, datetime):
                    d[k] = v.isoformat()
            return d

        data_list = [serialize_row(r) for r in results]

        return jsonify({
            'success': True,
            'report': {
                'type': report_type,
                'generated_at': datetime.now().isoformat(),
                'filters': filters_in,
                'count': len(data_list),
                'data': data_list
            }
        })

    except Exception as e:
        logger.error(f"Generate report error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        release_db(conn, cursor)