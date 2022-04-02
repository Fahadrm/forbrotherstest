odoo.define('mobile_basket_verification.BasketVerification', function (require){
'use strict';

var core = require('web.core');
var Widget = require('web.Widget');
var AbstractAction = require('web.AbstractAction');
var Dialog = require('web.Dialog');
const mobile = require('web_mobile.core');

var Qweb = core.qweb;
var _t = core._t;

var BasketWidget = AbstractAction.extend({
  contentTemplate:'BasketVerificationComponent',
  events:{
    // 'change .basket_barcode_input':'_onClickBasketInputChange',
    'input .basket_barcode_input':'_onClickBasketInputChange',
    'click .basket_verify':'_onClickBasketVerify',
    'click .barcode_verification_icon': 'open_mobile_scanner_basket_verify',
    'click .barcode_verification_icon_text': 'open_mobile_scanner_basket_verify',

  },
  init: function(parent,action){
    this._super.apply(this, arguments);
    this.basketVerificationId = action.context.active_id;
    this.barcode = null;
  },

  open_mobile_scanner_basket_verify:function(){
    // console.log('am here');
    var self = this;
    mobile.methods.vibrate({'duration':100});

    self.openMobileScannerBasketVerification(function (barcode) {
        self._onBasketBarcodeScannedVerification(barcode);
    });

  },

  openMobileScannerBasketVerification(callback){
    mobile.methods.scanBarcode().then(function (response){
      var barcode = response.data;
      if (barcode){
        callback(barcode);
        mobile.methods.vibrate({'duration':100});
      } else {

        mobile.methods.showToast({'message':_t('Please, Scan again !!')});
      }
    });
  },

  _onBasketBarcodeScannedVerification: function (barcode){
    var self = this;
    core.bus.off('barcode_scanned', this, this._onBarcodeScanned);
    this.barcode = barcode;

    if (barcode !=''){

      return this._rpc({
        model: 'mobile.basket.verification',
        method: 'get_picking_details',
        args: [this.basketVerificationId,barcode],
      }).then(function(res){
        self.$el.find('.o_barcode_lines').html('');

        self.picking_id = res['picking_id']
        // if (res['picking_id'] != false){
        var message = res['result'];

        if (res['status'] == true){

          self.picking = res['picking_id']
          self.customer = res['partner_id']
          self.line = res['line_ids']
          var $body = self.$el.find('.o_barcode_lines');
          if (res['status'] == true){
            var $lines = $(Qweb.render('basketVerificationLines', {
              picking:res['picking_id'],
              customer:res['partner_id'],
              sale_order:res['sale_id'],
              street:res['street'],
              street1:res['street1'],
              city:res['city'],
              zip:res['zip'],
              lines:res['line_ids']
            }));
            $body.prepend($lines);
          }
        }else{
          self.$el.find('.o_barcode_lines').html('');
          var message = res['result'];

          // mobile.methods.showToast({'message':_t('basket not found.')});
          mobile.methods.showToast({'message':_t(message)});

        }
      });
    }else{
      self.$el.find('.o_barcode_lines').html('');
      mobile.methods.showToast({'message':_t('No basket found!!')});

    }
  },
  _onClickBasketInputChange: function(){
    var self = this;
    var barcode = $('.basket_barcode_input').val();
    if (barcode !=''){
      return this._rpc({
        model: 'mobile.basket.verification',
        method: 'get_picking_details',
        args: [this.basketVerificationId,barcode],
      }).then(function(res){
  
        self.picking_id = res['picking_id']
        if (res['status'] != false){
          self.picking = res['picking_id']
          self.customer = res['partner_id']
          self.line = res['line_ids']
          var $body = self.$el.find('.o_barcode_lines');
          if (res['status'] == true){
            var $lines = $(Qweb.render('basketVerificationLines', {
              picking:res['picking_id'],
              customer:res['partner_id'],
              sale_order:res['sale_id'],
              street:res['street'],
              street1:res['street1'],
              city:res['city'],
              zip:res['zip'],
              lines:res['line_ids']
            }));
            $body.prepend($lines);
          }
          var message = res['result'];
          if (res['status'] == false){
            Dialog.alert(self, message);
          }
        }else{
          self.$el.find('.o_barcode_lines').html('');
        }
      });
    }else{
      self.$el.find('.o_barcode_lines').html('');

    }
  },
  _onClickBasketVerify: function(){
    var self = this;
    var barcode = null;
    if (this.barcode != undefined){
      barcode = this.barcode;
    }else{
      barcode = $('.basket_barcode_input').val();

    }


    if ($('input#product_check_verify').not(':checked').length > 0){

      Dialog.alert(self,'All products should be verified before a basket unallocation.');
    }else{


    var rec = this._rpc({
      model: 'mobile.basket.verification',
      method: 'basket_verify',
      args: [this.basketVerificationId,barcode],
    });
    rec.then(function(result){
      $('.basket_barcode_input').val('');
      var message = result['result'];
      var status = result['status'];
      Dialog.alert(self,message);
      self.$el.find('.o_barcode_lines').html('');

    });
    }
  },
  start: function() {
    this.$('.o_content').addClass('o_barcode_client_action'); // reuse stylings
      this._super.apply(this, arguments);
    },
});
core.action_registry.add('basket_verification_client_action',BasketWidget);
return BasketWidget;

});
