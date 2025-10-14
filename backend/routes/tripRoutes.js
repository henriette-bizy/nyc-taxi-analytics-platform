const express = require('express');
const { getAllTrips, getTripById, getHourlyStats } = require('../controllers/tripController.js');

const router = express.Router();

router.get('/', getAllTrips);
router.get('/:id', getTripById);
router.get('/analytics/hourly', getHourlyStats);

module.exports.tripRoutes = router;
