# -*- coding: utf-8 -*-
# from odoo import http


# class StockFlowReport(http.Controller):
#     @http.route('/stock_flow_report/stock_flow_report/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/stock_flow_report/stock_flow_report/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('stock_flow_report.listing', {
#             'root': '/stock_flow_report/stock_flow_report',
#             'objects': http.request.env['stock_flow_report.stock_flow_report'].search([]),
#         })

#     @http.route('/stock_flow_report/stock_flow_report/objects/<model("stock_flow_report.stock_flow_report"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('stock_flow_report.object', {
#             'object': obj
#         })
