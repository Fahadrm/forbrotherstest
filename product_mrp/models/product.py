# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.osv import expression
from odoo.exceptions import UserError


class ProductProduct(models.Model):
    _inherit = 'product.product'

    # def check_unique_stock_mrp(self):
    #     result=[]
    #     mrp_duplicate = []
    #     mrp_float = []
    #     for product in self:
    #         mrp_values = self.env['stock.mrp.product.report'].search([('product_id','=',product.id)])
    #         mr = [rec.id for rec in mrp_values if rec.name != 0 and rec.name not in mrp_duplicate]
    #         serial_no = 1
    #         for rec in mrp_values:
    #             if rec.name != 0 and rec.name not in mrp_float:
    #                 # rec.sl_no = serial_no
    #                 serial_no += 1
    #                 mrp_float.append(rec.name)
    #                 mrp_duplicate.append(rec.id)
    #         result = [('id', 'in', mrp_duplicate)]
    #     mrp_list = mrp_duplicate
    #     if mrp_list != []:
    #         mrp_list = mrp_duplicate
    #         return [('id', 'in', mrp_duplicate)]
    #     else:
    #         return

    product_mrp_ids = fields.One2many(
            'stock.mrp.product.report',
            'product_id',
            string='Product MRP',store=True

        )


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_mrp_ids = fields.One2many( 'stock.mrp.product.report',related='product_variant_ids.product_mrp_ids',readonly=False)


    @api.model_create_multi
    def create(self, vals_list):
        res = super(ProductTemplate, self).create(vals_list)
        for vals in vals_list:
            if 'product_mrp_ids' in vals:
                for val in vals['product_mrp_ids']:
                    res.update({'product_mrp_ids': [(0, 0, {'name': val[2]['name']})]})
        return res
