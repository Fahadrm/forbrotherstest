# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockPicking(models.Model):
    _name = 'stock.picking'
    _inherit = ['stock.picking', 'barcodes.barcode_events_mixin']

    sum_done_qty = fields.Float(compute='calculate_done_qty', string='Total Done Quantity')
    len_qty = fields.Float(compute='calculate_uom_qty', string='Total Lines')

    sum_uom_qty = fields.Float(compute='calculate_uom_qty', string='Total Demand Quantity')
    city = fields.Char(string='CITY', related='partner_id.city',store=True)


    def calculate_done_qty(self):
        for rs in self:
            sumqty = 0
            # for line in rs.move_lines:
            for line in rs.move_ids_without_package:
                sumqty += line.quantity_done
            rs.sum_done_qty = sumqty

    def calculate_uom_qty(self):

        for rs in self:
            uomqty = 0
            len=0
            for line in rs.move_ids_without_package:
            # for line in rs.move_lines:
                len+=1
                uomqty += line.product_uom_qty
            rs.sum_uom_qty = uomqty
            rs.len_qty = len

    # @api.model
    # def _get_picking_fields_to_read(self):
    #     res = super(StockPicking, self)._get_picking_fields_to_read()
    #     res.append('basket_ids')
    #     return res

