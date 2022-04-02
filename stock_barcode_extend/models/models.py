# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'


    @api.model
    def _get_move_line_ids_fields_to_read(self):
        """ read() on picking.move_line_ids only returns the id and the display
        name however a lot more data from stock.move.line are used by the client
        action.
        """
        res = super(StockPicking, self)._get_move_line_ids_fields_to_read()
        res.append('product_mrp')
        res.append('customer_locations')
        res.append('expiration_date')
        return res


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    @api.onchange('product_id', 'product_uom_id')
    def _onchange_product_id(self):
        res = super()._onchange_product_id()
        if self.product_id:
            self.customer_locations = self.product_id.product_location_ids.id
        return res


class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    def get_barcode_view_state(self):
        """ Return the initial state of the barcode view as a dict.
        """
        if self.env.context.get('company_id'):
            company = self.env['res.company'].browse(self.env.context['company_id'])
        else:
            company = self.env.company
        inventories = self.read([
            'line_ids',
            'location_ids',
            'name',
            'state',
            'company_id',
        ])
        for inventory in inventories:
            inventory['line_ids'] = self.env['stock.inventory.line'].browse(inventory.pop('line_ids')).read([
                'product_id',
                'location_id',
                'product_qty',
                'theoretical_qty',
                'product_uom_id',
                'prod_lot_id',
                'package_id',
                'partner_id',
                'dummy_id',
                'customer_locations',
                'product_mrp'
            ])

            # Prefetch data
            location_ids = list(set([line_id["location_id"][0] for line_id in inventory['line_ids']]))
            product_ids = list(set([line_id["product_id"][0] for line_id in inventory['line_ids']]))

            parent_path_per_location_id = {}
            for res in self.env['stock.location'].search_read([('id', 'in', location_ids)], ['parent_path']):
                parent_path_per_location_id[res.pop("id")] = res

            tracking_and_barcode_per_product_id = {}
            for res in self.env['product.product'].with_context(active_test=False).search_read([('id', 'in', product_ids)], ['tracking', 'barcode']):
                tracking_and_barcode_per_product_id[res.pop("id")] = res

            for line_id in inventory['line_ids']:
                id, name = line_id.pop('product_id')
                line_id['product_id'] = {"id": id, "display_name": name, **tracking_and_barcode_per_product_id[id]}
                id, name = line_id.pop('location_id')
                line_id['location_id'] = {"id": id, "display_name": name, **parent_path_per_location_id[id]}
            inventory['location_ids'] = self.env['stock.location'].browse(inventory.pop('location_ids')).read([
                'id',
                'display_name',
                'parent_path',
            ])
            inventory['group_stock_multi_locations'] = self.env.user.has_group('stock.group_stock_multi_locations')
            inventory['group_tracking_owner'] = self.env.user.has_group('stock.group_tracking_owner')
            inventory['group_tracking_lot'] = self.env.user.has_group('stock.group_tracking_lot')
            inventory['group_production_lot'] = self.env.user.has_group('stock.group_production_lot')
            inventory['group_uom'] = self.env.user.has_group('uom.group_uom')
            inventory['group_barcode_keyboard_shortcuts'] = self.env.user.has_group('stock_barcode.group_barcode_keyboard_shortcuts')
            inventory['actionReportInventory'] = self.env.ref('stock.action_report_inventory').id
            if self.env.company.nomenclature_id:
                inventory['nomenclature_id'] = [self.env.company.nomenclature_id.id]
            if not inventory['location_ids'] and not inventory['line_ids']:
                warehouse = self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id)], limit=1)
                inventory['location_ids'] = warehouse.lot_stock_id.read(['id', 'display_name', 'parent_path'])
        return inventories





