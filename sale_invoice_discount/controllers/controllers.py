# -*- coding: utf-8 -*-
# from odoo import http


# class SaleInvoiceDiscount(http.Controller):
#     @http.route('/sale_invoice_discount/sale_invoice_discount/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sale_invoice_discount/sale_invoice_discount/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('sale_invoice_discount.listing', {
#             'root': '/sale_invoice_discount/sale_invoice_discount',
#             'objects': http.request.env['sale_invoice_discount.sale_invoice_discount'].search([]),
#         })

#     @http.route('/sale_invoice_discount/sale_invoice_discount/objects/<model("sale_invoice_discount.sale_invoice_discount"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sale_invoice_discount.object', {
#             'object': obj
#         })
