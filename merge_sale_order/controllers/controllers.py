# -*- coding: utf-8 -*-
# from odoo import http


# class MergeSaleOrder(http.Controller):
#     @http.route('/merge_sale_order/merge_sale_order/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/merge_sale_order/merge_sale_order/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('merge_sale_order.listing', {
#             'root': '/merge_sale_order/merge_sale_order',
#             'objects': http.request.env['merge_sale_order.merge_sale_order'].search([]),
#         })

#     @http.route('/merge_sale_order/merge_sale_order/objects/<model("merge_sale_order.merge_sale_order"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('merge_sale_order.object', {
#             'object': obj
#         })
