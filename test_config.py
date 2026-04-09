import os

# Get DATABASE_URL from Railway (you can also set it manually)
DATABASE_URL = "postgresql://postgres:cbZOkSkTGHUBzcIKZQOLmcClIVhHqNAI@postgres.railway.internal:5432/railway"

# Set environment variable for tests
os.environ['DATABASE_URL'] = DATABASE_URL
os.environ['TESTING'] = 'True'