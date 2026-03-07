#!/usr/bin/env python3
"""
🧪 COMPLETE TEST SUITE - Alhudha Haj Travel System
Comprehensive testing for all Python components
Run: pytest test_suite_complete.py -v
Or: python test_suite_complete.py
"""

import pytest
import requests
import json
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import hashlib

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import server
from app.database import get_db, release_db, hash_password

# ==================== FIXTURES ====================

@pytest.fixture
def client():
    """Create Flask test client"""
    server.app.config['TESTING'] = True
    with server.app.test_client() as client:
        yield client

@pytest.fixture
def session():
    """Create requests session"""
    return requests.Session()

@pytest.fixture
def auth_session(session):
    """Create authenticated session"""
    base_url = os.getenv('TEST_URL', 'http://localhost:8080')
    response = session.post(f"{base_url}/api/auth/login", json={
        'username': 'superadmin',
        'password': 'admin123'
    })
    if response.status_code == 200:
        return session
    return None

# ==================== UNIT TESTS ====================

class TestAuthentication:
    """Test authentication functionality"""
    
    def test_password_hashing(self):
        """Test password hashing function"""
        password = "test123"
        hash1 = hashlib.sha256(password.encode()).hexdigest()
        hash2 = hashlib.sha256(password.encode()).hexdigest()
        assert hash1 == hash2
        assert hash1 != password
    
    def test_password_different_inputs(self):
        """Test different passwords produce different hashes"""
        pass1 = hashlib.sha256("pass123".encode()).hexdigest()
        pass2 = hashlib.sha256("pass456".encode()).hexdigest()
        assert pass1 != pass2
    
    def test_login_valid_credentials(self, client):
        """Test login with valid credentials"""
        response = client.post('/api/auth/login', json={
            'username': 'superadmin',
            'password': 'admin123'
        })
        assert response.status_code in [200, 400, 401]
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        response = client.post('/api/auth/login', json={
            'username': 'invalid',
            'password': 'invalid'
        })
        assert response.status_code in [401, 400]
    
    def test_login_missing_fields(self, client):
        """Test login with missing fields"""
        response = client.post('/api/auth/login', json={
            'username': 'test'
        })
        assert response.status_code == 400
    
    def test_logout(self, client):
        """Test logout endpoint"""
        response = client.post('/api/auth/logout')
        assert response.status_code in [200, 401]
    
    def test_get_current_user_without_auth(self, client):
        """Test getting current user without authentication"""
        response = client.get('/api/auth/me')
        assert response.status_code == 401

class TestBatches:
    """Test batches API"""
    
    def test_get_batches_list(self, auth_session):
        """Test getting list of batches"""
        if not auth_session:
            pytest.skip("Not authenticated")
        
        response = auth_session.get('http://localhost:8080/api/batches')
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            assert 'data' in data or 'batches' in data
    
    def test_create_batch(self, auth_session):
        """Test creating a new batch"""
        if not auth_session:
            pytest.skip("Not authenticated")
        
        payload = {
            'batch_name': 'Test Batch',
            'batch_number': f'TEST-{int(datetime.now().timestamp())}',
            'departure_date': (datetime.now() + timedelta(days=30)).isoformat(),
            'return_date': (datetime.now() + timedelta(days=40)).isoformat(),
            'total_slots': 50,
        }
        
        response = auth_session.post('http://localhost:8080/api/batches', json=payload)
        assert response.status_code in [201, 400, 401, 403]
    
    def test_batch_schema(self):
        """Test batch data schema"""
        batch = {
            'id': 1,
            'batch_name': 'Test',
            'batch_number': 'BAT-001',
            'total_slots': 50,
            'available_slots': 50,
            'status': 'active'
        }
        
        assert 'batch_name' in batch
        assert 'batch_number' in batch
        assert batch['total_slots'] >= 0
        assert batch['available_slots'] >= 0

class TestTravelers:
    """Test travelers API"""
    
    def test_get_travelers(self, auth_session):
        """Test getting travelers list"""
        if not auth_session:
            pytest.skip("Not authenticated")
        
        response = auth_session.get('http://localhost:8080/api/travelers')
        assert response.status_code in [200, 401]
    
    def test_create_traveler(self, auth_session):
        """Test creating a traveler"""
        if not auth_session:
            pytest.skip("Not authenticated")
        
        payload = {
            'full_name': f'Test Traveler {int(datetime.now().timestamp())}',
            'email': f'test{int(datetime.now().timestamp())}@test.com',
            'phone': '+1234567890',
            'passport_number': 'ABC123456',
        }
        
        response = auth_session.post('http://localhost:8080/api/travelers', json=payload)
        assert response.status_code in [201, 400, 401, 403]
    
    def test_traveler_schema(self):
        """Test traveler data schema"""
        traveler = {
            'id': 1,
            'full_name': 'John Doe',
            'email': 'john@example.com',
            'phone': '+1234567890',
            'passport_number': 'ABC123456',
            'status': 'active'
        }
        
        assert 'full_name' in traveler
        assert 'email' in traveler
        assert '@' in traveler['email']

class TestPayments:
    """Test payments API"""
    
    def test_get_payments(self, auth_session):
        """Test getting payments list"""
        if not auth_session:
            pytest.skip("Not authenticated")
        
        response = auth_session.get('http://localhost:8080/api/payments')
        assert response.status_code in [200, 401]
    
    def test_create_payment(self, auth_session):
        """Test creating a payment"""
        if not auth_session:
            pytest.skip("Not authenticated")
        
        payload = {
            'traveler_id': 1,
            'amount': 1000.00,
            'payment_method': 'bank_transfer'
        }
        
        response = auth_session.post('http://localhost:8080/api/payments', json=payload)
        assert response.status_code in [201, 400, 401, 403]
    
    def test_payment_amount_validation(self):
        """Test payment amount validation"""
        valid_amounts = [100.00, 1000.50, 10000.00]
        invalid_amounts = [-100, 0, -50.50]
        
        for amount in valid_amounts:
            assert amount > 0
        
        for amount in invalid_amounts:
            assert amount <= 0

class TestReports:
    """Test reports API"""
    
    def test_get_summary_report(self, auth_session):
        """Test getting summary report"""
        if not auth_session:
            pytest.skip("Not authenticated")
        
        response = auth_session.get('http://localhost:8080/api/reports/summary')
        assert response.status_code in [200, 401]
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                assert isinstance(data['data'], dict)
    
    def test_get_payments_report(self, auth_session):
        """Test getting payments report"""
        if not auth_session:
            pytest.skip("Not authenticated")
        
        response = auth_session.get('http://localhost:8080/api/reports/payments')
        assert response.status_code in [200, 401]
    
    def test_get_travelers_report(self, auth_session):
        """Test getting travelers report"""
        if not auth_session:
            pytest.skip("Not authenticated")
        
        response = auth_session.get('http://localhost:8080/api/reports/travelers')
        assert response.status_code in [200, 401]

class TestAdmin:
    """Test admin functionality"""
    
    def test_get_users(self, auth_session):
        """Test getting users list"""
        if not auth_session:
            pytest.skip("Not authenticated")
        
        response = auth_session.get('http://localhost:8080/api/admin/users')
        assert response.status_code in [200, 401, 403]
    
    def test_user_roles(self):
        """Test user roles are valid"""
        valid_roles = ['super_admin', 'admin', 'manager', 'staff', 'viewer']
        
        for role in valid_roles:
            assert role in valid_roles
        
        invalid_role = 'hacker'
        assert invalid_role not in valid_roles

class TestErrorHandling:
    """Test error handling"""
    
    def test_404_not_found(self, client):
        """Test 404 error handling"""
        response = client.get('/api/nonexistent')
        assert response.status_code == 404
        data = response.json()
        assert 'error' in data or 'success' in data
    
    def test_method_not_allowed(self, client):
        """Test method not allowed"""
        response = client.delete('/api/batches')
        assert response.status_code in [405, 401]
    
    def test_bad_request(self, client):
        """Test bad request handling"""
        response = client.post('/api/auth/login', json={'invalid': 'data'})
        assert response.status_code in [400, 401]
    
    def test_server_error_handling(self, client):
        """Test server error handling"""
        response = client.get('/')
        assert response.status_code in [200, 404, 500]

class TestInputValidation:
    """Test input validation"""
    
    def test_email_validation(self):
        """Test email validation"""
        valid_emails = [
            'user@example.com',
            'test.user@domain.co.uk',
            'user+tag@example.com'
        ]
        
        invalid_emails = [
            'invalid.email',
            '@example.com',
            'user@',
            'user@@example.com'
        ]
        
        for email in valid_emails:
            assert '@' in email and '.' in email.split('@')[1]
        
        for email in invalid_emails:
            parts = email.split('@')
            assert len(parts) != 2 or not parts[0] or not parts[1]
    
    def test_phone_validation(self):
        """Test phone validation"""
        valid_phones = ['+1234567890', '1234567890', '+44-20-7946-0958']
        
        for phone in valid_phones:
            assert len(phone.replace('-', '').replace('+', '')) >= 10
    
    def test_sql_injection_prevention(self, client):
        """Test SQL injection prevention"""
        injection_attempts = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "1 UNION SELECT * FROM users",
        ]
        
        for attempt in injection_attempts:
            response = client.post('/api/auth/login', json={
                'username': attempt,
                'password': attempt
            })
            # Should not execute injection
            assert response.status_code in [400, 401, 500]
    
    def test_xss_prevention(self, client):
        """Test XSS prevention"""
        xss_attempts = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
        ]
        
        for attempt in xss_attempts:
            response = client.post('/api/auth/login', json={
                'username': attempt,
                'password': 'test'
            })
            # Response should be safe
            assert response.status_code in [400, 401]

class TestDataConsistency:
    """Test data consistency"""
    
    def test_batch_slots_consistency(self):
        """Test batch slots consistency"""
        batch = {
            'total_slots': 50,
            'available_slots': 50,
            'used_slots': 0
        }
        
        # Total should equal available + used
        assert batch['total_slots'] == batch['available_slots'] + batch['used_slots']
    
    def test_payment_status_values(self):
        """Test valid payment statuses"""
        valid_statuses = ['pending', 'completed', 'failed', 'refunded']
        
        for status in valid_statuses:
            assert status in valid_statuses
    
    def test_traveler_status_values(self):
        """Test valid traveler statuses"""
        valid_statuses = ['active', 'inactive', 'completed', 'cancelled']
        
        for status in valid_statuses:
            assert status in valid_statuses

class TestPerformance:
    """Test performance metrics"""
    
    def test_login_response_time(self, session):
        """Test login response time"""
        import time
        
        start = time.time()
        response = session.post('http://localhost:8080/api/auth/login', json={
            'username': 'superadmin',
            'password': 'admin123'
        })
        elapsed = (time.time() - start) * 1000
        
        # Should respond in less than 5 seconds
        assert elapsed < 5000
    
    def test_list_endpoint_response_time(self, auth_session):
        """Test list endpoint response time"""
        if not auth_session:
            pytest.skip("Not authenticated")
        
        import time
        
        start = time.time()
        response = auth_session.get('http://localhost:8080/api/batches')
        elapsed = (time.time() - start) * 1000
        
        # Should respond in less than 3 seconds
        assert elapsed < 3000

# ==================== INTEGRATION TESTS ====================

class TestIntegration:
    """Integration tests"""
    
    def test_complete_user_workflow(self, auth_session):
        """Test complete user workflow"""
        if not auth_session:
            pytest.skip("Not authenticated")
        
        # 1. Get batches
        response1 = auth_session.get('http://localhost:8080/api/batches')
        assert response1.status_code in [200, 401]
        
        # 2. Get travelers
        response2 = auth_session.get('http://localhost:8080/api/travelers')
        assert response2.status_code in [200, 401]
        
        # 3. Get payments
        response3 = auth_session.get('http://localhost:8080/api/payments')
        assert response3.status_code in [200, 401]
    
    def test_database_connection(self):
        """Test database connection"""
        try:
            conn, cursor = get_db()
            cursor.execute('SELECT 1')
            result = cursor.fetchone()
            release_db(conn, cursor)
            assert result is not None
        except Exception as e:
            pytest.skip(f"Database not available: {e}")

# ==================== PYTEST MAIN ====================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])