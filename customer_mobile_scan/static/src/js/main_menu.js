odoo.define('customer_mobile_scan.customer_main_menu', function (require) {
"use strict";

var AbstractAction = require('web.AbstractAction');
var core = require('web.core');
var Dialog = require('web.Dialog');
var Session = require('web.session');

var _t = core._t;

var CustomerMainMenu = AbstractAction.extend({
    contentTemplate: 'customer_main_menu',

    events: {

        "click .o_customer_barcode_menu": function(){
            this.trigger_up('toggle_fullscreen');
            this.trigger_up('show_home_menu');
        },
    },

    init: function(parent, action) {
        this._super.apply(this, arguments);
    },


    start: function() {
        var self = this;
        core.bus.on('barcode_scanned', this, this._onBarcodeScanned);
        return this._super().then(function() {

        });
    },

    destroy: function () {
        core.bus.off('barcode_scanned', this, this._onBarcodeScanned);
        this._super();
    },

    _onBarcodeScanned: function(barcode) {
        var self = this;
        if (!$.contains(document, this.el)) {
            return;
        }
        Session.rpc('/customer_mobile_scan/scan_from_main_menu', {
            barcode: barcode,
        }).then(function(result) {
            if (result.action) {
                self.do_action(result.action);
            } else if (result.warning) {
                self.do_warn(result.warning);
            }
        });
    },
});

core.action_registry.add('seq_customer_main_menu', CustomerMainMenu);

return {
    CustomerMainMenu: CustomerMainMenu,
};

});
