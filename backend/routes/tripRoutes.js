const express = require('express');
const { getAllTrips, getTripById, getHourlyStats } = require('../controllers/tripController.js');

const router = express.Router();

router.get('/trips', getAllTrips);
router.get('/trips/:id', getTripById);
router.get('/trips/analytics/hourly', getHourlyStats);

module.exports.tripRoutes = router;
