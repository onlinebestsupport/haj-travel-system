import psycopg2
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

print("🚀 Adding test data with correct columns...")

# Add a batch with all required fields
try:
        cursor.execute("""
    INSERT INTO batches (
        batch_name, total_seats, booked_seats, price, 
        departure_date, return_date, status, created_at
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    RETURNING id
""", (
    'Haj Platinum 2026',           # batch_name
    50,                             # total_seats
    0,                               # booked_seats
    850000.00,                       # price
    datetime.now() + timedelta(days=30),  # departure_date
    datetime.now() + timedelta(days=60),  # return_date
    'Open',                          # status
    datetime.now()                    # created_at
))
batch_id = cursor.fetchone()[0]
print(f"✅ Added batch with ID: {batch_id}")

# Add a traveler with all required fields
cursor.execute("""
    INSERT INTO travelers (
        first_name, last_name, passport_name, batch_id,
        passport_no, passport_issue_date, passport_expiry_date,
        passport_status, gender, dob, mobile, email,
        aadhaar, pan, aadhaar_pan_linked, vaccine_status,
        wheelchair, place_of_birth, place_of_issue, passport_address,
        father_name, mother_name, spouse_name, pin,
        emergency_contact, emergency_phone, medical_notes,
        created_at
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s
    )
""", (
    'Ahmed', 'Khan', 'Ahmed Khan', batch_id,
    'A1234567', '2020-01-15', '2030-01-14',
    'Active', 'Male', '1985-06-15', '9876543210', 'ahmed@example.com',
    '123456789012', 'ABCDE1234F', 'Yes', 'Fully Vaccinated',
    'No', 'Mumbai', 'Mumbai', '123, Green Street, Mumbai',
    'Abdullah Khan', 'Amina Khan', 'N/A', '1234',
    'Brother', '9876543211', 'No allergies',
    datetime.now()
))
print("✅ Added test traveler")

# Add another batch
cursor.execute("""
    INSERT INTO batches (
        batch_name, total_seats, booked_seats, price, 
        departure_date, return_date, status, created_at
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    RETURNING id
""", (
    'Haj Gold 2026',                # batch_name
    40,                              # total_seats
    0,                               # booked_seats
    550000.00,                       # price
    datetime.now() + timedelta(days=45),  # departure_date
    datetime.now() + timedelta(days=75),  # return_date
    'Open',                          # status
    datetime.now()                    # created_at
))
batch_id2 = cursor.fetchone()[0]
print(f"✅ Added second batch with ID: {batch_id2}")

# Add another traveler
cursor.execute("""
    INSERT INTO travelers (
        first_name, last_name, passport_name, batch_id,
        passport_no, mobile, email, passport_status,
        gender, created_at
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
""", (
    'Fatima', 'Begum', 'Fatima Begum', batch_id2,
    'B7654321', '8765432109', 'fatima@example.com',
    'Active', 'Female', datetime.now()
))
print("✅ Added second test traveler")

conn.commit()
print(f"\n✅ Successfully added:")
print(f"   - 2 batches")
print(f"   - 2 travelers")

# Verify the data
cursor.execute("SELECT COUNT(*) FROM batches")
batch_count = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM travelers")
traveler_count = cursor.fetchone()[0]
print(f"\n📊 Current counts:")
print(f"   - Batches: {batch_count}")
print(f"   - Travelers: {traveler_count}")

cursor.close()
conn.close()
    finally:
        release_db(conn, cursor)
print("\n✅ Done! Refresh your dashboard (F5)")