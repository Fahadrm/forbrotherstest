odoo.define('stock_barcode_extend.models', function (require) {
    var models = require('point_of_sale.models');

    models.load_fields('stock.move.line', ['product_mrp','customer_locations','expiration_date']);
     models.load_fields('stock.move', ['product_mrp','customer_locations']);
});
