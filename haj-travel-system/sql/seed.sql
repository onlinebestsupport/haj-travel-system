-- Seed sample travelers for testing

-- Insert sample travelers
INSERT INTO travelers (
  first_name, last_name, batch_id, passport_no, 
  passport_issue_date, passport_expiry_date, passport_status,
  gender, dob, mobile, email, aadhaar, pan,
  aadhaar_pan_linked, vaccine_status, wheelchair,
  place_of_birth, place_of_issue, passport_address,
  father_name, mother_name, spouse_name,
  extra_fields
) VALUES 
(
  'Ahmed', 'Mohammed', 1, 'P12345678',
  '2020-01-15', '2030-01-14', 'Active',
  'Male', '1985-05-20', '9876543210', 'ahmed@example.com', '123456789012', 'ABCDE1234F',
  'Yes', 'Fully Vaccinated', 'No',
  'Makkah', 'Riyadh', '123 King Fahd Road, Riyadh',
  'Mohammed Ahmed', 'Fatima Ahmed', 'Aisha Ahmed',
  '{"emergency_contact": "9876543211", "blood_group": "O+", "nationality": "Saudi"}'
),
(
  'Fatima', 'Ali', 1, 'P87654321',
  '2021-03-10', '2031-03-09', 'Active',
  'Female', '1990-08-15', '9876543212', 'fatima@example.com', '876543210987', 'FEDCBA4321',
  'Yes', 'Fully Vaccinated', 'No',
  'Madinah', 'Jeddah', '456 Queen Street, Jeddah',
  'Ali Hassan', 'Zahra Ali', NULL,
  '{"emergency_contact": "9876543213", "blood_group": "A+", "nationality": "Saudi"}'
);