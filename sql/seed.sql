-- Insert default admin
INSERT OR IGNORE INTO users (username, password, email, role) 
VALUES ('admin', 'admin123', 'admin@example.com', 'admin');

-- Insert sample batches
INSERT OR IGNORE INTO batches (id, batch_name, total_seats, price, departure_date, return_date, status, description) VALUES
(1, 'Haj Platinum 2026', 50, 850000, '2026-06-14', '2026-07-31', 'Open', 'Premium Haj package with 5-star accommodation'),
(2, 'Haj Gold 2026', 100, 550000, '2026-06-15', '2026-07-30', 'Open', 'Standard Haj package with 4-star accommodation'),
(3, 'Umrah Ramadhan Special', 200, 125000, '2026-03-01', '2026-03-20', 'Closing Soon', 'Special Umrah package for Ramadhan'),
(4, 'Haj Silver 2026', 150, 350000, '2026-06-20', '2026-07-28', 'Open', 'Economy Haj package with shared accommodation'),
(5, 'Umrah Winter Special', 100, 95000, '2026-12-10', '2026-12-30', 'Open', 'Winter Umrah package');

-- Insert sample travelers
INSERT OR IGNORE INTO travelers (id, first_name, last_name, passport_name, batch_id, passport_no, mobile, email, gender, passport_status, pin) VALUES
(1, 'Ahmed', 'Khan', 'Ahmed Khan', 1, 'Z1234567', '+91 98765 43210', 'ahmed.khan@email.com', 'Male', 'Active', '1234'),
(2, 'Fatima', 'Begum', 'Fatima Begum', 2, 'A7654321', '+91 87654 32109', 'fatima.b@email.com', 'Female', 'Submitted', '5678'),
(3, 'Mohammed', 'Rafiq', 'Mohammed Rafiq', 3, 'B9876543', '+91 76543 21098', 'm.rafiq@email.com', 'Male', 'Processing', '9012');
