const express = require('express');
const cors = require('cors');
const dotenv = require('dotenv');
const { vendorRoutes } = require('./routes/vendorRoutes');
const { tripRoutes } = require('./routes/tripRoutes');

dotenv.config();
const app = express();

// some middleware
app.use(cors());
app.use(express.json());

//routes
app.use('/api/vendors', vendorRoutes);
app.use('/api/trips', tripRoutes);

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`Server running at http://localhost:${PORT}`));
//db connection to test connection
// const pool = require('./db/db.js');
// pool.connect();