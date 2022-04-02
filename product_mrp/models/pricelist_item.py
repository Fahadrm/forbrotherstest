# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools
from odoo.exceptions import RedirectWarning, UserError, ValidationError
from odoo.osv import expression
from odoo.tools.float_utils import float_compare, float_is_zero, float_repr, float_round



class Pricelistitem(models.Model):
    _inherit = "product.pricelist.item"

    is_mrp = fields.Boolean(string='Based On MRP', default=False)

class Pricelist(models.Model):
    _inherit = "product.pricelist"

    is_mrp = fields.Boolean(string='Based On MRP', default=False)

class ProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    product_mrp = fields.Many2one('stock.mrp.product.report', string='MRP', store=True)
    customer_locations = fields.Many2one('location.code', 'Locations', ondelete='set null')



class StockQuant(models.Model):
    _inherit = 'stock.quant'

    product_mrp = fields.Many2one('stock.mrp.product.report', string='MRP', store=True,related='lot_id.product_mrp',readonly=False)
    customer_locations = fields.Many2one('location.code', 'Locations', ondelete='set null',store=True,related='lot_id.customer_locations',readonly=False)

    @api.model
    def _get_inventory_fields_write(self):
        """ Returns a list of fields user can edit when he want to edit a quant in `inventory_mode`.
        """
        res = super(StockQuant, self)._get_inventory_fields_write()
        # res = super()._get_inventory_fields_write()
        res.append('product_mrp')
        res.append('customer_locations')
        # res += ['product_mrp', 'customer_locations']
        return res


    # def _gather(self, product_id, location_id, lot_id=None, package_id=None, owner_id=None, strict=False):
    #     self.env['stock.quant'].flush(['location_id', 'owner_id', 'package_id', 'lot_id', 'product_id'])
    #     self.env['product.product'].flush(['virtual_available'])
    #     removal_strategy = self._get_removal_strategy(product_id, location_id)
    #     removal_strategy_order = self._get_removal_strategy_order(removal_strategy)
    #     domain = [
    #         ('product_id', '=', product_id.id),
    #     ]
    #     customer_locations = False
    #     if product_id._context.get('customer_locations'):
    #         customer_locations = product_id._context.get('customer_locations')
    #     if self._context.get('customer_locations'):
    #         customer_locations = self._context.get('customer_locations')
    #
    #     mrp = False
    #     if product_id._context.get('product_mrp'):
    #         mrp = product_id._context.get('product_mrp')
    #     if self._context.get('product_mrp'):
    #         mrp = self._context.get('product_mrp')
    #     if not strict:
    #         if lot_id and not (product_id._context.get('product_mrp') or self._context.get('product_mrp')):
    #             domain = expression.AND([['|', ('lot_id', '=', lot_id.id), ('lot_id', '=', False)], domain])
    #         if package_id:
    #             domain = expression.AND([[('package_id', '=', package_id.id)], domain])
    #         if owner_id:
    #             domain = expression.AND([[('owner_id', '=', owner_id.id)], domain])
    #
    #         if product_id._context.get('product_mrp') or self._context.get('product_mrp') and not lot_id:
    #
    #             domain = expression.AND([[('product_mrp', '=', mrp)], domain])
    #         if lot_id and product_id._context.get('product_mrp'):
    #             domain = expression.AND([['|','|', ('lot_id', '=', lot_id.id), ('lot_id', '=', False),('product_mrp', '=', mrp)], domain])
    #
    #         domain = expression.AND([[('location_id', 'child_of', location_id.id)], domain])
    #     else:
    #         domain = expression.AND([['|', ('lot_id', '=', lot_id.id), ('lot_id', '=', False)] if lot_id and not mrp else [('lot_id', '=', False)], domain])
    #         domain = expression.AND([[('package_id', '=', package_id and package_id.id or False)], domain])
    #         domain = expression.AND([[('owner_id', '=', owner_id and owner_id.id or False)], domain])
    #         domain = expression.AND([[('location_id', '=', location_id.id)], domain])
    #         domain = expression.AND([[('product_mrp', '=', mrp)], domain])
    #
    #     # Copy code of _search for special NULLS FIRST/LAST order
    #     self.check_access_rights('read')
    #     query = self._where_calc(domain)
    #     self._apply_ir_rules(query, 'read')
    #     from_clause, where_clause, where_clause_params = query.get_sql()
    #     where_str = where_clause and (" WHERE %s" % where_clause) or ''
    #     query_str = 'SELECT "%s".id FROM ' % self._table + from_clause + where_str + " ORDER BY "+ removal_strategy_order
    #     self._cr.execute(query_str, where_clause_params)
    #     res = self._cr.fetchall()
    #     # No uniquify list necessary as auto_join is not applied anyways...
    #     quants = self.browse([x[0] for x in res])
    #     quants = quants.sorted(lambda q: not q.lot_id)
    #     quants = quants.with_context( product_mrp=mrp,customer_locations=customer_locations)
    #     if lot_id:
    #         quants.update(
    #             {
    #                 'product_mrp': lot_id.product_mrp.id,
    #                 'customer_locations': lot_id.customer_locations.id
    #             }
    #         )
    #     # if product_id:
    #     #
    #     #     for i in quants:
    #     #         mrp = False
    #     #         s = i._context.get('product_mrp')
    #     #         r = i._context.get('customer_locations')
    #     #         if product_id._context.get('product_mrp'):
    #     #             mrp = product_id._context.get('product_mrp')
    #     #         if self._context.get('product_mrp'):
    #     #             mrp = self._context.get('product_mrp')
    #     #
    #     #         i.update(
    #     #         {
    #     #             'product_mrp': mrp,
    #     #             'customer_locations': customer_locations
    #     #         }
    #     #     )
    #
    #     return quants



    # def _gather(self, product_id, location_id, lot_id=None, package_id=None, owner_id=None, strict=False):
    #     res = super(StockQuant, self)._gather(product_id, location_id, lot_id, package_id, owner_id, strict)
    #     if lot_id:
    #         res.update(
    #             {
    #                 'product_mrp': lot_id.product_mrp.id,
    #                 'customer_locations': lot_id.customer_locations.id
    #             }
    #         )
    #     if product_id:
    #
    #         res.update(
    #             {
    #                 'product_mrp': product_id._context.get('product_mrp'),
    #                 'customer_locations': product_id._context.get('customer_locations')
    #             }
    #         )
    #
    #     return res

    # @api.model
    # def create(self, vals):
    #     """ Override to handle the "inventory mode" and create a quant as
    #     superuser the conditions are met.
    #     """
    #     res = super(StockQuant, self).create(vals)
    #     # for i in res:
    #     #     if i._context.get('product_mrp'):
    #     #         res.product_mrp = i._context.get('product_mrp')
    #     #     if i._context.get('customer_locations'):
    #     #         res.customer_locations = i._context.get('customer_locations')
    #     for values in vals:
    #         if 'product_mrp' in values:
    #             res.product_mrp = values['product_mrp']
    #         if 'customer_locations' in values:
    #             res.customer_locations = values['product_mrp']
    #     return res


class StockMove(models.Model):
    _inherit = "stock.move"

    product_mrp = fields.Many2one('stock.mrp.product.report', string='MRP', store=True)
    customer_locations = fields.Many2one('location.code', 'Locations', ondelete='set null')


    # def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
    #     print('_prepare_move_line_vals')
    #     self.ensure_one()
    #     # apply putaway
    #     location_dest_id = self.location_dest_id._get_putaway_strategy(self.product_id).id or self.location_dest_id.id
    #     vals = {
    #         'move_id': self.id,
    #         'product_id': self.product_id.id,
    #         'product_uom_id': self.product_uom.id,
    #         'location_id': self.location_id.id,
    #         'location_dest_id': location_dest_id,
    #         'picking_id': self.picking_id.id,
    #         'company_id': self.company_id.id,
    #     }
    #     if quantity:
    #         rounding = self.env['decimal.precision'].precision_get('Product Unit of Measure')
    #         uom_quantity = self.product_id.uom_id._compute_quantity(quantity, self.product_uom, rounding_method='HALF-UP')
    #         uom_quantity = float_round(uom_quantity, precision_digits=rounding)
    #         uom_quantity_back_to_product_uom = self.product_uom._compute_quantity(uom_quantity, self.product_id.uom_id, rounding_method='HALF-UP')
    #         if float_compare(quantity, uom_quantity_back_to_product_uom, precision_digits=rounding) == 0:
    #             vals = dict(vals, product_uom_qty=uom_quantity)
    #         else:
    #             vals = dict(vals, product_uom_qty=quantity, product_uom_id=self.product_id.uom_id.id)
    #     print('reserved_quant',reserved_quant)
    #     print('reserved_quant.lot_id',reserved_quant.lot_id.name)
    #     if reserved_quant:
    #         vals = dict(
    #             vals,
    #             location_id=reserved_quant.location_id.id,
    #             lot_id=reserved_quant.lot_id.id or False,
    #             package_id=reserved_quant.package_id.id or False,
    #             owner_id =reserved_quant.owner_id.id or False,
    #         )
    #     return vals
    def _update_reserved_quantity(self, need, available_quantity, location_id, lot_id=None, package_id=None, owner_id=None, strict=True):
        mrp_lot_id = self.env['stock.production.lot'].search([('product_id','=',self.product_id.id),('product_mrp','=',self.product_mrp.id)])
        if mrp_lot_id:
            lot_id = mrp_lot_id[0]
        return super()._update_reserved_quantity(need, available_quantity, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=strict)

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        res = super(StockMove, self)._prepare_move_line_vals(quantity, reserved_quant)
        res.update({'product_mrp': self.product_mrp.id})
        return res



class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    product_mrp = fields.Many2one('stock.mrp.product.report', string='MRP', store=True)

    def _prepare_move_values(self):
        vals = super(StockScrap, self)._prepare_move_values()
        if self.product_mrp:
            vals.update({'move_line_ids': [(0, 0, {'product_id': self.product_id.id,
                                      'product_uom_id': self.product_uom_id.id,
                                      'qty_done': self.scrap_qty,
                                      'location_id': self.location_id.id,
                                      'location_dest_id': self.scrap_location_id.id,
                                      'package_id': self.package_id.id,
                                      'owner_id': self.owner_id.id,
                                      'lot_id': self.lot_id.id,
                                      'product_mrp': self.product_mrp.id})],})

        return vals


class StockReturnPickingLine(models.TransientModel):
    _inherit = "stock.return.picking.line"

    product_mrp = fields.Many2one('stock.mrp.product.report', string='MRP', store=True)

class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    def _prepare_move_default_values(self, return_line, new_picking):
        res=super(ReturnPicking, self)._prepare_move_default_values(return_line, new_picking)
        res.update({'product_mrp': return_line.product_mrp.id})
        return res

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'


    def _prepare_procurement_values(self, group_id=False):
        res = super(SaleOrderLine, self)._prepare_procurement_values(group_id)
        res.update({'product_mrp': self.product_mrp.id})
        return res

class StockRuleInherit(models.Model):
    _inherit = 'stock.rule'

    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id, name, origin,
                                   values, group_id):
        res = super(StockRuleInherit, self)._get_stock_move_values(product_id, product_qty, product_uom,
                                                                       location_id,
                                                                       name, origin, values, group_id)
        res['product_mrp'] = group_id.get('product_mrp', False)


        return res
