const pool = require('../db/db.js');

// GET all trips (limit for performance)
exports.getAllTrips = async (req, res) => {
  try {
    const limit = req.query.limit || 100;
    const result = await pool.query('SELECT * FROM trip_facts LIMIT $1', [limit]);
    res.status(200).json(result.rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
};

// GET trip by ID
exports.getTripById = async (req, res) => {
  try {
    const { id } = req.params;
    const result = await pool.query('SELECT * FROM trip_facts WHERE trip_id = $1', [id]);
    if (result.rows.length === 0) return res.status(404).json({ message: 'Trip not found' });
    res.status(200).json(result.rows[0]);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
};

// Analytics endpoint example
exports.getHourlyStats = async (req, res) => {
  try {
    const result = await pool.query('SELECT * FROM hourly_trip_stats ORDER BY pickup_hour');
    res.status(200).json(result.rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
};
