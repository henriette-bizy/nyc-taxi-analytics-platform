const express = require('express');
const cors = require('cors');
const dotenv = require('dotenv');
const { vendorRoutes } = require('./routes/vendorRoutes');
const { tripRoutes } = require('./routes/tripRoutes');
const swaggerUi = require("swagger-ui-express");
const swaggerFile = require('../swaggerDocs.json');

dotenv.config({ path: '../.env' });
const app = express();

// some middleware
app.use(cors());
app.use(express.json());
//set swagger documentation
app.use("/api/documentation", swaggerUi.serve, swaggerUi.setup(swaggerFile, false, {
    docExpansion: "none"
}));
//routes
app.use('/api', vendorRoutes);
app.use('/api', tripRoutes);

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`Server running at http://localhost:${PORT}`));
//db connection to test connection
// const pool = require('./db/db.js');
// pool.connect();