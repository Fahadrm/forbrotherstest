# -*- coding: utf-8 -*-
# from odoo import http


# class DuplicateProductWarning(http.Controller):
#     @http.route('/duplicate_product_warning/duplicate_product_warning/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/duplicate_product_warning/duplicate_product_warning/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('duplicate_product_warning.listing', {
#             'root': '/duplicate_product_warning/duplicate_product_warning',
#             'objects': http.request.env['duplicate_product_warning.duplicate_product_warning'].search([]),
#         })

#     @http.route('/duplicate_product_warning/duplicate_product_warning/objects/<model("duplicate_product_warning.duplicate_product_warning"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('duplicate_product_warning.object', {
#             'object': obj
#         })
