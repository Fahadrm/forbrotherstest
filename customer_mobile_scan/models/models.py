# -*- coding: utf-8 -*-
from odoo import models, fields, api

#
# class ResPartner(models.Model):
#     _inherit = 'res.partner'
#
#     @api.model
#     def get_all_customer_by_barcode(self):
#         locations = self.env['res.partner'].search_read(
#             [('barcode', '!=', None)], ['display_name', 'barcode', 'parent_path'])
#         locationsByBarcode = {location.pop('barcode'): location for location in locations}
#         return locationsByBarcode