const express=require('express');
const { getAllVendors, getVendorById, createVendor } =require ('../controllers/vendorController.js');

const router = express.Router();

router.get('/', getAllVendors);
router.get('/:id', getVendorById);
router.post('/', createVendor);

module.exports.vendorRoutes=router;