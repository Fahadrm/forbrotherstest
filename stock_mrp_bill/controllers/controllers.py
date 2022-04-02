# -*- coding: utf-8 -*-
# from odoo import http


# class StockMrpBill(http.Controller):
#     @http.route('/stock_mrp_bill/stock_mrp_bill/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/stock_mrp_bill/stock_mrp_bill/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('stock_mrp_bill.listing', {
#             'root': '/stock_mrp_bill/stock_mrp_bill',
#             'objects': http.request.env['stock_mrp_bill.stock_mrp_bill'].search([]),
#         })

#     @http.route('/stock_mrp_bill/stock_mrp_bill/objects/<model("stock_mrp_bill.stock_mrp_bill"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('stock_mrp_bill.object', {
#             'object': obj
#         })
