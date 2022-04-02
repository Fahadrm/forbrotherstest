# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models,_
from psycopg2 import sql
from odoo.exceptions import AccessDenied, ValidationError
from odoo.tools import float_compare, float_is_zero
from odoo.osv import expression
from odoo.tools.misc import OrderedSet



class InventoryLine(models.Model):
    _inherit = 'stock.inventory'

    duplicate_product = fields.Boolean(string="Duplicate Product")


    def _get_quantities(self):
        """Return quantities group by product_id, location_id, lot_id, package_id and owner_id,product_mrp

        :return: a dict with keys as tuple of group by and quantity as value
        :rtype: dict
        """
        self.ensure_one()
        if self.location_ids:
            domain_loc = [('id', 'child_of', self.location_ids.ids)]
        else:
            domain_loc = [('company_id', '=', self.company_id.id), ('usage', 'in', ['internal', 'transit'])]
        locations_ids = [l['id'] for l in self.env['stock.location'].search_read(domain_loc, ['id'])]

        domain = [('company_id', '=', self.company_id.id),
                  ('quantity', '!=', '0'),
                  ('location_id', 'in', locations_ids)]
        if self.prefill_counted_quantity == 'zero':
            domain.append(('product_id.active', '=', True))

        if self.product_ids:
            domain = expression.AND([domain, [('product_id', 'in', self.product_ids.ids)]])

        fields = ['product_id', 'location_id', 'lot_id', 'package_id', 'owner_id','product_mrp','customer_locations', 'quantity:sum',]
        group_by = ['product_id', 'location_id', 'lot_id', 'package_id', 'owner_id','product_mrp']

        quants = self.env['stock.quant'].read_group(domain, fields, group_by, lazy=False)
        return {(
            quant['product_id'] and quant['product_id'][0] or False,
            quant['location_id'] and quant['location_id'][0] or False,
            quant['lot_id'] and quant['lot_id'][0] or False,
            quant['package_id'] and quant['package_id'][0] or False,
            quant['owner_id'] and quant['owner_id'][0] or False,
            quant['product_mrp'] and quant['product_mrp'][0] or False,
                ):
            quant['quantity'] for quant in quants
        }



    def _get_inventory_lines_values(self):
        """Return the values of the inventory lines to create for this inventory.

        :return: a list containing the `stock.inventory.line` values to create
        :rtype: list
        """
        self.ensure_one()
        quants_groups = self._get_quantities()
        vals = []
        product_ids = OrderedSet()
        for (product_id, location_id, lot_id, package_id, owner_id,product_mrp), quantity in quants_groups.items():
            line_values = {
                'inventory_id': self.id,
                'product_qty': 0 if self.prefill_counted_quantity == "zero" else quantity,
                'theoretical_qty': quantity,
                'prod_lot_id': lot_id,
                'partner_id': owner_id,
                'product_id': product_id,
                'location_id': location_id,
                'package_id': package_id,
                'product_mrp':product_mrp
            }
            product_ids.add(product_id)
            vals.append(line_values)
        product_id_to_product = dict(zip(product_ids, self.env['product.product'].browse(product_ids)))
        for val in vals:
            val['product_uom_id'] = product_id_to_product[val['product_id']].product_tmpl_id.uom_id.id
        if self.exhausted:
            vals += self._get_exhausted_inventory_lines_vals({(l['product_id'], l['location_id']) for l in vals})
        return vals



class InventoryLine(models.Model):
    _inherit = 'stock.inventory.line'

    product_mrp = fields.Many2one('stock.mrp.product.report', string='MRP', store=True)

    mrp = fields.Float(string='MRP', digits='Product Price', default=0.0)

    customer_locations = fields.Many2one('location.code', 'Locations', ondelete='set null',related='product_id.product_location_ids',readonly=False,store=True)


    def _check_no_duplicate_line(self):
        for i in self:
            if i.inventory_id.duplicate_product == True:
                pass
            else:
                return super(InventoryLine, self)._check_no_duplicate_line()



    @api.onchange('product_mrp','customer_locations','product_id')
    def _onchange_prod_lotmrp(self):
        for lot in self:
            # if lot.product_mrp:
            #     if lot.product_mrp.product_id.id != lot.product_id.id:
            #         # lot.product_mrp = False
            #         raise ValidationError(_("You need to Select Product wise MRP"))
            if lot.product_id:
                lot.product_mrp.product_id = lot.product_id.id
                lot.customer_locations = lot.customer_locations.id

            if lot.prod_lot_id:
                lot.prod_lot_id.product_mrp = lot.product_mrp.id
                lot.prod_lot_id.customer_locations = lot.customer_locations.id


    def _get_move_values(self, qty, location_id, location_dest_id, out):

        self.ensure_one()
        return {
            'name': _('INV:') + (self.inventory_id.name or ''),
            'product_id': self.product_id.id,
            'product_uom': self.product_uom_id.id,
            'product_uom_qty': qty,
            'date': self.inventory_id.date,
            'company_id': self.inventory_id.company_id.id,
            'inventory_id': self.inventory_id.id,
            'state': 'confirmed',
            'restrict_partner_id': self.partner_id.id,
            'location_id': location_id,
            'location_dest_id': location_dest_id,
            'move_line_ids': [(0, 0, {
                'product_id': self.product_id.id,
                'lot_id': self.prod_lot_id.id,
                'product_uom_qty': 0,  # bypass reservation here
                'product_uom_id': self.product_uom_id.id,
                'qty_done': qty,
                'package_id': out and self.package_id.id or False,
                'result_package_id': (not out) and self.package_id.id or False,
                'location_id': location_id,
                'location_dest_id': location_dest_id,
                'owner_id': self.partner_id.id,
                'product_mrp': self.product_mrp.id,
                'customer_locations':self.customer_locations.id
            })]
        }




class ProductMRPReport(models.Model):
    _name = "stock.mrp.product.report"
    _description = "Product MRP"


    name = fields.Float(string='MRP',default=0.0)
    sl_no = fields.Integer(string='sl')
    product_id = fields.Many2one('product.product',string='product',required=True)
    move_id = fields.Many2one('stock.move',string="Move")
    move_line_id = fields.Many2one('stock.move.line', string="Move Line")
    company_id = fields.Many2one('res.company', string='Company')
    mrp = fields.Float(string='MRP value',default=0.0,store=True)
    qty = fields.Float(string='MRP Qty Available',default=0.0,store=True)
    # qty = fields.Float(string='MRP Qty Available', compute='mrp_qty_available',default=0.0, store=True)
    lot_id = fields.Many2one('stock.production.lot',store=True)

    _sql_constraints = [
        (
            'unique_product_id_name','UNIQUE(name,product_id)',
            'MRP should be unique for each product.'
        )
    ]

    @api.onchange('name')
    def mrp_value(self):
        for i in self:
            i.mrp = i.name
