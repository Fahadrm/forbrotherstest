# -*- coding: utf-8 -*-
#############################################################################


from odoo import api, fields, models,_
from functools import partial
from odoo.tools.misc import formatLang
from odoo.exceptions import UserError, ValidationError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    enable_discount = fields.Boolean(string="Activate Universal Discount", )
    sales_discount_account = fields.Many2one('account.account', string="Sales Discount Account",)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(
            sales_discount_account=int(params.get_param('account.sales_discount_account', default=False)) or False,
            enable_discount=params.get_param('account.enable_discount') or False,
        )
        return res

    def set_values(self):
        self.ensure_one()
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param("account.sales_discount_account",
                                                         self.sales_discount_account.id or False)
        self.env['ir.config_parameter'].sudo().set_param("account.enable_discount", self.enable_discount)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    is_enabled_discount = fields.Boolean('Enabled Discount',
                                         default=lambda self: self.env["ir.config_parameter"].sudo().get_param(
                                             "account.enable_discount"))

    global_discount_type = fields.Selection([('percent', 'Percentage'), ('amount', 'Amount')],
                                               string='Global Discount Type',
                                               readonly=True,
                                               states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                               default='percent')
    global_discount_rate = fields.Float('Global Discount',
                                           readonly=True,
                                           states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    amount_discount = fields.Monetary(string='Global Discount', readonly=True, compute='_amount_all', store=True,
                                         track_visibility='always')
    total_discount = fields.Monetary(string='Total Discount', readonly=True, compute='_compute_total_discount', store=True,
                                      track_visibility='always')

    @api.depends('order_line.discount', 'order_line.discount_amount', 'amount_discount')
    def _compute_total_discount(self):
        for order in self:
            total_discount = 0.0
            for line in order.order_line:
                total_discount += (line.discount_amount*line.product_uom_qty)+((line.price_unit*line.discount*line.product_uom_qty)/100)
            total_discount += order.amount_discount
            order.update({
                'total_discount': total_discount,
            })

    @api.depends('order_line.price_total', 'global_discount_rate', 'global_discount_type')
    def _amount_all(self):
        res = super(SaleOrder, self)._amount_all()
        for rec in self:
            if not ('global_tax_rate' in rec):
                rec.calculate_discount()
        return res

    # @api.multi
    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        for rec in self:
            res['global_discount_rate'] = rec.global_discount_rate
            res['global_discount_type'] = rec.global_discount_type
        return res

    # @api.multi
    def calculate_discount(self):
        for rec in self:
            if rec.global_discount_type == "amount":
                rec.amount_discount = rec.global_discount_rate if rec.amount_untaxed > 0 else 0

            elif rec.global_discount_type == "percent":
                if rec.global_discount_rate != 0.0:
                    rec.amount_discount = (rec.amount_untaxed + rec.amount_tax) * rec.global_discount_rate / 100
                else:
                    rec.amount_discount = 0
            elif not rec.global_discount_type:
                rec.amount_discount = 0
                rec.global_discount_rate = 0
            rec.amount_total = rec.amount_untaxed + rec.amount_tax - rec.amount_discount

    @api.constrains('global_discount_rate')
    def check_discount_value(self):
        if self.global_discount_type == "percent":
            if self.global_discount_rate > 100 or self.global_discount_rate < 0:
                raise ValidationError('You cannot enter percentage value greater than 100.')
        else:
            if self.global_discount_rate < 0 or self.global_discount_rate > self.amount_untaxed:
                raise ValidationError(
                    'You cannot enter discount amount greater than actual cost or value lower than 0.')

    def _compute_amount_undiscounted(self):
        for order in self:
            total = 0.0
            for line in order.order_line:
                line_discount = line.price_unit * ((line.discount or 0.0) / 100.0) * line.product_uom_qty
                if line.discount_amount and not line.discount:
                    line_discount = line.discount_amount * line.product_uom_qty
                total += line.price_subtotal + line_discount # why is there a discount in a field named amount_undiscounted ??
            order.amount_undiscounted = total

    def _amount_by_group(self):
        for order in self:
            currency = order.currency_id or order.company_id.currency_id
            fmt = partial(formatLang, self.with_context(lang=order.partner_id.lang).env, currency_obj=currency)
            res = {}
            for line in order.order_line:
                price_reduce = line.price_unit * (1.0 - line.discount / 100.0)
                if line.discount_amount and not line.discount:
                    price_reduce = line.price_unit - line.discount_amount
                taxes = line.tax_id.compute_all(price_reduce, quantity=line.product_uom_qty, product=line.product_id,
                                                partner=order.partner_shipping_id)['taxes']
                for tax in line.tax_id:
                    group = tax.tax_group_id
                    res.setdefault(group, {'amount': 0.0, 'base': 0.0})
                    for t in taxes:
                        if t['id'] == tax.id or t['id'] in tax.children_tax_ids.ids:
                            res[group]['amount'] += t['amount']
                            res[group]['base'] += t['base']
            res = sorted(res.items(), key=lambda l: l[0].sequence)
            order.amount_by_group = [(
                l[0].name, l[1]['amount'], l[1]['base'],
                fmt(l[1]['amount']), fmt(l[1]['base']),
                len(res),
            ) for l in res]


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def _create_invoice(self, order, so_line, amount):
        invoice = super(SaleAdvancePaymentInv, self)._create_invoice(order, so_line, amount)
        if invoice:
            invoice['global_discount_rate'] = order.global_discount_rate
            invoice['global_discount_type'] = order.global_discount_type
        return invoice


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    discount_amount = fields.Float(string="Discount(amt)", default=0.0)

    # @api.depends('price_unit')
    # @api.onchange('discount_amount', 'price_unit', 'quantity')
    # def onchange_discount_amount(self):
    #     for amount in self:
    #         if amount.price_unit and amount.product_uom_qty != 0:
    #             amount.discount = (amount.discount_amount * 100) / (amount.price_unit * amount.product_uom_qty)

    @api.onchange("discount")
    def _onchange_discount_percent(self):
        # _onchange_discount method already exists in core,
        # but discount is not in the onchange definition
        if self.discount:
            self.discount_amount = 0.0

    @api.onchange("discount_amount")
    def _onchange_discount_amount(self):
        if self.discount_amount:
            self.discount = 0.0

    @api.constrains("discount", "discount_amount")
    def _check_only_one_discount(self):
        for line in self:
            if line.discount and line.discount_amount:
                raise ValidationError(
                    _("You can only set one type of discount per line.")
                )

    # @api.onchange('discount', 'price_unit', 'product_uom_qty')
    # def onchange_discount_percentage(self):
    #     for i in self:
    #         if i.price_unit and i.product_uom_qty != 0:
    #             i.discount_amount = (i.discount * i.price_unit * i.product_uom_qty) / 100

    def _prepare_invoice_line(self, **optional_values):
        res = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
        res.update({'discount_amount': self.discount_amount})
        return res

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id', 'discount_amount')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            if line.discount_amount and not line.discount:
                price = line.price_unit - line.discount_amount
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
                                            product=line.product_id, partner=line.order_id.partner_shipping_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })
            if self.env.context.get('import_file', False) and not self.env.user.user_has_groups(
                    'account.group_account_manager'):
                line.tax_id.invalidate_cache(['invoice_repartition_line_ids'], [line.tax_id.id])

    @api.depends('price_unit', 'discount', 'discount_amount')
    def _get_price_reduce(self):
        for line in self:
            line.price_reduce = line.price_unit * (1.0 - line.discount / 100.0)
            if line.discount_amount and not line.discount:
                line.price_reduce = line.price_unit - line.discount_amount