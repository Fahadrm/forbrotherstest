# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class stock_invoice_lot(models.Model):
#     _name = 'stock_invoice_lot.stock_invoice_lot'
#     _description = 'stock_invoice_lot.stock_invoice_lot'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
