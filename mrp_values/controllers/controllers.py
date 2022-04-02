# -*- coding: utf-8 -*-
# from odoo import http


# class MrpValues(http.Controller):
#     @http.route('/mrp_values/mrp_values/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mrp_values/mrp_values/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('mrp_values.listing', {
#             'root': '/mrp_values/mrp_values',
#             'objects': http.request.env['mrp_values.mrp_values'].search([]),
#         })

#     @http.route('/mrp_values/mrp_values/objects/<model("mrp_values.mrp_values"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mrp_values.object', {
#             'object': obj
#         })
