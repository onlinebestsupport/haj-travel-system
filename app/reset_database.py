import sqlite3
import os
from datetime import datetime

# Connect to database
db_path = os.path.join(os.path.dirname(__file__), 'sql', 'alhudha.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("🔴 Deleting all sample data...")

# Disable foreign key constraints temporarily
cursor.execute("PRAGMA foreign_keys = OFF")

# Delete data from all tables
cursor.execute("DELETE FROM payments")
cursor.execute("DELETE FROM receipts")
cursor.execute("DELETE FROM invoices")
cursor.execute("DELETE FROM travelers")
cursor.execute("DELETE FROM batches")
cursor.execute("DELETE FROM users WHERE username IN ('superadmin', 'admin1', 'manager1', 'staff1', 'viewer1')")
cursor.execute("DELETE FROM activity_log")
cursor.execute("DELETE FROM backup_history")

# Reset auto-increment counters
cursor.execute("DELETE FROM sqlite_sequence")
cursor.execute("UPDATE sqlite_sequence SET seq = 0 WHERE name IN ('payments', 'receipts', 'invoices', 'travelers', 'batches', 'users', 'activity_log', 'backup_history')")

# Re-enable foreign keys
cursor.execute("PRAGMA foreign_keys = ON")

conn.commit()
print("✅ All data deleted!")

print("\n🟢 Adding fresh sample data...")

# Insert users
users = [
    ('superadmin', 'admin123', 'Super Admin', 'super@alhudha.com', '9999999999', 'Management', 'super_admin', 
     '{"dashboard":true,"batches":true,"travelers":true,"payments":true,"invoices":true,"receipts":true,"reports":true,"users":true,"frontpage":true,"whatsapp":true,"email":true,"backup":true}', 1),
    ('admin1', 'admin123', 'Admin User', 'admin@alhudha.com', '8888888888', 'Operations', 'admin',
     '{"dashboard":true,"batches":true,"travelers":true,"payments":true,"invoices":true,"receipts":true,"reports":true,"users":false,"frontpage":false,"whatsapp":true,"email":true,"backup":false}', 1),
    ('manager1', 'admin123', 'Manager User', 'manager@alhudha.com', '7777777777', 'Sales', 'manager',
     '{"dashboard":true,"batches":true,"travelers":true,"payments":true,"invoices":true,"receipts":true,"reports":true,"users":false,"frontpage":false,"whatsapp":false,"email":false,"backup":false}', 1),
    ('staff1', 'admin123', 'Staff User', 'staff@alhudha.com', '6666666666', 'Customer Service', 'staff',
     '{"dashboard":true,"batches":false,"travelers":true,"payments":true,"invoices":false,"receipts":true,"reports":false,"users":false,"frontpage":false,"whatsapp":false,"email":false,"backup":false}', 1),
    ('viewer1', 'admin123', 'Viewer User', 'viewer@alhudha.com', '5555555555', 'Accounts', 'viewer',
     '{"dashboard":true,"batches":true,"travelers":true,"payments":true,"invoices":true,"receipts":true,"reports":true,"users":false,"frontpage":false,"whatsapp":false,"email":false,"backup":false}', 1)
]

cursor.executemany('''
    INSERT INTO users (username, password, full_name, email, phone, department, role, permissions, is_active, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
''', users)

print("✅ Users added")

# Insert batches
batches = [
    ('Haj Platinum 2026', 50, 850000, '2026-06-14', '2026-07-31', 'Open', 
     'Premium Haj package with 5-star accommodation near Haram',
     'Day 1: Arrival, Day 2-7: Makkah, Day 8-13: Mina/Arafat/Muzdalifah, Day 14-20: Madinah',
     '5-star hotel, VIP transport, expert guide, meals, visa processing',
     'Airfare not included, personal expenses',
     'Pullman ZamZam Makkah (5-star)',
     'Private AC buses',
     'Full board (breakfast, lunch, dinner)'),
    
    ('Haj Gold 2026', 100, 550000, '2026-06-15', '2026-07-30', 'Open',
     'Standard Haj package with 4-star accommodation',
     'Day 1-20: Standard Haj itinerary',
     '4-star hotel, transport, guide, meals',
     'Airfare, personal expenses',
     'Makkah Hotel (4-star)',
     'Shared AC buses',
     'Half board (breakfast & dinner)'),
    
    ('Umrah Ramadhan Special', 200, 125000, '2026-03-01', '2026-03-20', 'Closing Soon',
     'Special Umrah package for the last 10 days of Ramadhan',
     'Day 1-20: Umrah itinerary with focus on Ramadhan',
     '3-star hotel, transport, guide',
     'Airfare, meals',
     'Dar Al Tawhid (3-star)',
     'Shared buses',
     'Breakfast only'),
    
    ('Haj Silver 2026', 150, 350000, '2026-06-20', '2026-07-28', 'Open',
     'Economy Haj package for budget-conscious pilgrims',
     'Day 1-20: Standard Haj itinerary',
     '3-star hotel, transport, basic guidance',
     'Airfare, meals, extras',
     'Al Safwah Hotel (3-star)',
     'Economy buses',
     'No meals included')
]

cursor.executemany('''
    INSERT INTO batches (batch_name, total_seats, price, departure_date, return_date, status, description,
                        itinerary, inclusions, exclusions, hotel_details, transport_details, meal_plan,
                        created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
''', batches)

print("✅ Batches added")

# Insert travelers
travelers = [
    ('Ahmed', 'Khan', 'Ahmed Khan', 1, 'A1234567', '2020-01-15', '2030-01-14', 'Active', 'Male', '1985-06-15',
     '9876543210', 'ahmed@email.com', '123456789012', 'ABCDE1234F', 'Yes', 'Fully Vaccinated', 'No',
     'Mumbai', 'Mumbai', '123, Green Street, Andheri East, Mumbai - 400093',
     'Abdullah Khan', 'Amina Khan', '', '1234', 'Brother', '9876543211', 'No known allergies',
     '{"blood_group":"O+","allergies":"None"}'),
    
    ('Fatima', 'Begum', 'Fatima Begum', 2, 'B7654321', '2019-08-20', '2029-08-19', 'Active', 'Female', '1990-11-22',
     '8765432109', 'fatima@email.com', '234567890123', 'FGHIJ5678K', 'Pending', 'Partially Vaccinated', 'No',
     'Delhi', 'Delhi', '456, Lotus Apartments, Saket, New Delhi - 110017',
     'Mohammed Ali', 'Zainab Ali', 'Hasan Raza', '5678', 'Husband', '8765432100', 'Diabetic',
     '{"blood_group":"B+","allergies":"None"}'),
    
    ('Mohammed', 'Rafiq', 'Mohammed Rafiq', 3, 'C9876543', '2021-03-10', '2031-03-09', 'Processing', 'Male', '1978-03-08',
     '7654321098', 'rafiq@email.com', '345678901234', 'KLMNO9012P', 'No', 'Not Vaccinated', 'Yes',
     'Hyderabad', 'Hyderabad', '789, Old City, Hyderabad - 500002',
     'Abdul Rafiq', 'Razia Sultana', '', '9012', 'Son', '7654321000', 'Requires wheelchair assistance',
     '{"blood_group":"A+","allergies":"Dust"}')
]

cursor.executemany('''
    INSERT INTO travelers (first_name, last_name, passport_name, batch_id, passport_no,
                          passport_issue_date, passport_expiry_date, passport_status, gender, dob,
                          mobile, email, aadhaar, pan, aadhaar_pan_linked, vaccine_status, wheelchair,
                          place_of_birth, place_of_issue, passport_address, father_name, mother_name, spouse_name,
                          pin, emergency_contact, emergency_phone, medical_notes, extra_fields,
                          created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
''', travelers)

print("✅ Travelers added")

# Update batch booked seats
cursor.execute("UPDATE batches SET booked_seats = (SELECT COUNT(*) FROM travelers WHERE batch_id = 1) WHERE id = 1")
cursor.execute("UPDATE batches SET booked_seats = (SELECT COUNT(*) FROM travelers WHERE batch_id = 2) WHERE id = 2")
cursor.execute("UPDATE batches SET booked_seats = (SELECT COUNT(*) FROM travelers WHERE batch_id = 3) WHERE id = 3")

# Insert payments
payments = [
    (1, 1, 85000, '2026-01-15', 'Bank Transfer', 'TXN123456', 'Booking Amount', 'completed', 'Booking payment received'),
    (1, 1, 85000, '2026-02-15', 'Bank Transfer', 'TXN123457', '1st Installment', 'completed', 'First installment'),
    (2, 2, 550000, '2026-01-20', 'UPI', 'UPI123456', 'Full Payment', 'completed', 'Full payment received'),
    (3, 3, 25000, '2026-02-01', 'Cash', 'CASH001', 'Booking Amount', 'pending', 'Booking amount pending')
]

cursor.executemany('''
    INSERT INTO payments (traveler_id, batch_id, amount, payment_date, payment_method, transaction_id, installment, status, remarks, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
''', payments)

print("✅ Payments added")

# Insert company settings
cursor.execute('''
    INSERT OR REPLACE INTO company_settings (
        id, legal_name, display_name, address_line1, address_line2, city, state, country, pin_code,
        phone, mobile, email, website, gstin, pan, tan, tcs_no, tin, cin, iec, msme,
        bank_name, bank_branch, account_name, account_no, ifsc_code, micr_code, upi_id, qr_code
    ) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', (
    'Alhudha Haj Service P Ltd.', 'Alhudha Haj Travel',
    '2/117, Second Floor, Armenian Street', 'Mannady', 'Chennai', 'Tamil Nadu', 'India', '600001',
    '+91 44 1234 5678', '+91 98765 43210', 'info@alhudha.com', 'www.alhudha.com',
    '33ABCDE1234F1Z5', 'ABCDE1234F', 'ABCD12345E', 'TCS123456789', '33123456789', 'U12345TN1998PTC123456', '1234567890', 'UDYAM-TN-01-1234567',
    'State Bank of India', 'Armenian Street, Chennai', 'Alhudha Haj Service P Ltd.', '12345678901', 'SBIN0012345', '600002123', 'alhudha@okhdfcbank', 'upi://pay?pa=alhudha@okhdfcbank&pn=Alhudha'
))

print("✅ Company settings added")

# Insert frontpage settings
cursor.execute('''
    INSERT OR REPLACE INTO frontpage_settings (
        id, hero_heading, hero_subheading, hero_button_text, hero_button_link,
        packages_title, footer_text, footer_phone, footer_email,
        facebook_url, twitter_url, instagram_url,
        alert_enabled, alert_message, alert_link,
        whatsapp_number, whatsapp_message, booking_email, email_subject
    ) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', (
    'Your Journey to the Holy Land',
    'Experience the spiritual journey of a lifetime with our premium Haj and Umrah packages',
    'View Packages', '#packages',
    'Our Haj & Umrah Packages',
    '© 2026 Alhudha Haj Travel System. All rights reserved.',
    '+91 98765 43210', 'info@alhudha.com',
    '#', '#', '#',
    1, '⚠️ Important: Visa requirements updated for 2026 Hajj. Please submit documents by March 15th.', '/visa-update',
    '919876543210', "Hi, I'm interested in your Haj/Umrah packages. Can you please share more details?",
    'bookings@alhudha.com', 'Package Inquiry: '
))

print("✅ Frontpage settings added")

conn.commit()
conn.close()

print("\n🎉 Database reset complete! Fresh sample data loaded.")
print("\n📊 Sample data summary:")
print("   - Users: 5 (superadmin, admin1, manager1, staff1, viewer1)")
print("   - Batches: 4 (Haj Platinum, Haj Gold, Umrah, Haj Silver)")
print("   - Travelers: 3 (Ahmed Khan, Fatima Begum, Mohammed Rafiq)")
print("   - Payments: 4 transactions")
print("\n🔑 Login credentials:")
print("   - superadmin / admin123")
print("   - admin1 / admin123")
print("   - manager1 / admin123")
