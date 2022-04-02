odoo.define('customer_mobile_scan.mobile_barcode', function (require) {
"use strict";

//var linesWidget = require('stock_barcode.LinesWidget');
var BarcodeMainMenu = require('customer_mobile_scan.customer_main_menu').CustomerMainMenu;

var core = require('web.core');

const mobile = require('web_mobile.core');

var _t = core._t;

/**
 * Opens camera for mobile device to scan barcode.
 *
 * @param {Function} callback function that called after barcode scanned sucessfully
 *
 */
function openMobileScanner (callback) {
    mobile.methods.scanBarcode().then(function (response) {
        var barcode = response.data;
        if (barcode){
            callback(barcode);
            mobile.methods.vibrate({'duration': 100});
        } else {
            mobile.methods.showToast({'message':_t('Please, Scan again !!')});
        }
    });
}
BarcodeMainMenu.include({
    events: _.defaults({
        'click .o_customer_mobile_barcode': 'open_mobile_scanner'
    }, BarcodeMainMenu.prototype.events),
    init: function () {
        this.mobileMethods = mobile.methods;
        return this._super.apply(this, arguments);
    },
    open_mobile_scanner: function() {
        var self = this;
        openMobileScanner(function (barcode) {
            self._onBarcodeScanned(barcode);
        });
    }
});

});
