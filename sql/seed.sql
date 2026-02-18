-- =====================================================
-- HAJ TRAVEL SYSTEM - SEED DATA
-- =====================================================
-- This script adds sample data for testing the system
-- Includes: Additional travelers, payments, and test scenarios
-- =====================================================

-- =====================================================
-- PART 1: ADD MORE BATCHES FOR TESTING
-- =====================================================

INSERT INTO batches (batch_name, departure_date, return_date, total_seats, price, status, description) VALUES
('Haj Executive 2026', '2026-05-08', '2026-06-28', 75, 750000.00, 'Open', 'Executive Haj package with business class flights and 4-star hotels'),
('Haj VIP 2026', '2026-05-01', '2026-07-05', 25, 1200000.00, 'Open', 'VIP Haj package with 5-star hotels, private guides, and luxury transport'),
('Umrah Plus 2026', '2026-02-15', '2026-03-10', 180, 145000.00, 'Open', 'Extended Umrah package with additional Ziyarat visits'),
('Umrah Comfort 2026', '2026-04-20', '2026-05-10', 220, 115000.00, 'Open', 'Comfort Umrah package with upgraded accommodations'),
('Haj Silver 2027', '2027-05-20', '2027-06-25', 200, 375000.00, 'Coming Soon', 'Early bird Haj Silver 2027 - Limited seats'),
('Haj Gold 2027', '2027-05-15', '2027-06-30', 120, 575000.00, 'Coming Soon', 'Early bird Haj Gold 2027 - Register now'),
('Umrah Winter 2027', '2027-01-15', '2027-02-05', 250, 100000.00, 'Coming Soon', 'Winter Umrah 2027 - Advanced booking'),
('Ramadhan Special 2027', '2027-03-20', '2027-04-15', 180, 135000.00, 'Coming Soon', 'Ramadhan Umrah 2027 - Early bird special')
ON CONFLICT (batch_name) DO NOTHING;

-- =====================================================
-- PART 2: ADD MORE TRAVELERS FOR COMPREHENSIVE TESTING
-- =====================================================

DO $$
DECLARE
    executive_id INTEGER;
    vip_id INTEGER;
    umrah_plus_id INTEGER;
    umrah_comfort_id INTEGER;
    silver_2027_id INTEGER;
    gold_2027_id INTEGER;
    winter_2027_id INTEGER;
    ramadhan_2027_id INTEGER;
BEGIN
    -- Get new batch IDs
    SELECT id INTO executive_id FROM batches WHERE batch_name = 'Haj Executive 2026';
    SELECT id INTO vip_id FROM batches WHERE batch_name = 'Haj VIP 2026';
    SELECT id INTO umrah_plus_id FROM batches WHERE batch_name = 'Umrah Plus 2026';
    SELECT id INTO umrah_comfort_id FROM batches WHERE batch_name = 'Umrah Comfort 2026';
    SELECT id INTO silver_2027_id FROM batches WHERE batch_name = 'Haj Silver 2027';
    SELECT id INTO gold_2027_id FROM batches WHERE batch_name = 'Haj Gold 2027';
    SELECT id INTO winter_2027_id FROM batches WHERE batch_name = 'Umrah Winter 2027';
    SELECT id INTO ramadhan_2027_id FROM batches WHERE batch_name = 'Ramadhan Special 2027';

    -- Insert additional travelers
    INSERT INTO travelers (
        first_name, last_name, batch_id, passport_no, passport_issue_date, passport_expiry_date,
        passport_status, gender, dob, mobile, email, aadhaar, pan, aadhaar_pan_linked,
        vaccine_status, wheelchair, place_of_birth, place_of_issue, passport_address,
        father_name, mother_name, spouse_name, extra_fields, pin
    ) VALUES
    -- Traveler 11: Abdullah Malik (Haj Executive)
    ('Abdullah', 'Malik', executive_id, 'K1234567', '2022-06-10', '2032-06-09',
     'Active', 'Male', '1980-09-15', '9876543221', 'abdullah.malik@email.com',
     '123456789013', 'ABCDE2345G', 'Yes', 'Fully Vaccinated', 'No',
     'Riyadh', 'Riyadh', 'Villa 45, Diplomatic Quarter, Riyadh, Saudi Arabia',
     'Malik Ahmed', 'Aisha Malik', 'Nadia Malik',
     '{"emergency_contact": "9876543222", "blood_group": "A+", "nationality": "Saudi", "profession": "Businessman"}', '1234'),

    -- Traveler 12: Amina Hassan (Haj VIP)
    ('Amina', 'Hassan', vip_id, 'L7654321', '2021-11-05', '2031-11-04',
     'Active', 'Female', '1985-04-22', '9876543223', 'amina.hassan@email.com',
     '234567890124', 'FGHIJ6789L', 'Yes', 'Booster', 'No',
     'Dubai', 'Dubai', 'Apartment 2301, Burj Khalifa, Dubai, UAE',
     'Hassan Mohammed', 'Fatima Hassan', 'Omar Hassan',
     '{"emergency_contact": "9876543224", "blood_group": "B+", "nationality": "UAE", "profession": "Doctor"}', '2234'),

    -- Traveler 13: Bilal Ahmed (Umrah Plus)
    ('Bilal', 'Ahmed', umrah_plus_id, 'M9876543', '2023-01-20', '2033-01-19',
     'Active', 'Male', '1992-07-30', '9876543225', 'bilal.ahmed@email.com',
     '345678901235', 'KLMNO1234P', 'No', 'Fully Vaccinated', 'No',
     'Karachi', 'Karachi', 'House 78, Defence Phase 5, Karachi, Pakistan',
     'Ahmed Khan', 'Saira Ahmed', NULL,
     '{"emergency_contact": "9876543226", "blood_group": "O+", "nationality": "Pakistani", "profession": "Engineer"}', '3234'),

    -- Traveler 14: Fatima Zahra (Umrah Comfort)
    ('Fatima', 'Zahra', umrah_comfort_id, 'N4567890', '2022-08-15', '2032-08-14',
     'Active', 'Female', '1988-12-10', '9876543227', 'fatima.zahra@email.com',
     '456789012346', 'PQRST5678V', 'Pending', 'Partially Vaccinated', 'Yes',
     'Casablanca', 'Casablanca', '12 Rue des Fleurs, Casablanca, Morocco',
     'Zahra Mohammed', 'Khadija Zahra', 'Hassan Ali',
     '{"emergency_contact": "9876543228", "blood_group": "AB+", "nationality": "Moroccan", "profession": "Teacher"}', '4234'),

    -- Traveler 15: Hassan Raza (Haj Silver 2027)
    ('Hassan', 'Raza', silver_2027_id, 'O1122334', '2023-03-10', '2033-03-09',
     'Active', 'Male', '1975-11-25', '9876543229', 'hassan.raza@email.com',
     '567890123457', 'UVWXY8901Z', 'Yes', 'Fully Vaccinated', 'No',
     'Lahore', 'Lahore', '45 Gulberg III, Lahore, Pakistan',
     'Raza Ali', 'Zainab Raza', 'Sadia Raza',
     '{"emergency_contact": "9876543230", "blood_group": "B-", "nationality": "Pakistani", "profession": "Lawyer"}', '5234'),

    -- Traveler 16: Zainab Abbas (Haj Gold 2027)
    ('Zainab', 'Abbas', gold_2027_id, 'P9988776', '2021-09-18', '2031-09-17',
     'Active', 'Female', '1990-05-05', '9876543231', 'zainab.abbas@email.com',
     '678901234568', 'ABCDE1235F', 'Yes', 'Booster', 'No',
     'Istanbul', 'Istanbul', 'Levent Mahallesi, Istanbul, Turkey',
     'Abbas Hussain', 'Fatima Abbas', NULL,
     '{"emergency_contact": "9876543232", "blood_group": "A-", "nationality": "Turkish", "profession": "Architect"}', '6234'),

    -- Traveler 17: Yusuf Ibrahim (Umrah Winter 2027)
    ('Yusuf', 'Ibrahim', winter_2027_id, 'Q1122335', '2022-12-01', '2032-11-30',
     'Active', 'Male', '1983-08-12', '9876543233', 'yusuf.i@email.com',
     '789012345679', 'FGHIJ2346K', 'No', 'Fully Vaccinated', 'No',
     'Cairo', 'Cairo', '15 Zamalek, Cairo, Egypt',
     'Ibrahim Said', 'Mariam Ibrahim', 'Leila Ibrahim',
     '{"emergency_contact": "9876543234", "blood_group": "O-", "nationality": "Egyptian", "profession": "Professor"}', '7234'),

    -- Traveler 18: Maryam Hassan (Ramadhan 2027)
    ('Maryam', 'Hassan', ramadhan_2027_id, 'R5566778', '2023-05-20', '2033-05-19',
     'Active', 'Female', '1995-10-18', '9876543235', 'maryam.h@email.com',
     '890123456780', 'KLMNO3457P', 'Pending', 'Partially Vaccinated', 'No',
     'London', 'London', '25 Edgware Road, London, UK',
     'Hassan Yusuf', 'Amina Hassan', NULL,
     '{"emergency_contact": "9876543236", "blood_group": "AB-", "nationality": "British", "profession": "Designer"}', '8234'),

    -- Traveler 19: Ibrahim Khalil (Haj Executive - second)
    ('Ibrahim', 'Khalil', executive_id, 'S9988777', '2022-04-14', '2032-04-13',
     'Active', 'Male', '1970-02-28', '9876543237', 'ibrahim.khalil@email.com',
     '901234567891', 'PQRST4568U', 'Yes', 'Fully Vaccinated', 'No',
     'Kuala Lumpur', 'Kuala Lumpur', '88 Jalan Ampang, Kuala Lumpur, Malaysia',
     'Khalil Abdullah', 'Nor Khalil', 'Sarah Khalil',
     '{"emergency_contact": "9876543238", "blood_group": "A+", "nationality": "Malaysian", "profession": "Businessman"}', '9234'),

    -- Traveler 20: Khadija Omar (Umrah Plus - second)
    ('Khadija', 'Omar', umrah_plus_id, 'T2233445', '2023-02-25', '2033-02-24',
     'Active', 'Female', '1987-06-17', '9876543239', 'khadija.omar@email.com',
     '012345678902', 'UVWXY5679Z', 'No', 'Booster', 'No',
     'Jakarta', 'Jakarta', 'Jl. Sudirman No. 45, Jakarta, Indonesia',
     'Omar Hasyim', 'Aisyah Omar', 'Ahmad Omar',
     '{"emergency_contact": "9876543240", "blood_group": "B+", "nationality": "Indonesian", "profession": "Doctor"}', '0334')
    ON CONFLICT (passport_no) DO NOTHING;

    -- Update booked seats
    UPDATE batches SET booked_seats = (SELECT COUNT(*) FROM travelers WHERE batch_id = batches.id);
END $$;

-- =====================================================
-- PART 3: ADD MORE PAYMENTS FOR TESTING
-- =====================================================

DO $$
DECLARE
    t_id INTEGER;
BEGIN
    -- Add payments for traveler 11 (Abdullah)
    SELECT id INTO t_id FROM travelers WHERE passport_no = 'K1234567';
    INSERT INTO payments (traveler_id, installment, amount, due_date, payment_date, payment_method, status, remarks) VALUES
    (t_id, 'Booking Amount', 100000, '2026-02-01', '2026-01-28', 'Bank Transfer', 'Paid', 'Executive package booking'),
    (t_id, '1st Installment', 200000, '2026-03-01', '2026-02-25', 'Credit Card', 'Paid', 'First installment - online'),
    (t_id, '2nd Installment', 200000, '2026-04-01', NULL, NULL, 'Pending', NULL),
    (t_id, 'Final Payment', 250000, '2026-05-01', NULL, NULL, 'Pending', NULL)
    ON CONFLICT DO NOTHING;

    -- Payments for traveler 12 (Amina)
    SELECT id INTO t_id FROM travelers WHERE passport_no = 'L7654321';
    INSERT INTO payments (traveler_id, installment, amount, due_date, payment_date, payment_method, status, remarks) VALUES
    (t_id, 'Full Payment', 1200000, '2026-02-15', '2026-02-10', 'Bank Transfer', 'Paid', 'VIP package full payment - wire transfer')
    ON CONFLICT DO NOTHING;

    -- Payments for traveler 13 (Bilal)
    SELECT id INTO t_id FROM travelers WHERE passport_no = 'M9876543';
    INSERT INTO payments (traveler_id, installment, amount, due_date, payment_date, payment_method, status, remarks) VALUES
    (t_id, 'Booking Amount', 35000, '2026-01-20', '2026-01-15', 'UPI', 'Paid', 'PhonePe payment'),
    (t_id, '1st Installment', 55000, '2026-02-20', '2026-02-18', 'Credit Card', 'Paid', 'Online payment'),
    (t_id, '2nd Installment', 55000, '2026-03-20', NULL, NULL, 'Pending', NULL)
    ON CONFLICT DO NOTHING;

    -- Payments for traveler 14 (Fatima)
    SELECT id INTO t_id FROM travelers WHERE passport_no = 'N4567890';
    INSERT INTO payments (traveler_id, installment, amount, due_date, payment_date, payment_method, status, remarks) VALUES
    (t_id, 'Booking Amount', 30000, '2026-02-10', '2026-02-05', 'Cash', 'Paid', 'Cash payment at office'),
    (t_id, '1st Installment', 45000, '2026-03-10', NULL, NULL, 'Pending', NULL),
    (t_id, 'Final Payment', 40000, '2026-04-10', NULL, NULL, 'Pending', NULL)
    ON CONFLICT DO NOTHING;

    -- Payments for traveler 15 (Hassan) - Haj Silver 2027 (early bird)
    SELECT id INTO t_id FROM travelers WHERE passport_no = 'O1122334';
    INSERT INTO payments (traveler_id, installment, amount, due_date, payment_date, payment_method, status, remarks) VALUES
    (t_id, 'Booking Amount', 50000, '2026-02-28', '2026-02-20', 'Bank Transfer', 'Paid', 'Early bird booking'),
    (t_id, '1st Installment', 100000, '2026-04-30', NULL, NULL, 'Pending', NULL)
    ON CONFLICT DO NOTHING;

    -- Payments for traveler 16 (Zainab) - Haj Gold 2027
    SELECT id INTO t_id FROM travelers WHERE passport_no = 'P9988776';
    INSERT INTO payments (traveler_id, installment, amount, due_date, payment_date, payment_method, status, remarks) VALUES
    (t_id, 'Booking Amount', 75000, '2026-03-15', '2026-03-10', 'Credit Card', 'Paid', 'Online booking with discount'),
    (t_id, '1st Installment', 150000, '2026-05-15', NULL, NULL, 'Pending', NULL),
    (t_id, '2nd Installment', 150000, '2026-07-15', NULL, NULL, 'Pending', NULL),
    (t_id, 'Final Payment', 200000, '2026-09-15', NULL, NULL, 'Pending', NULL)
    ON CONFLICT DO NOTHING;

    -- Payments for traveler 17 (Yusuf) - Umrah Winter 2027
    SELECT id INTO t_id FROM travelers WHERE passport_no = 'Q1122335';
    INSERT INTO payments (traveler_id, installment, amount, due_date, payment_date, payment_method, status, remarks) VALUES
    (t_id, 'Full Payment', 100000, '2026-04-01', '2026-03-25', 'Bank Transfer', 'Paid', 'Full payment early bird')
    ON CONFLICT DO NOTHING;

    -- Payments for traveler 18 (Maryam) - Ramadhan 2027
    SELECT id INTO t_id FROM travelers WHERE passport_no = 'R5566778';
    INSERT INTO payments (traveler_id, installment, amount, due_date, payment_date, payment_method, status, remarks) VALUES
    (t_id, 'Booking Amount', 40000, '2026-05-01', '2026-04-25', 'UPI', 'Paid', 'Google Pay'),
    (t_id, '1st Installment', 50000, '2026-07-01', NULL, NULL, 'Pending', NULL)
    ON CONFLICT DO NOTHING;

    -- Payments for traveler 19 (Ibrahim) - Executive second
    SELECT id INTO t_id FROM travelers WHERE passport_no = 'S9988777';
    INSERT INTO payments (traveler_id, installment, amount, due_date, payment_date, payment_method, status, remarks) VALUES
    (t_id, 'Booking Amount', 150000, '2026-01-05', '2026-01-02', 'Bank Transfer', 'Paid', 'New year booking'),
    (t_id, '1st Installment', 200000, '2026-02-05', '2026-02-01', 'Credit Card', 'Paid', 'Regular payment'),
    (t_id, '2nd Installment', 200000, '2026-03-05', NULL, NULL, 'Pending', NULL)
    ON CONFLICT DO NOTHING;

    -- Payments for traveler 20 (Khadija) - Umrah Plus second
    SELECT id INTO t_id FROM travelers WHERE passport_no = 'T2233445';
    INSERT INTO payments (traveler_id, installment, amount, due_date, payment_date, payment_method, status, remarks) VALUES
    (t_id, 'Booking Amount', 45000, '2026-02-20', '2026-02-15', 'Cash', 'Paid', 'Walk-in booking'),
    (t_id, '1st Installment', 50000, '2026-03-20', '2026-03-18', 'UPI', 'Paid', 'PhonePe'),
    (t_id, '2nd Installment', 50000, '2026-04-20', NULL, NULL, 'Pending', NULL)
    ON CONFLICT DO NOTHING;

END $$;

-- =====================================================
-- PART 4: CREATE TEST SCENARIOS
-- =====================================================

-- Scenario 1: Travelers with complete documentation
UPDATE travelers SET 
    passport_scan = 'passport_' || passport_no || '.pdf',
    aadhaar_scan = 'aadhaar_' || passport_no || '.pdf',
    pan_scan = 'pan_' || passport_no || '.pdf',
    vaccine_scan = 'vaccine_' || passport_no || '.pdf'
WHERE id IN (1, 2, 5, 11, 12, 15, 17);

-- Scenario 2: Travelers with missing documents
UPDATE travelers SET 
    passport_scan = NULL,
    aadhaar_scan = NULL,
    pan_scan = NULL,
    vaccine_scan = NULL
WHERE id IN (3, 7, 9, 13, 18);

-- Scenario 3: Travelers with partial documents
UPDATE travelers SET 
    passport_scan = 'passport_' || passport_no || '.pdf',
    vaccine_scan = 'vaccine_' || passport_no || '.pdf'
WHERE id IN (4, 6, 8, 10, 14, 16, 19, 20);

-- Scenario 4: Create some payment reversals for testing
INSERT INTO payment_reversals (original_payment_id, amount, reason, reversed_by, is_full_reversal)
SELECT 
    p.id,
    p.amount * 0.5,
    'Customer requested partial refund due to payment error',
    1,
    false
FROM payments p
WHERE p.traveler_id IN (3, 8)
AND p.status = 'Paid'
LIMIT 2;

-- Update original payment status for reversals
UPDATE payments SET status = 'Partially Reversed' 
WHERE id IN (SELECT original_payment_id FROM payment_reversals);

-- Scenario 5: Create some invoices
INSERT INTO invoices (
    traveler_id, invoice_number, base_amount, gst_rate, gst_amount,
    tcs_rate, tcs_amount, total_amount, total_paid, balance_due, generated_by
)
SELECT 
    t.id,
    'INV-2026-' || LPAD(t.id::TEXT, 4, '0'),
    b.price,
    5,
    b.price * 0.05,
    0.5,
    (b.price * 1.05) * 0.005,
    (b.price * 1.05) * 1.005,
    COALESCE(SUM(p.amount) FILTER (WHERE p.status = 'Paid'), 0),
    (b.price * 1.05) * 1.005 - COALESCE(SUM(p.amount) FILTER (WHERE p.status = 'Paid'), 0),
    1
FROM travelers t
JOIN batches b ON t.batch_id = b.id
LEFT JOIN payments p ON t.id = p.traveler_id
WHERE t.id IN (1, 2, 5, 11, 12)
GROUP BY t.id, b.id, b.price
ON CONFLICT DO NOTHING;

-- =====================================================
-- PART 5: CREATE PAYMENT SCHEDULES FOR FUTURE
-- =====================================================

DO $$
DECLARE
    t_record RECORD;
    batch_price DECIMAL;
    installments TEXT[] := ARRAY['Booking Amount', '1st Installment', '2nd Installment', '3rd Installment', 'Final Payment'];
    installment_amount DECIMAL;
    due_date DATE;
    i INTEGER;
BEGIN
    FOR t_record IN SELECT t.id, b.price, b.departure_date FROM travelers t JOIN batches b ON t.batch_id = b.id WHERE t.id > 15 LOOP
        -- Create future payment schedule if not exists
        IF NOT EXISTS (SELECT 1 FROM payments WHERE traveler_id = t_record.id) THEN
            batch_price := t_record.price;
            
            -- Create 4 installments
            FOR i IN 1..4 LOOP
                IF i = 1 THEN
                    installment_amount := batch_price * 0.2; -- 20% booking
                ELSIF i = 4 THEN
                    installment_amount := batch_price * 0.3; -- 30% final
                ELSE
                    installment_amount := batch_price * 0.25; -- 25% each for 2nd and 3rd
                END IF;
                
                due_date := t_record.departure_date - (5 - i) * 30; -- 4,3,2,1 months before departure
                
                INSERT INTO payments (traveler_id, installment, amount, due_date, status)
                VALUES (t_record.id, installments[i], installment_amount, due_date, 'Pending');
            END LOOP;
        END IF;
    END LOOP;
END $$;

-- =====================================================
-- PART 6: CREATE LOGIN LOGS (SAMPLE DATA)
-- =====================================================

INSERT INTO login_logs (user_id, login_time, logout_time, ip_address, user_agent) VALUES
(1, NOW() - INTERVAL '2 hours', NOW() - INTERVAL '1 hour', '192.168.1.100', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'),
(1, NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 day' + INTERVAL '3 hours', '192.168.1.100', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'),
(2, NOW() - INTERVAL '12 hours', NOW() - INTERVAL '11 hours', '192.168.1.101', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/17.0'),
(3, NOW() - INTERVAL '3 days', NOW() - INTERVAL '3 days' + INTERVAL '2 hours', '192.168.1.102', 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15'),
(4, NOW() - INTERVAL '5 days', NULL, '192.168.1.103', 'Mozilla/5.0 (Linux; Android 14) Chrome/120.0.0.0 Mobile'),
(5, NOW() - INTERVAL '6 hours', NOW() - INTERVAL '5 hours', '192.168.1.104', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Edge/120.0.0.0');

-- =====================================================
-- PART 7: CREATE BACKUP RECORDS (SAMPLE)
-- =====================================================

INSERT INTO backups (filename, size_bytes, traveler_count, batch_count, payment_count, status, created_by, created_at) VALUES
('backup_20260201_000000.zip', 15728640, 10, 8, 18, 'Success', 1, NOW() - INTERVAL '15 days'),
('backup_20260205_000000.zip', 16777216, 12, 9, 22, 'Success', 1, NOW() - INTERVAL '11 days'),
('backup_20260210_000000.zip', 18874368, 15, 10, 28, 'Success', 1, NOW() - INTERVAL '6 days'),
('backup_20260214_000000.zip', 20971520, 18, 11, 35, 'Success', 1, NOW() - INTERVAL '2 days'),
('backup_20260215_020000.zip', 11534336, 16, 10, 30, 'Failed', 1, NOW() - INTERVAL '1 day'),
('backup_20260215_180000.zip', 22020096, 20, 12, 40, 'Success', 1, NOW() - INTERVAL '6 hours');

-- =====================================================
-- PART 8: UPDATE BATCH STATUSES BASED ON DATES
-- =====================================================

-- Update batches that are close to departure
UPDATE batches 
SET status = 'Closing Soon' 
WHERE departure_date BETWEEN CURRENT_DATE + INTERVAL '30 days' AND CURRENT_DATE + INTERVAL '60 days'
AND status = 'Open';

-- Update batches that are full
UPDATE batches 
SET status = 'Full' 
WHERE booked_seats >= total_seats
AND status IN ('Open', 'Closing Soon');

-- Update past batches
UPDATE batches 
SET status = 'Completed' 
WHERE return_date < CURRENT_DATE
AND status NOT IN ('Completed', 'Cancelled');

-- =====================================================
-- PART 9: VERIFICATION QUERIES
-- =====================================================

-- Show summary of all data
SELECT 'TOTAL TRAVELERS' as metric, COUNT(*) as value FROM travelers
UNION ALL
SELECT 'TOTAL BATCHES', COUNT(*) FROM batches
UNION ALL
SELECT 'TOTAL PAYMENTS', COUNT(*) FROM payments
UNION ALL
SELECT 'TOTAL PAID AMOUNT', SUM(amount)::TEXT FROM payments WHERE status = 'Paid'
UNION ALL
SELECT 'TOTAL PENDING AMOUNT', SUM(amount)::TEXT FROM payments WHERE status = 'Pending'
UNION ALL
SELECT 'TOTAL USERS', COUNT(*) FROM admin_users;

-- Show batch occupancy
SELECT 
    batch_name,
    total_seats,
    booked_seats,
    (total_seats - booked_seats) as available,
    ROUND((booked_seats::DECIMAL / total_seats * 100), 2) as occupancy_percent,
    status
FROM batches
ORDER BY departure_date;

-- Show payment status summary by batch
SELECT 
    b.batch_name,
    COUNT(DISTINCT t.id) as travelers,
    COUNT(p.id) as payments,
    SUM(CASE WHEN p.status = 'Paid' THEN p.amount ELSE 0 END) as collected,
    SUM(CASE WHEN p.status = 'Pending' THEN p.amount ELSE 0 END) as pending
FROM batches b
LEFT JOIN travelers t ON b.id = t.batch_id
LEFT JOIN payments p ON t.id = p.traveler_id
GROUP BY b.id, b.batch_name
ORDER BY b.departure_date;

-- Show recent registrations
SELECT 
    first_name || ' ' || last_name as name,
    passport_no,
    batch_name,
    created_at
FROM travelers t
LEFT JOIN batches b ON t.batch_id = b.id
ORDER BY created_at DESC
LIMIT 10;

-- =====================================================
-- PART 10: CREATE TEST USER FOR DIFFERENT ROLES
-- =====================================================

-- Add test users with different roles
INSERT INTO admin_users (username, password_hash, email, full_name, is_active) VALUES
('test_admin', 'L5Ks5qk2Y8O+c1CXzX6hWpPxG69RyB5+2n4O7U+DmVQ=', 'test.admin@alhudha.com', 'Test Admin', true),
('test_manager', 'L5Ks5qk2Y8O+c1CXzX6hWpPxG69RyB5+2n4O7U+DmVQ=', 'test.manager@alhudha.com', 'Test Manager', true),
('test_staff', 'L5Ks5qk2Y8O+c1CXzX6hWpPxG69RyB5+2n4O7U+DmVQ=', 'test.staff@alhudha.com', 'Test Staff', true),
('test_viewer', 'L5Ks5qk2Y8O+c1CXzX6hWpPxG69RyB5+2n4O7U+DmVQ=', 'test.viewer@alhudha.com', 'Test Viewer', true)
ON CONFLICT (username) DO NOTHING;

-- Assign roles to test users
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id FROM admin_users u, roles r
WHERE u.username = 'test_admin' AND r.name = 'admin'
ON CONFLICT DO NOTHING;

INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id FROM admin_users u, roles r
WHERE u.username = 'test_manager' AND r.name = 'manager'
ON CONFLICT DO NOTHING;

INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id FROM admin_users u, roles r
WHERE u.username = 'test_staff' AND r.name = 'staff'
ON CONFLICT DO NOTHING;

INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id FROM admin_users u, roles r
WHERE u.username = 'test_viewer' AND r.name = 'viewer'
ON CONFLICT DO NOTHING;

-- =====================================================
-- PART 11: FINAL SUCCESS MESSAGE
-- =====================================================

DO $$
DECLARE
    traveler_count INTEGER;
    batch_count INTEGER;
    payment_count INTEGER;
    paid_sum DECIMAL;
    pending_sum DECIMAL;
BEGIN
    SELECT COUNT(*) INTO traveler_count FROM travelers;
    SELECT COUNT(*) INTO batch_count FROM batches;
    SELECT COUNT(*) INTO payment_count FROM payments;
    SELECT COALESCE(SUM(amount), 0) INTO paid_sum FROM payments WHERE status = 'Paid';
    SELECT COALESCE(SUM(amount), 0) INTO pending_sum FROM payments WHERE status = 'Pending';
    
    RAISE NOTICE '==================================================';
    RAISE NOTICE '✅ SEED DATA ADDED SUCCESSFULLY';
    RAISE NOTICE '==================================================';
    RAISE NOTICE '📊 DATABASE SUMMARY:';
    RAISE NOTICE '   Travelers: %', traveler_count;
    RAISE NOTICE '   Batches: %', batch_count;
    RAISE NOTICE '   Payments: %', payment_count;
    RAISE NOTICE '   Total Collected: ₹%', paid_sum;
    RAISE NOTICE '   Pending Amount: ₹%', pending_sum;
    RAISE NOTICE '==================================================';
    RAISE NOTICE '🔑 TEST CREDENTIALS:';
    RAISE NOTICE '   superadmin / admin123 (Super Admin)';
    RAISE NOTICE '   test_admin / admin123 (Admin)';
    RAISE NOTICE '   test_manager / admin123 (Manager)';
    RAISE NOTICE '   test_staff / admin123 (Staff)';
    RAISE NOTICE '   test_viewer / admin123 (Viewer)';
    RAISE NOTICE '==================================================';
    RAISE NOTICE '👤 TRAVELER LOGIN SAMPLES:';
    RAISE NOTICE '   Passport: A1234567, PIN: 1234';
    RAISE NOTICE '   Passport: B7654321, PIN: 2234';
    RAISE NOTICE '   Passport: C9876543, PIN: 3234';
    RAISE NOTICE '==================================================';
END $$;