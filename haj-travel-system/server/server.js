const express = require('express');
const cors = require('cors');
const fileUpload = require('express-fileupload');
const path = require('path');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(fileUpload({
  useTempFiles: true,
  tempFileDir: '/tmp/',
  limits: { fileSize: 10 * 1024 * 1024 }
}));

// Serve static files from public folder
app.use(express.static(path.join(__dirname, '../public')));

// Database connection
const { pool, initializeDatabase } = require('./database');

// Import routes
const travelerRoutes = require('./routes/travelers');
const uploadRoutes = require('./routes/uploads');

// Use routes
app.use('/api/travelers', travelerRoutes);
app.use('/api/upload', uploadRoutes);

// Admin route
app.get('/admin', (req, res) => {
  res.sendFile(path.join(__dirname, '../public/admin.html'));
});

// API Home
app.get('/api', (req, res) => {
  res.json({
    name: "Alhudha Haj Travel System",
    version: "2.0",
    fields: 33,
    status: "active",
    endpoints: {
      travelers: "/api/travelers",
      upload: "/api/upload",
      admin: "/admin",
      stats: "/api/travelers/stats/summary",
      batches: "/api/travelers/batches/list"
    }
  });
});

// Initialize database on startup
initializeDatabase().then(() => {
  console.log('✅ Database initialized successfully with 33 fields');
}).catch(err => {
  console.error('❌ Database initialization failed:', err);
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 Server running on port ${PORT}`);
  console.log(`📁 33 Fields System Ready`);
  console.log(`🌐 http://localhost:${PORT}`);
});