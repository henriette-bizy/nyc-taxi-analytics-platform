const express=require('express');
const { getAllVendors, getVendorById, createVendor } =require ('../controllers/vendorController.js');

const router = express.Router();

router.get('/vendors', getAllVendors);
router.get('/vendors/:id', getVendorById);
router.post('/vendors', createVendor);

module.exports.vendorRoutes=router;