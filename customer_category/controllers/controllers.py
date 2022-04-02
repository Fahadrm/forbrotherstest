# -*- coding: utf-8 -*-
# from odoo import http


# class CustomerCategory(http.Controller):
#     @http.route('/customer_category/customer_category/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/customer_category/customer_category/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('customer_category.listing', {
#             'root': '/customer_category/customer_category',
#             'objects': http.request.env['customer_category.customer_category'].search([]),
#         })

#     @http.route('/customer_category/customer_category/objects/<model("customer_category.customer_category"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('customer_category.object', {
#             'object': obj
#         })
