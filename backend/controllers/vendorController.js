const pool =require('../db/db.js');

// Get all vendors
exports.getAllVendors = async (req, res) => {
  try {
    const result = await pool.query('SELECT * FROM vendors ORDER BY vendor_id');
    res.status(200).json(result.rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
};

// Get vendor by ID
exports.getVendorById = async (req, res) => {
  try {
    const { id } = req.params;
    const result = await pool.query('SELECT * FROM vendors WHERE vendor_id = $1', [id]);
    if (result.rows.length === 0) return res.status(404).json({ message: 'Vendor not found' });
    res.status(200).json(result.rows[0]);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
};

// Create new vendor
exports.createVendor = async (req, res) => {
  try {
    const { vendor_name, description } = req.body;
    //get last id
    const lastIdResult = await pool.query('SELECT MAX(vendor_id) AS max_id FROM vendors');
    const lastId = lastIdResult.rows[0].max_id || 0;
    const vendorId = lastId + 1;

    if (!vendor_name || !description) {
      return res.status(400).json({ message: 'vendor_name and description are required' });
    }
    const result = await pool.query(
      'INSERT INTO vendors (vendor_id, vendor_name, description) VALUES ($1, $2, $3) RETURNING *',
      [vendorId,vendor_name, description]
    );
    res.status(201).json(result.rows[0]);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
};