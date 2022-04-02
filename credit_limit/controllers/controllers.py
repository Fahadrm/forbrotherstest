# -*- coding: utf-8 -*-
# from odoo import http


# class CreditLimit(http.Controller):
#     @http.route('/credit_limit/credit_limit/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/credit_limit/credit_limit/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('credit_limit.listing', {
#             'root': '/credit_limit/credit_limit',
#             'objects': http.request.env['credit_limit.credit_limit'].search([]),
#         })

#     @http.route('/credit_limit/credit_limit/objects/<model("credit_limit.credit_limit"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('credit_limit.object', {
#             'object': obj
#         })
