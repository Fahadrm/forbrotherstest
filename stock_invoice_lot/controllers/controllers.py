# -*- coding: utf-8 -*-
# from odoo import http


# class StockInvoiceLot(http.Controller):
#     @http.route('/stock_invoice_lot/stock_invoice_lot/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/stock_invoice_lot/stock_invoice_lot/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('stock_invoice_lot.listing', {
#             'root': '/stock_invoice_lot/stock_invoice_lot',
#             'objects': http.request.env['stock_invoice_lot.stock_invoice_lot'].search([]),
#         })

#     @http.route('/stock_invoice_lot/stock_invoice_lot/objects/<model("stock_invoice_lot.stock_invoice_lot"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('stock_invoice_lot.object', {
#             'object': obj
#         })
