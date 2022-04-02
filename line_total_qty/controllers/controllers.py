# -*- coding: utf-8 -*-
# from odoo import http


# class LineTotalQty(http.Controller):
#     @http.route('/line_total_qty/line_total_qty/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/line_total_qty/line_total_qty/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('line_total_qty.listing', {
#             'root': '/line_total_qty/line_total_qty',
#             'objects': http.request.env['line_total_qty.line_total_qty'].search([]),
#         })

#     @http.route('/line_total_qty/line_total_qty/objects/<model("line_total_qty.line_total_qty"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('line_total_qty.object', {
#             'object': obj
#         })
