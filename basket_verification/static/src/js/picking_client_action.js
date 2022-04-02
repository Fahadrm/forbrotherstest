odoo.define('stock_barcode.picking_client_action', function (require) {
'use strict';
var core = require('web.core');
var ClientAction = require('stock_barcode.ClientAction');
var ViewsWidget = require('stock_barcode.ViewsWidget');
var PickingClientAction = require('stock_barcode.picking_client_action');

var _t = core._t;
PickingClientAction.include({

  willStart:function(){
      var self = this;
      console.log('currentstate',self.currentState);
      return this._super.apply(this, arguments).then(function () {
        // self.picking_id =
      });
  },

});
