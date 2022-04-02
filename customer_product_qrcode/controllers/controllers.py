# -*- coding: utf-8 -*-
# from odoo import http


# class CustomerProductQrcode(http.Controller):
#     @http.route('/customer_product_qrcode/customer_product_qrcode/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/customer_product_qrcode/customer_product_qrcode/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('customer_product_qrcode.listing', {
#             'root': '/customer_product_qrcode/customer_product_qrcode',
#             'objects': http.request.env['customer_product_qrcode.customer_product_qrcode'].search([]),
#         })

#     @http.route('/customer_product_qrcode/customer_product_qrcode/objects/<model("customer_product_qrcode.customer_product_qrcode"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('customer_product_qrcode.object', {
#             'object': obj
#         })
