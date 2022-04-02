# -*- coding: utf-8 -*-
# from odoo import http


# class BasketVerification(http.Controller):
#     @http.route('/basket_verification/basket_verification/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/basket_verification/basket_verification/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('basket_verification.listing', {
#             'root': '/basket_verification/basket_verification',
#             'objects': http.request.env['basket_verification.basket_verification'].search([]),
#         })

#     @http.route('/basket_verification/basket_verification/objects/<model("basket_verification.basket_verification"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('basket_verification.object', {
#             'object': obj
#         })
