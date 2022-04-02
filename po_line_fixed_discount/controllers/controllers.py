# -*- coding: utf-8 -*-
# from odoo import http


# class PoLineFixedDiscount(http.Controller):
#     @http.route('/po_line_fixed_discount/po_line_fixed_discount/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/po_line_fixed_discount/po_line_fixed_discount/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('po_line_fixed_discount.listing', {
#             'root': '/po_line_fixed_discount/po_line_fixed_discount',
#             'objects': http.request.env['po_line_fixed_discount.po_line_fixed_discount'].search([]),
#         })

#     @http.route('/po_line_fixed_discount/po_line_fixed_discount/objects/<model("po_line_fixed_discount.po_line_fixed_discount"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('po_line_fixed_discount.object', {
#             'object': obj
#         })
