# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.osv import expression
from odoo.exceptions import UserError
from collections import Counter, defaultdict
from odoo.exceptions import AccessDenied, ValidationError
from odoo.tools.misc import OrderedSet
from odoo.tools import float_compare, float_round, float_repr






class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    sl_no = fields.Integer(string='Sl No.',store=True)
    product_mrp = fields.Many2one('stock.mrp.product.report', string='MRP', store=True,)
    customer_locations = fields.Many2one('location.code', 'Locations', ondelete='set null',related='product_id.product_location_ids',readonly=False,store=True)

    @api.onchange('product_mrp', 'customer_locations')
    def _onchange_prod_lot_mrp_move_line(self):
        for lot in self:
            # if lot.product_mrp:
            #     if lot.product_mrp.product_id.id != lot.product_id.id:
            #         # lot.product_mrp = False
            #         raise ValidationError(_("You need to Select Product wise MRP"))
            if lot.product_id:
                lot.product_mrp.product_id = lot.product_id.id
                lot.customer_locations = lot.customer_locations.id
            if lot.lot_id:
                lot.lot_id.product_mrp = lot.product_mrp.id
                lot.lot_id.customer_locations = lot.customer_locations.id
            if lot.lot_name:
                lots=self.env['stock.production.lot'].search([('product_id','=',lot.product_id.id),('name','=',lot.lot_name)])
                for i in lots:
                    i.product_mrp = lot.product_mrp.id
                    i.customer_locations = lot.customer_locations.id





    @api.model_create_multi
    def create(self, vals_list):
        res = super(StockMoveLine, self).create(vals_list)
        for i in res:
            exsiting_mrp_id = self.env['stock.mrp.product.report'].search([('product_id', '=', i.product_id.id),
                                                                           ('id', '=', i.product_mrp.id)])

            if exsiting_mrp_id:
                # i.write(())
                if i.picking_code == 'incoming':
                    onhand_qty = i.qty_done + exsiting_mrp_id.qty
                    exsiting_mrp_id.write({'qty': onhand_qty})
                elif i.picking_code == 'outgoing':
                    onhand_qty = exsiting_mrp_id.qty - i.qty_done
                    exsiting_mrp_id.write({'qty': onhand_qty})
                elif i.picking_code == 'internal':
                    if i.picking_id.location_id.usage == 'internal' and i.picking_id.location_dest_id.usage in ['supplier', 'customer', 'inventory', 'production', 'transit']:
                        onhand_qty = exsiting_mrp_id.qty - i.qty_done
                        exsiting_mrp_id.write({'qty': onhand_qty})
                    elif i.picking_id.location_dest_id.usage == 'internal' and i.picking_id.location_id.usage in ['supplier', 'customer', 'inventory', 'production', 'transit']:
                        onhand_qty = i.qty_done + exsiting_mrp_id.qty
                        exsiting_mrp_id.write({'qty': onhand_qty})

                else:
                    onhand_qty = i.qty_done + exsiting_mrp_id.qty
                    exsiting_mrp_id.write({'qty': onhand_qty})


            else:
                if i.product_mrp:
                # if i.product_mrp.id == vals['product_mrp']:
                    sample_settlement = self.env['stock.mrp.product.report'].create({
                    'sl_no': i.sl_no,
                    'name': i.product_mrp.name,
                    'product_id': i.product_id.id,
                    'mrp': i.product_mrp.name,
                    'company_id': i.company_id.id,
                    'move_id': i.move_id.id,
                    'move_line_id': i.id,
                    'lot_id': i.lot_id.id,
                    'qty': i.qty_done,

                })
            # if i.product_mrp:

        # for vals in vals_list:
        #     if 'product_mrp' in vals:

        return res

    def write(self, vals):
        res = super(StockMoveLine, self).write(vals)
        for i in self:
            if 'qty_done' in vals:
                exsiting_mrp_id = self.env['stock.mrp.product.report'].search([('product_id', '=', i.product_id.id),
                                                                               ('id', '=', i.product_mrp.id)])

                if exsiting_mrp_id:
                    # i.write(())
                    if i.picking_code == 'incoming':
                        onhand_qty = vals['qty_done'] + exsiting_mrp_id.qty
                        exsiting_mrp_id.write({'qty': onhand_qty})
                    elif i.picking_code == 'outgoing':
                        onhand_qty = exsiting_mrp_id.qty - vals['qty_done']
                        exsiting_mrp_id.write({'qty': onhand_qty})
                    elif i.picking_code == 'internal':
                        if i.picking_id.location_id.usage=='internal' and  i.picking_id.location_dest_id.usage in ['supplier','customer','inventory','production','transit']:
                            onhand_qty = exsiting_mrp_id.qty - vals['qty_done']
                            exsiting_mrp_id.write({'qty': onhand_qty})
                        elif i.picking_id.location_dest_id.usage == 'internal' and i.picking_id.location_id.usage in ['supplier', 'customer', 'inventory', 'production', 'transit']:
                            onhand_qty = exsiting_mrp_id.qty + vals['qty_done']
                            exsiting_mrp_id.write({'qty': onhand_qty})

                    else:
                        onhand_qty = vals['qty_done'] + exsiting_mrp_id.qty
                        exsiting_mrp_id.write({'qty': onhand_qty})


                else:
                    if i.product_mrp:
                    # if i.product_mrp.id == vals['product_mrp']:
                        sample_settlement = self.env['stock.mrp.product.report'].create({
                        'sl_no': i.sl_no,
                        'name': i.product_mrp.name,
                        'product_id': i.product_id.id,
                        'mrp': i.product_mrp.name,
                        'company_id': i.company_id.id,
                        'move_id': i.move_id.id,
                        'move_line_id': i.id,
                        'lot_id': i.lot_id.id,
                        'qty': i.qty_done,

                    })
        return res


    def _create_and_assign_production_lot(self):
        """ Creates and assign new production lots for move lines."""
        lot_vals = []
        # It is possible to have multiple time the same lot to create & assign,
        # so we handle the case with 2 dictionaries.
        key_to_index = {}  # key to index of the lot
        key_to_mls = defaultdict(lambda: self.env['stock.move.line'])  # key to all mls
        for ml in self:
            key = (ml.company_id.id, ml.product_id.id, ml.lot_name)
            key_to_mls[key] |= ml
            if ml.tracking != 'lot' or key not in key_to_index:
                key_to_index[key] = len(lot_vals)
                lot_vals.append({
                    'company_id': ml.company_id.id,
                    'name': ml.lot_name,
                    'product_id': ml.product_id.id,
                    'product_mrp': ml.product_mrp.id,
                    'customer_locations':ml.customer_locations.id
                })
        lots = self.env['stock.production.lot'].create(lot_vals)
        for key, mls in key_to_mls.items():
            mls._assign_production_lot(lots[key_to_index[key]].with_prefetch(lots._ids))  # With prefetch to reconstruct the ones broke by accessing by index

    def _action_done(self):
        """ This method is called during a move's `action_done`. It'll actually move a quant from
        the source location to the destination location, and unreserve if needed in the source
        location.

        This method is intended to be called on all the move lines of a move. This method is not
        intended to be called when editing a `done` move (that's what the override of `write` here
        is done.
        """
        Quant = self.env['stock.quant']

        # First, we loop over all the move lines to do a preliminary check: `qty_done` should not
        # be negative and, according to the presence of a picking type or a linked inventory
        # adjustment, enforce some rules on the `lot_id` field. If `qty_done` is null, we unlink
        # the line. It is mandatory in order to free the reservation and correctly apply
        # `action_done` on the next move lines.
        ml_ids_tracked_without_lot = OrderedSet()
        ml_ids_to_delete = OrderedSet()
        ml_ids_to_create_lot = OrderedSet()
        for ml in self:
            # Check here if `ml.qty_done` respects the rounding of `ml.product_uom_id`.
            uom_qty = float_round(ml.qty_done, precision_rounding=ml.product_uom_id.rounding, rounding_method='HALF-UP')
            precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            qty_done = float_round(ml.qty_done, precision_digits=precision_digits, rounding_method='HALF-UP')
            if float_compare(uom_qty, qty_done, precision_digits=precision_digits) != 0:
                raise UserError(_('The quantity done for the product "%s" doesn\'t respect the rounding precision \
                                  defined on the unit of measure "%s". Please change the quantity done or the \
                                  rounding precision of your unit of measure.') % (ml.product_id.display_name, ml.product_uom_id.name))

            qty_done_float_compared = float_compare(ml.qty_done, 0, precision_rounding=ml.product_uom_id.rounding)
            if qty_done_float_compared > 0:
                if ml.product_id.tracking != 'none':
                    picking_type_id = ml.move_id.picking_type_id
                    if picking_type_id:
                        if picking_type_id.use_create_lots:
                            # If a picking type is linked, we may have to create a production lot on
                            # the fly before assigning it to the move line if the user checked both
                            # `use_create_lots` and `use_existing_lots`.
                            if ml.lot_name and not ml.lot_id:
                                lot = self.env['stock.production.lot'].search([
                                    ('company_id', '=', ml.company_id.id),
                                    ('product_id', '=', ml.product_id.id),
                                    ('name', '=', ml.lot_name),
                                ], limit=1)
                                if lot:
                                    ml.lot_id = lot.id
                                else:
                                    ml_ids_to_create_lot.add(ml.id)
                        elif not picking_type_id.use_create_lots and not picking_type_id.use_existing_lots:
                            # If the user disabled both `use_create_lots` and `use_existing_lots`
                            # checkboxes on the picking type, he's allowed to enter tracked
                            # products without a `lot_id`.
                            continue
                    elif ml.move_id.inventory_id:
                        # If an inventory adjustment is linked, the user is allowed to enter
                        # tracked products without a `lot_id`.
                        continue

                    if not ml.lot_id and ml.id not in ml_ids_to_create_lot:
                        ml_ids_tracked_without_lot.add(ml.id)
            elif qty_done_float_compared < 0:
                raise UserError(_('No negative quantities allowed'))
            else:
                ml_ids_to_delete.add(ml.id)

        if ml_ids_tracked_without_lot:
            mls_tracked_without_lot = self.env['stock.move.line'].browse(ml_ids_tracked_without_lot)
            raise UserError(_('You need to supply a Lot/Serial Number for product: \n - ') +
                              '\n - '.join(mls_tracked_without_lot.mapped('product_id.display_name')))
        ml_to_create_lot = self.env['stock.move.line'].browse(ml_ids_to_create_lot)
        ml_to_create_lot._create_and_assign_production_lot()

        mls_to_delete = self.env['stock.move.line'].browse(ml_ids_to_delete)
        mls_to_delete.unlink()

        mls_todo = (self - mls_to_delete)
        mls_todo._check_company()

        # Now, we can actually move the quant.
        ml_ids_to_ignore = OrderedSet()
        for ml in mls_todo:
            if ml.product_id.type == 'product':
                rounding = ml.product_uom_id.rounding

                # if this move line is force assigned, unreserve elsewhere if needed
                if not ml._should_bypass_reservation(ml.location_id) and float_compare(ml.qty_done, ml.product_uom_qty, precision_rounding=rounding) > 0:
                    qty_done_product_uom = ml.product_uom_id._compute_quantity(ml.qty_done, ml.product_id.uom_id, rounding_method='HALF-UP')
                    extra_qty = qty_done_product_uom - ml.product_qty
                    ml_to_ignore = self.env['stock.move.line'].browse(ml_ids_to_ignore)
                    ml._free_reservation(ml.product_id, ml.location_id, extra_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id, ml_to_ignore=ml_to_ignore)
                # unreserve what's been reserved
                if not ml._should_bypass_reservation(ml.location_id) and ml.product_id.type == 'product' and ml.product_qty:
                    Quant._update_reserved_quantity(ml.product_id, ml.location_id, -ml.product_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)

                # move what's been actually done
                quantity = ml.product_uom_id._compute_quantity(ml.qty_done, ml.move_id.product_id.uom_id, rounding_method='HALF-UP')
                available_qty, in_date = Quant.with_context( product_mrp=ml.product_mrp.id,customer_locations=ml.customer_locations.id)._update_available_quantity(ml.product_id.with_context( product_mrp=ml.product_mrp.id,customer_locations=ml.customer_locations.id), ml.location_id, -quantity, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id)
                if available_qty < 0 and ml.lot_id:
                    # see if we can compensate the negative quants with some untracked quants
                    untracked_qty = Quant._get_available_quantity(ml.product_id.with_context( product_mrp=ml.product_mrp.id,customer_locations=ml.customer_locations.id), ml.location_id, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
                    if untracked_qty:
                        taken_from_untracked_qty = min(untracked_qty, abs(quantity))
                        Quant.with_context( product_mrp=ml.product_mrp.id,customer_locations=ml.customer_locations.id)._update_available_quantity(ml.product_id.with_context( product_mrp=ml.product_mrp.id,customer_locations=ml.customer_locations.id), ml.location_id, -taken_from_untracked_qty, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id)
                        Quant.with_context( product_mrp=ml.product_mrp.id,customer_locations=ml.customer_locations.id)._update_available_quantity(ml.product_id.with_context( product_mrp=ml.product_mrp.id,customer_locations=ml.customer_locations.id), ml.location_id, taken_from_untracked_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id)
                Quant.with_context( product_mrp=ml.product_mrp.id,customer_locations=ml.customer_locations.id)._update_available_quantity(ml.product_id.with_context( product_mrp=ml.product_mrp.id,customer_locations=ml.customer_locations.id), ml.location_dest_id, quantity, lot_id=ml.lot_id, package_id=ml.result_package_id, owner_id=ml.owner_id, in_date=in_date)
            ml_ids_to_ignore.add(ml.id)
        # Reset the reserved quantity as we just moved it to the destination location.
        mls_todo.with_context(bypass_reservation_update=True).write({
            'product_uom_qty': 0.00,
            'date': fields.Datetime.now(),
        })
