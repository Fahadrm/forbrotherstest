odoo.define('user_hide_smart_button.website', function (require) {
"use strict";

var field_registry = require('web.field_registry');
var session = require('web.session');
//var websitepreviewbutton = require('website.backend.button');
var AbstractField = require('web.AbstractField');
var core = require('web.core');

var _t = core._t;


var AbstractField = AbstractField.include({

        init: function (parent, name, record, options) {

            var user = session.uid;
            session.user_has_group('website.group_website_designer').then(function(has_group){
            if(!has_group){
            $('.btn.oe_stat_button.o_field_widget').css('visibility', 'hidden')

            }

            })
        this._super(parent, name, record, options);
    },


    });

    return AbstractField;
});


//
//AbstractField.include({
//    start: function () {
//        var self = this;
//        session.user_has_group('website.group_website_designer').then(function(has_group){
//
////            var user = session.uid;
//            if(!has_group){
//            $('.btn.oe_stat_button.o_field_widget').css('visibility', 'hidden')
//            }
//
//            })
//        this._super.apply(this, arguments);
//    },
//});
//
//});
//
