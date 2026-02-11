const express = require('express');
const router = express.Router();
const path = require('path');
const fs = require('fs');

// Ensure uploads directory exists
const uploadsDir = path.join(__dirname, '../../uploads');
if (!fs.existsSync(uploadsDir)) {
  fs.mkdirSync(uploadsDir, { recursive: true });
}

// Upload document
router.post('/', async (req, res) => {
  try {
    if (!req.files || Object.keys(req.files).length === 0) {
      return res.status(400).json({ success: false, error: 'No files uploaded' });
    }

    const file = req.files.file;
    const fileType = req.body.type || 'document';
    const travelerId = req.body.travelerId;
    
    // Create unique filename
    const fileExt = path.extname(file.name);
    const fileName = `${fileType}_${Date.now()}${fileExt}`;
    const filePath = path.join(uploadsDir, fileName);

    // Move file to uploads directory
    await file.mv(filePath);

    res.json({
      success: true,
      message: 'File uploaded successfully',
      file: {
        name: fileName,
        path: `/uploads/${fileName}`,
        type: fileType,
        size: file.size,
        mimetype: file.mimetype
      }
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Get uploaded file
router.get('/:filename', (req, res) => {
  try {
    const { filename } = req.params;
    const filePath = path.join(uploadsDir, filename);
    
    if (!fs.existsSync(filePath)) {
      return res.status(404).json({ success: false, error: 'File not found' });
    }

    res.sendFile(filePath);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

module.exports = router;