# -*- coding: utf-8 -*-
# from odoo import http


# class CustomerLocationCode(http.Controller):
#     @http.route('/customer_location_code/customer_location_code/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/customer_location_code/customer_location_code/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('customer_location_code.listing', {
#             'root': '/customer_location_code/customer_location_code',
#             'objects': http.request.env['customer_location_code.customer_location_code'].search([]),
#         })

#     @http.route('/customer_location_code/customer_location_code/objects/<model("customer_location_code.customer_location_code"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('customer_location_code.object', {
#             'object': obj
#         })
