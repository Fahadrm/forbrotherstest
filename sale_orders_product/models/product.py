# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from collections import defaultdict

from odoo import api, fields, models,_


class ProductProduct(models.Model):
    _inherit = 'product.product'

    mobile_fsm_quantity = fields.Float('Material Quantity', compute="_compute_mobile_fsm_quantity",
                                       inverse="_inverse_mobile_fsm_quantity")
    mobile_fsm_free_quantity = fields.Float('Free Quantity', compute="_compute_mobile_fsm_quantity",
                                            inverse="_inverse_mobile_fsm_quantity")




    def default_mobile_mrp_value(self):
        for war in self:
            string = 0.00
            price_list_value = 0.00
            if war.with_context(all_default_mrps=1):
                product_id = self.env['product.product'].search([('product_tmpl_id', '=', war.id)])
                product_stock_location = self.env['stock.mrp.product.report'].search(
                    [('product_id', '=', product_id[0].id)])
                warehouse_names = []
                if product_stock_location:
                    for n in product_stock_location:
                        vals = {
                            "mrp": n.name if n.name else 0.00,
                            "mrp_name": n.name if n.name else 0,
                         "mrp_id": n.id if n.id else 0,
                        }
                        warehouse_names.append(vals)
                        warehouse_names = sorted(warehouse_names, key=lambda k: k['mrp_id'])
                    if warehouse_names:
                        temp_string = warehouse_names[0]['mrp'] if warehouse_names[0]['mrp'] else 0.00
                        string = temp_string
                        order = self.env['sale.order'].search([('id', '=', self.env.context.get('fsm_sale_id'))])
                        product_context = dict(self.env.context, partner_id=self.env.context.get('partner_id'),
                                               date=self.env.context.get('date_order'), uom=n.product_id.uom_id.id,)
                        price, rule_id = order.pricelist_id.with_context(
                            product_context).get_product_price_rule(
                            n.product_id, n.product_id.mobile_fsm_quantity or 1.0, self.env.context.get('partner_id'))
                        pricelist_rule = self.env['product.pricelist.item'].browse(rule_id)

                        if self.env['sale.order'].search([('id','=',self.env.context.get('fsm_sale_id'))]).pricelist_id and self.env.context.get('partner_id') and order.pricelist_id.item_ids.filtered(
                                lambda l: l.is_mrp == True):
                            if pricelist_rule:
                                for item in pricelist_rule:
                                    if item.is_mrp == True:
                                        product = n.product_id.with_context(
                                            lang=self.env.context.get('lang'),
                                            partner=self.env.context.get('partner_id'),
                                            quantity=n.product_id.mobile_fsm_quantity,
                                            date=self.env.context.get('date_order'),
                                            pricelist=self.env.context.get('pricelist'),
                                            uom=n.product_id.uom_id.id,
                                            fiscal_position=self.env.context.get('fiscal_position'),
                                            product_mrp=warehouse_names[0]['mrp_id']
                                        )
                                        # price_list_value = n.product_id.price_compute('list_price')
                                        price_list_product = self.env['account.tax']._fix_tax_included_price_company(product,
                                                                                                                     n.product_id.taxes_id,
                                                                                                                     n.product_id.taxes_id,
                                                                                                                     n.product_id.company_id)
                                        price_list_value = price_list_product.price
                                        war.mobile_pricelist_value = price_list_value
                            else:
                                price_list_value = n.product_id.price
                        else:
                            price_list_value = n.product_id.price

                    else:
                        temp_string = 0.00
                        string = temp_string
            war.mobile_mrp_value = string
            war.mobile_pricelist_value = price_list_value
            # self.update_price_value(price_list_value,war.id)




    mobile_fsm_mrp = fields.Many2one('stock.mrp.product.report',string='MRP Value', compute="_compute_mobile_fsm_quantity", inverse="_inverse_mobile_fsm_quantity")
    mobile_mrp_value = fields.Float('MRP', compute="default_mobile_mrp_value")
    sale_note = fields.Char('Mobile Note')
    is_mrp_val = fields.Boolean("Is MRP?",default=False)
    de_mobile_mrp_value = fields.Float()
    mobile_pricelist_value = fields.Float('Product value')



    def mobile_note(self):
        action = self.env.ref(
            'sale_orders_product.action_form_for_note').sudo().read()[0]
        action['context'] = {
            'default_res_model': self._name,
            'default_res_id': self.ids[0],
            'fsm_sale_id': self.env.context.get('fsm_sale_id'),
            'fsm_product_id':self.id,
        }
        return action

    def mobile_mrp_view(self):
        action = self.env.ref(
            'sale_orders_product.action_form_for_mrp').sudo().read()[0]
        action['context'] = {
            'default_res_model': self._name,
            'default_res_id': self.ids[0],
            'fsm_sale_id': self.env.context.get('fsm_sale_id'),
            'fsm_product_id':self.id,
            'default_product_id': self.id,
            # 'product_mrp':self.mobile_fsm_mrp.id,
        }
        return action


    @api.depends_context('fsm_sale_id')
    def _compute_mobile_fsm_quantity(self):
        sale = self._get_contextual_mobile_fsm_task()
        if sale:

            SaleOrderLine = self.env['sale.order.line']
            if self.user_has_groups('sales_team.group_sale_salesman'):
                sale = sale.sudo()
                SaleOrderLine = SaleOrderLine.sudo()

            products_qties = SaleOrderLine.read_group(
                [('id', 'in', sale.order_line.ids)],
                ['product_id', 'product_uom_qty'], ['product_id'])
            products_free_qties = SaleOrderLine.read_group(
                [('id', 'in', sale.order_line.ids)],
                ['product_id', 'free_qty'], ['product_id'])
            qty_dict = dict([(x['product_id'][0], x['product_uom_qty']) for x in products_qties if x['product_id']])
            free_qty_dict = dict([(x['product_id'][0], x['free_qty']) for x in products_free_qties if x['product_id']])

            for product in self:
                product.mobile_fsm_quantity = qty_dict.get(product.id, 0)
                product.mobile_fsm_free_quantity = free_qty_dict.get(product.id, 0)
        else:
            self.mobile_fsm_quantity = False
            self.mobile_fsm_free_quantity = False

    def _inverse_mobile_fsm_quantity(self):
        sale = self._get_contextual_mobile_fsm_task()
        if sale:
            for product in self:
                sale_line = self.env['sale.order.line'].search([('order_id', '=', sale.id), ('product_id', '=', product.id), '|', '|', ('qty_delivered', '=', 0.0), ('qty_delivered_method', '=', 'manual'), ('state', 'not in', ['sale', 'done'])], limit=1)
                if sale_line:  # existing line: change ordered qty (and delivered, if delivered method)
                    vals = {
                        'product_uom_qty': product.mobile_fsm_quantity,
                        'free_qty':product.mobile_fsm_free_quantity
                    }
                    if sale_line.qty_delivered_method == 'manual':
                        vals['qty_delivered'] = product.mobile_fsm_quantity
                        vals['free_qty'] = product.mobile_fsm_free_quantity
                    sale_line.with_context(fsm_no_message_post=True).write(vals)
                else:  # create new SOL
                    vals = {
                        'order_id': sale.id,
                        'product_id': product.id,
                        'product_uom_qty': product.mobile_fsm_quantity,
                        'product_uom': product.uom_id.id,
                        'free_qty':product.mobile_fsm_free_quantity,
                    }
                    if product.service_type == 'manual':
                        vals['qty_delivered'] = product.mobile_fsm_quantity
                        vals['free_qty'] = product.mobile_fsm_free_quantity

                    if sale.pricelist_id.discount_policy == 'without_discount':
                        sol = self.env['sale.order.line'].new(vals)
                        sol._onchange_discount()
                        vals.update({'discount': sol.discount or 0.0})
                    sale_line = self.env['sale.order.line'].create(vals)

    @api.model
    def _get_contextual_mobile_fsm_task(self):
        sale_id = self.env.context.get('fsm_sale_id')
        if sale_id:
            return self.env['sale.order'].browse(sale_id)
        return self.env['sale.order']

    def set_mobile_fsm_quantity(self, quantity):
        sale = self._get_contextual_mobile_fsm_task()
        # project user with no sale rights should be able to change material quantities
        if not sale or quantity and quantity < 0 or not self.user_has_groups('sales_team.group_sale_salesman'):
            return
        self = self.sudo()
        # don't add material on confirmed/locked SO to avoid inconsistence with the stock picking
        if sale.state == 'done':
            return False
        # ensure that the task is linked to a sale order
        # wizard_product_lot = self.action_assign_serial()
        # if wizard_product_lot:
        #     return wizard_product_lot
        self.mobile_fsm_quantity = quantity
        return True


    def set_mobile_fsm_free_quantity(self, quantity):
        sale = self._get_contextual_mobile_fsm_task()
        # project user with no sale rights should be able to change material quantities
        if not sale or quantity and quantity < 0 or not self.user_has_groups('sales_team.group_sale_salesman'):
            return
        self = self.sudo()
        # don't add material on confirmed/locked SO to avoid inconsistence with the stock picking
        if sale.state == 'done':
            return False
        # ensure that the task is linked to a sale order

        self.mobile_fsm_free_quantity = quantity
        return True


    # Is override by fsm_stock to manage lot
    def action_assign_serial(self):
        return False

    def mobile_fsm_add_quantity(self):
        return self.set_mobile_fsm_quantity(self.sudo().mobile_fsm_quantity + 1)

    def mobile_fsm_remove_quantity(self):
        return self.set_mobile_fsm_quantity(self.sudo().mobile_fsm_quantity - 1)

    def mobile_fsm_free_add_quantity(self):
        return self.set_mobile_fsm_free_quantity(self.sudo().mobile_fsm_free_quantity + 1)

    def mobile_fsm_free_remove_quantity(self):
        return self.set_mobile_fsm_free_quantity(self.sudo().mobile_fsm_free_quantity - 1)


class SaleLineNote(models.TransientModel):
    _name = 'sale.line.note'

    # @api.depends('product_id')
    # @api.depends_context('fsm_sale_id', 'show_mrp')
    def _compute_get_lot_mrps(self):
        mrp_float = []
        order = self.env['product.product'].browse(self._context.get('fsm_product_id'))
        for product in order:
            lot_mrp = product.product_mrp_ids
            if lot_mrp:
                for rec in lot_mrp:
                    mrp_float.append(rec.id)

        res = {}
        res['domain'] = {'mrp_value': [('id', 'in', mrp_float)]}
        return [('id', 'in', mrp_float)]

    def default_mobile_mrp_value(self):
        for war in self:
            string = 0
            product_id = self.env['product.product'].search([('product_tmpl_id', '=', war.product_id.id)])
            product_stock_location = self.env['stock.mrp.product.report'].search(
                [('product_id', '=', product_id[0].id)])
            warehouse_names = []
            if product_stock_location:
                for n in product_stock_location:
                    vals = {
                        "mrp": n.mrp if n.mrp else 0.00,
                        "mrp_name": n.name if n.name else 0,
                        "mrp_id": n.id if n.id else 0
                    }
                    warehouse_names.append(vals)
                    warehouse_names = sorted(warehouse_names, key=lambda k: k['mrp_id'])
                if warehouse_names:
                    temp_string = warehouse_names[0]['mrp_id'] if warehouse_names[0]['mrp_id'] else 0
                    string = temp_string
                else:
                    temp_string = 0
                    string = temp_string
            war.mrp_value = string


    sale_note = fields.Char(string="Note",store=True)
    sale_id = fields.Many2one('sale.order', string='Sale Order',store=True)
    product_id = fields.Many2one('product.product', string='Product',store=True)
    mrp_value = fields.Many2one('stock.mrp.product.report',string='MRP',store=True,domain=_compute_get_lot_mrps)


    @api.model
    def _prepare_default_get(self, order):
        string = order.mobile_fsm_mrp.id
        product_stock_location = self.env['stock.mrp.product.report'].search(
            [('product_id', '=', order.id)])
        recs_sorted = order.product_mrp_ids.sorted(key=lambda r: r.id)
        mrp_id = recs_sorted[0] if recs_sorted else 0
        if mrp_id:
            string = mrp_id.id
        else:
            string = order.mobile_fsm_mrp.id


        default = {
            'sale_id': self._context.get('fsm_sale_id'),
            'sale_note':order.sale_note,
            'product_id':order.id,
            # 'mrp_value':order.mobile_fsm_mrp.id,
            'mrp_value': string,

        }
        return default

    @api.model
    def default_get(self, fields):
        res = super(SaleLineNote, self).default_get(fields)
        assert self._context.get('active_model') == 'product.product', \
            'active_model should be product.product'
        sale = self._context.get('fsm_sale_id')
        sale_order = self.env['sale.order'].browse(sale)
        order = self.env['product.product'].browse(self._context.get('active_id'))
        default = self._prepare_default_get(order)
        self._compute_get_lot_mrps()
        res.update(default)
        return res


    @api.model
    def _get_contextual_mobile_fsm_task(self):
        sale_id = self.env.context.get('fsm_sale_id')
        if sale_id:
            return self.env['sale.order'].browse(sale_id)
        return self.env['sale.order']

    def confirm(self):
        self.ensure_one()
        # confirm sale order
        sale_order = self.env['sale.order'].browse(self._context.get('fsm_sale_id'))
        sale = self._get_contextual_mobile_fsm_task()
        if sale:
            for product in self:
                # sale_line = self.env['sale.order.line'].search(
                #     [('order_id', '=', sale.id), '|', '|', ('qty_delivered', '=', 0.0),
                #      ('qty_delivered_method', '=', 'manual'), ('state', 'not in', ['sale', 'done'])], limit=1)
                # if sale_line:  # existing line: change ordered qty (and delivered, if delivered method)
                vals = {
                        'name': self.sale_note,
                        'order_id': sale.id,
                        'display_type': 'line_note',
                        'product_id': False,
                        'product_uom_qty': 0,
                        'product_uom': False,
                        'price_unit': 0,
                        'tax_id': False,
                    }

                sale_line = self.env['sale.order.line'].create(vals)
        # vals = self._prepare_update_so()
        # self.sale_id.write(vals)
        return True


    def add_mrp_button(self):
        sale = self._get_contextual_mobile_fsm_task()
        if sale:
            for product in self:
                sale_line = self.env['sale.order.line'].search([('order_id', '=', sale.id), ('product_id', '=', product.product_id.id), '|', '|', ('qty_delivered', '=', 0.0), ('qty_delivered_method', '=', 'manual'), ('state', 'not in', ['sale', 'done'])], limit=1)
                if product.mrp_value:
                    product.product_id.with_context(
                        product_mrp=product.mrp_value.id,
                        all_default_mrps=0
                    ).mobile_mrp_value = product.mrp_value.mrp
                    product.product_id.with_context(
                        product_mrp=product.mrp_value.id,
                        all_default_mrps=0
                    ).write({'mobile_mrp_value': product.mrp_value.name})
                    product.product_id.is_mrp_val = True
                if sale_line:  # existing line: change ordered qty (and delivered, if delivered method)

                    # mobile_mrp_value
                    vals = {
                        'product_mrp': product.mrp_value.id,
                        'qty_available': product.mrp_value.qty
                    }
                    if sale_line.qty_delivered_method == 'manual':
                        vals['product_mrp'] = product.mrp_value.id
                        vals['qty_available'] = product.mrp_value.qty
                    product.product_id.with_context(
                        product_mrp=product.mrp_value.id
                    )
                    sale_line.with_context(fsm_no_message_post=True,product_mrp=product.mrp_value.id).write(vals)

                    sale_line.product_mrp_change()
                    sale_line.product_id.mobile_pricelist_value = sale_line.price_unit
                else:  # create new SOL
                    vals = {
                        'order_id': sale.id,
                        'product_id': product.product_id.id,
                        # 'product_uom_qty': product.mobile_fsm_quantity,
                        'product_uom': product.product_id.uom_id.id,
                        'product_mrp': product.mrp_value.id,
                        'qty_available':product.mrp_value.qty
                    }
                    if product.product_id.service_type == 'manual':
                        vals['product_mrp'] = product.mrp_value.id
                    if sale.pricelist_id.discount_policy == 'without_discount':
                        sol = self.env['sale.order.line'].new(vals)
                        sol._onchange_discount()
                        vals.update({'discount': sol.discount or 0.0})

                    sale_line = self.env['sale.order.line'].with_context(
                        product_mrp=product.mrp_value.id
                    ).create(vals)
                    sale_line.product_mrp_change()
                    sale_line.product_id.mobile_pricelist_value = sale_line.price_unit

