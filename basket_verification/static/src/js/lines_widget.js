odoo.define('basket_verification.add_basket',function (require){
  'use strict';
  var core = require('web.core');
  var Widget = require('web.Widget');
  var Dialog = require('web.Dialog');
  var QWeb = core.qweb;
  var LinesWidget = require('stock_barcode.LinesWidget');
  const mobile = require('web_mobile.core');
  var _t = core._t;



  // _onClickAddUnit: function (ev) {

  // console.log('LinesWidget',LinesWidget);
  LinesWidget.include({

    events:_.extend({}, LinesWidget.prototype.events,{
      'click .add_basket':'_AllocateBasket',
      // 'click .o_scan_basket': 'open_mobile_scanner_basket',
      'click .barcode_allocation': 'open_mobile_scanner_basket',
    }),
    init: function (parent, page, pageIndex, nbPages) {
        this._super.apply(this, arguments);
        console.log('parent.actionParams',parent.actionParams);
        // this.basket_ids = parent.basket_ids;
        this.action_params = parent.actionParams;
        this.o_line_id = null;
      },
    open_mobile_scanner_basket:function(ev){
      var self = this;
      // var line_id = self.$el.find('.o_barcode_line').data('id');
      ev.preventDefault();
      const $line = $(ev.target).parents('.o_barcode_line');
      const line_id = $line.data('id');
      this.o_line_id = line_id;
      // console.log('am here',line_id);
      var self = this;

      self.openMobileScannerBasket(function (barcode) {
          self._onBasketBarcodeScanned(barcode);
      });

    },
    _onBasketBarcodeScanned: function (barcode){
      // console.log('am here');
      var self = this;
      core.bus.off('barcode_scanned', this, this._onBarcodeScanned);
      this._rpc({
        model: 'stock.picking',
        method: 'set_basket',
        // args: [this.action_params.id,this.action_params.id,barcode,]
        args: [this.o_line_id,this.o_line_id,barcode,]
      }).then(function (res){
        // console.log('rec',res);
      // $('.basket_barcode_input').val('');
      var message = res['result'];
      if (res['status'] == true){
        mobile.methods.showToast({'message':_t(message)});

        // Dialog.alert(self, message);
      }
      else{
        // var msg = _t(message);
        // return Promise.reject(msg);
        mobile.methods.showToast({'message':_t(message)});
        // Dialog.alert(self, message);
      }
      });
    },
    openMobileScannerBasket(callback){
      mobile.methods.scanBarcode().then(function (response){
        var barcode = response.data;
        // this.basket_barcode = barcode;
        $('.basket_barcode_input').val(barcode);

        if (barcode){
          mobile.methods.vibrate({'duration':100});
          callback(barcode);
        } else {

          mobile.methods.showToast({'message':_t('Please, Scan again !!')});
        }
      });
    },

    _AllocateBasket:function(){
      var self = this;
      var barcode = $('.basket_barcode_input').val();
      var rec = this._rpc({
      // return this._rpc({
        model: 'stock.picking',
        method: 'set_basket_status',
        args: [this.action_params.id,barcode],
        // args: [this.action_params.id,{
        //   'picking_id': this.action_params.id,
        //   'basket':'B2',
        // }],
      });
      rec.then(function(res){
        // console.log('rec',res);
      $('.basket_barcode_input').val('');
      var message = res['result'];
      if (res['status'] == true){
        Dialog.alert(self, message);
      }
      else{
        Dialog.alert(self, message);
      }
    });
    },
  });
});
