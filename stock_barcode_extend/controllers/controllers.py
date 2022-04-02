# -*- coding: utf-8 -*-
# from odoo import http


# class StockBarcodeExtend(http.Controller):
#     @http.route('/stock_barcode_extend/stock_barcode_extend/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/stock_barcode_extend/stock_barcode_extend/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('stock_barcode_extend.listing', {
#             'root': '/stock_barcode_extend/stock_barcode_extend',
#             'objects': http.request.env['stock_barcode_extend.stock_barcode_extend'].search([]),
#         })

#     @http.route('/stock_barcode_extend/stock_barcode_extend/objects/<model("stock_barcode_extend.stock_barcode_extend"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('stock_barcode_extend.object', {
#             'object': obj
#         })
