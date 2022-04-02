# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ProductMRPReport(models.Model):
    _inherit = "stock.mrp.product.report"


    @api.onchange('mrp','sl_no')
    def _onchange(self):
        for i in self:
            if i.mrp:
                i.name = i.mrp
            if i.sl_no:
                i.name = i.mrp



class ProductMasterInherit(models.Model):
    _inherit = ['product.template']


    all_mrp = fields.Text("On hand: ",compute='compute_war_qty')


    def compute_war_qty(self):
        for war in self:
            string = ''
            product_id = self.env['product.product'].search([('product_tmpl_id', '=', war.id)])
            if product_id:
                product_stock_location = self.env['stock.mrp.product.report'].search([('product_id', '=', product_id[0].id)])
                warehouse_names = []
                if product_stock_location:
                    for n in product_stock_location:
                        vals = {
                        "mrp" : n.mrp if n.mrp else 0.00,
                        "mrp_name" : n.name if n.name else 0.00,
                        }
                        warehouse_names.append(vals)
                        if warehouse_names:
                            warehouse_names = sorted(warehouse_names, key=lambda k: k['mrp_name'])
                    if len(warehouse_names)>1:
                        temp_string = warehouse_names[0]['mrp_name'] if warehouse_names[0]['mrp_name'] else 0
                        temp_string = str(temp_string)
                        string = string + '\n' + temp_string + ' ' + 'More'
                    elif len(warehouse_names)==1:
                        temp_string = warehouse_names[0]['mrp_name'] if warehouse_names[0]['mrp_name'] else 0
                        temp_string = str(temp_string)
                        string = string + '\n' + temp_string
                    else:
                        temp_string = " "
                        string = string + '\n' + temp_string
            war.all_mrp = string



class SaleOrder(models.Model):
    _inherit = 'sale.order'

    beat_id =fields.Many2one('village.master',string="Beat")


    @api.onchange('beat_id')
    def _onchange_beat(self):
        partner_list = []
        for i in self:
            if i.beat_id:
                beats = self.env['res.partner'].search([('village_id','=',i.beat_id.id)])
                for partner in beats:
                    partner_list.append(partner.id)
                result = {'domain': {'partner_id': [('id', 'in', partner_list)]}}
            else:
                beats = self.env['res.partner'].search([])
                for partner in beats:
                    partner_list.append(partner.id)
                result = {'domain': {'partner_id': [('id', 'in', partner_list)]}}
        return result

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    def _get_inventory_move_values(self, qty, location_id, location_dest_id, out=False):
        res = super(StockQuant, self)._get_inventory_move_values(qty, location_id, location_dest_id, out=False)
        move_line_ids= res[ 'move_line_ids']
        for mv_line in move_line_ids:
            mv_line[2]['product_mrp'] = self.product_mrp.id
            mv_line[2]['customer_locations'] = self.customer_locations.id
        return res

    @api.model
    def _get_inventory_fields_create(self):
        res = super(StockQuant, self)._get_inventory_fields_create()
        res.append('product_mrp')
        res.append('customer_locations')
        return res
