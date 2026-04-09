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

        # Check if invoice exists
        cursor.execute('SELECT id FROM invoices WHERE id = %s', (invoice_id,))
        if not cursor.fetchone():
            return jsonify({'success': False, 'error': 'Invoice not found'}), 404

        # Build update query dynamically - only update columns that exist
        updates = []
        values = []
        
        # Map frontend fields to database columns (using actual column names)
        field_mapping = {
            'amount': 'amount',
            'paid_amount': 'paid_amount',
            'due_date': 'due_date',
            'status': 'status'
        }
        
        for frontend_field, db_field in field_mapping.items():
            if frontend_field in data:
                updates.append(f"{db_field} = %s")
                values.append(data[frontend_field])
        
        if updates:
            values.append(datetime.now())
            values.append(invoice_id)
            query = f"UPDATE invoices SET {', '.join(updates)}, updated_at = %s WHERE id = %s"
            cursor.execute(query, values)
            conn.commit()
        
        return jsonify({'success': True, 'message': 'Invoice updated successfully'})
        
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        if conn:
            release_db(conn, cursor)