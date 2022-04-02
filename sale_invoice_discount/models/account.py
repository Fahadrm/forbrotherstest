# -*- coding: utf-8 -*-


from odoo import api, fields, models,_
from odoo.exceptions import UserError, ValidationError


class AccountInvoice(models.Model):
    _inherit = "account.move"

    global_discount_type = fields.Selection([
        ('percent', 'Percentage'),
        ('amount', 'Amount')],
        string='Global Discount Type',
        readonly=True,
        states={'draft': [('readonly', False)],
                'sent': [('readonly', False)]},
        default='percent')
    global_discount_rate = fields.Float('Global Discount',
                                           readonly=True,
                                           states={'draft': [('readonly', False)],
                                                   'sent': [('readonly', False)]})
    amount_discount = fields.Monetary(string='Global Discount',
                                         readonly=True,
                                         compute='_compute_amount',
                                         store=True, track_visibility='always')

    round_active = fields.Boolean('Enabled Discount', default=lambda self: self.env["ir.config_parameter"].sudo().get_param("account.enable_discount"))

    # enable_discount = fields.Boolean(compute='verify_discount')
    # sales_discount_account_id = fields.Integer(compute='verify_discount')

    def _create_global_discount_journal_items(self):
        """Append global discounts move lines"""
        lines_to_delete = self.line_ids.filtered("global_discount_item")
        # if self != self._origin:
        #     self.line_ids -= lines_to_delete
        # else:
        #     lines_to_delete.with_context(check_move_validity=False).unlink()
        vals_list = []

        for discount in self:
            if discount.round_active == True and discount.global_discount_rate:
                # If rounding amount is available, then update the total amount and add the roundoff value as new line.
                account_id = int(self.env['ir.config_parameter'].sudo().get_param("account.sales_discount_account"))
                flag = False
                already_exists = self.line_ids.filtered(lambda line: line.name =='Discount Amount')
                already_exists.unlink()

                account = self.env['account.account'].browse(account_id)
                disc_amount = discount.amount_discount
                if (
                        self.currency_id
                        and self.company_id
                        and self.currency_id != self.company_id.currency_id
                ):
                    date = self.invoice_date or fields.Date.today()

                    disc_amount = self.currency_id._convert(
                        self.amount_discount, self.company_id.currency_id, self.company_id, date
                    )
                if self.move_type in ['out_refund']:
                    vals_list.append(
                        (
                            0,
                            0,
                            {
                                "global_discount_item": True,
                                'name': 'Discount Amount',
                                "debit":  disc_amount < 0.0 and -disc_amount or 0.0,
                                "credit": disc_amount > 0.0 and disc_amount or 0.0,
                                "account_id": account.id,
                                # "analytic_account_id": discount.account_analytic_id.id,
                                "exclude_from_invoice_tab": True,
                            },
                        )
                    )
                else:
                    vals_list.append(
                            (
                                0,
                                0,
                                {
                                    "global_discount_item": True,
                                    'name': 'Discount Amount',
                                    "debit": disc_amount > 0.0 and disc_amount or 0.0,
                                    "credit": disc_amount < 0.0 and -disc_amount or 0.0,
                                    "account_id": account.id,
                                    # "analytic_account_id": discount.account_analytic_id.id,
                                    "exclude_from_invoice_tab": True,
                                },
                            )
                        )
        self.line_ids = vals_list
        self._onchange_recompute_dynamic_lines()

    def _set_global_discounts(self):
        """Get global discounts in order and apply them in chain. They will be
        fetched in their sequence order"""
        for inv in self:
            # inv._set_global_discounts_by_tax()
            inv._create_global_discount_journal_items()

    # @api.depends("invoice_line_ids","global_discount_rate",
    #     "amount_discount",
    #     "global_discount_type")
    @api.onchange("invoice_line_ids", "global_discount_rate", "amount_discount", "global_discount_type")
    def _onchange_invoice_line_ids(self):
        others_lines = self.line_ids.filtered(
            lambda line: line.exclude_from_invoice_tab
        )
        if others_lines:
            others_lines[0].recompute_tax_line = True
        res = super()._onchange_invoice_line_ids()
        self._set_global_discounts()
        return res

    def _compute_amount_one(self):
        if not self.global_discount_rate :
            self.amount_discount = 0.0
            return
        round_curr = self.currency_id.round
        if self.global_discount_type == "amount":
            self.amount_discount = self.global_discount_rate if self.amount_untaxed > 0 else 0
        elif self.global_discount_type == "percent":
            if self.global_discount_rate != 0.0:
                self.amount_discount = (self.amount_untaxed + self.amount_tax) * self.global_discount_rate / 100
            else:
                self.amount_discount = 0
        elif not self.global_discount_type:
            self.global_discount_rate = 0
            self.amount_discount = 0
        self.amount_total = self.amount_tax + self.amount_untaxed - self.amount_discount

        amount_untaxed_signed = self.amount_untaxed
        if (
            self.currency_id
            and self.company_id
            and self.currency_id != self.company_id.currency_id
        ):
            date = self.invoice_date or fields.Date.today()

            amount_untaxed_signed = self.currency_id._convert(
                self.amount_untaxed, self.company_id.currency_id, self.company_id, date
            )
        sign = self.move_type in ["in_refund", "out_refund"] and -1 or 1
        self.amount_total_signed = self.amount_total * sign
        self.amount_untaxed_signed = amount_untaxed_signed * sign


    @api.depends(
        "line_ids.debit",
        "line_ids.credit",
        "line_ids.currency_id",
        "line_ids.amount_currency",
        "line_ids.amount_residual",
        "line_ids.amount_residual_currency",
        "line_ids.payment_id.state",
        "global_discount_rate",
        "amount_discount",
        "global_discount_type"
    )
    def _compute_amount(self):
        super()._compute_amount()
        for record in self:
            record._compute_amount_one()
            # self._set_global_discounts()
            # record.discount_value()

    # @api.depends('debit', 'credit', 'amount_currency', 'account_id', 'currency_id', 'move_id.state', 'company_id',
    #              'matched_debit_ids', 'matched_credit_ids',"global_discount_rate",
    #     "amount_discount",
    #     "global_discount_type")
    # def _compute_amount_residual(self):
    #     res = super()._compute_amount()
    #     """ Computes the residual amount of a move line from a reconcilable account in the company currency and the line's currency.
    #         This amount will be 0 for fully reconciled lines or lines from a non-reconcilable account, the original line amount
    #         for unreconciled lines, and something in-between for partially reconciled lines.
    #     """
    #     for line in self:
    #         if line.id and (line.account_id.reconcile or line.account_id.internal_type == 'liquidity'):
    #             reconciled_balance = sum(line.matched_credit_ids.mapped('amount')) \
    #                                  - sum(line.matched_debit_ids.mapped('amount'))
    #             reconciled_amount_currency = sum(line.matched_credit_ids.mapped('debit_amount_currency')) \
    #                                          - sum(line.matched_debit_ids.mapped('credit_amount_currency'))
    #
    #             line.amount_residual = line.balance - reconciled_balance
    #
    #             if line.currency_id:
    #                 line.amount_residual_currency = line.amount_currency - reconciled_amount_currency
    #             else:
    #                 line.amount_residual_currency = 0.0
    #
    #             line.reconciled = line.company_currency_id.is_zero(line.amount_residual) \
    #                               and (not line.currency_id or line.currency_id.is_zero(line.amount_residual_currency))
    #         else:
    #             # Must not have any reconciliation since the line is not eligible for that.
    #             line.amount_residual = 0.0
    #             line.amount_residual_currency = 0.0
    #             line.reconciled = False

    @api.model_create_multi
    def create(self, vals_list):
        """If we create the invoice with the discounts already set like from
        a sales order, we must compute the global discounts as well"""
        moves = super().create(vals_list)
        # move_with_global_discounts = moves.filtered("global_discount_ids")
        for move in moves:
            move.with_context(check_move_validity=False)._onchange_invoice_line_ids()
        return moves

    # def _construct_values(self, account_id, accountoff_amount):
    #
    #     # [0, 0,
    #     values = ({
    #         'name': 'Discount Amount',
    #         'account_id': account_id,
    #         'quantity': 1,
    #         'price_unit': accountoff_amount,
    #         'display_type': False,
    #         # 'is_roundoff_line': True,
    #         'exclude_from_invoice_tab': False,
    #         # 'is_rounding_line': False,
    #         # 'predict_override_default_account': False,
    #         # 'predict_from_name': False,
    #     })
    #
    #               # ]
    #     return values
    #
    # def discount_value(self):
    #     # OVERRIDE
    #     for i in self:
    #         if 'invoice_line_ids' in i:
    #             account_id = int(self.env['ir.config_parameter'].sudo().get_param("account.sales_discount_account"))
    #             amount_discount = 0.00
    #             if self.env.context.get('active_id') and self.env.context.get('active_model') == 'sale.order':
    #                 sale = self.env['sale.order'].browse(self.env.context.get('active_id'))
    #                 if sale and sale.is_enabled_discount:
    #                     amount_discount = sale.amount_discount
    #                 if amount_discount:
    #                     values = self._construct_values(account_id, amount_discount)
    #                     create_method = self.env['account.move.line'].new or \
    #                                     self.env['account.move.line'].create
    #                     i.invoice_line_ids += create_method(values)
    #                     # i.invoice_line_ids.append(values)
    #             else:
    #                 if i.round_active ==True and i.global_discount_rate:
    #                     # If rounding amount is available, then update the total amount and add the roundoff value as new line.
    #                     account_id = int(self.env['ir.config_parameter'].sudo().get_param("account.sales_discount_account"))
    #                     flag=False
    #                     for record in i.line_ids:
    #                         if record.account_id:
    #                             account = self.env['account.account'].browse(record.account_id.id)
    #                             # Update the values for the sale order
    #                             if account.user_type_id.type in ('Receivable', 'receivable'):
    #                                 if i.amount_discount <0.0:
    #                                     total=abs(record.price_unit) - abs(i.amount_discount)
    #                                 else:
    #                                     total = abs(record.price_unit) + abs(i.amount_discount)
    #                                 record.price_unit=-total
    #                                 record.debit = total
    #                                 flag=True
    #                             # Update the values for the purchase order
    #                             elif account.user_type_id.type in ('Payable', 'payable'):
    #                                 if i.amount_discount < 0.0:
    #                                     total = abs(record.price_unit) - abs(i.amount_discount)
    #                                 else:
    #                                     total = abs(record.price_unit) + abs(i.amount_discount)
    #                                 record.price_unit = -total
    #                                 record.credit = total
    #                                 flag = True
    #                     if flag ==True:
    #                         values = self._construct_values(account_id, i.amount_discount)
    #                         new_tax_line = self.env['account.move.line']
    #                         in_draft_mode = self != self._origin
    #                         create_method = self.env['account.move.line'].new or \
    #                                         self.env['account.move.line'].create
    #                         i.line_ids += create_method(values)
    #                         i.invoice_line_ids += create_method(values)
    #                         # i.line_ids.append(values)
    #                         # i.invoice_line_ids.append(values)
    #         if any(i.state and i.state == 'posted' for i in self):
    #             raise UserError(_('You cannot create a move already in the posted state. Please create a draft move and post it after.'))
    #         # vals_list = self._move_autocomplete_invoice_lines_create(vals_list)
    #     return
    def _recompute_tax_lines(self, recompute_tax_base_amount=False):
        ''' Compute the dynamic tax lines of the journal entry.

        :param lines_map: The line_ids dispatched by type containing:
            * base_lines: The lines having a tax_ids set.
            * tax_lines: The lines having a tax_line_id set.
            * terms_lines: The lines generated by the payment terms of the invoice.
            * rounding_lines: The cash rounding lines of the invoice.
        '''
        self.ensure_one()
        in_draft_mode = self != self._origin

        def _serialize_tax_grouping_key(grouping_dict):
            ''' Serialize the dictionary values to be used in the taxes_map.
            :param grouping_dict: The values returned by '_get_tax_grouping_key_from_tax_line' or '_get_tax_grouping_key_from_base_line'.
            :return: A string representing the values.
            '''
            return '-'.join(str(v) for v in grouping_dict.values())

        def _compute_base_line_taxes(base_line):
            ''' Compute taxes amounts both in company currency / foreign currency as the ratio between
            amount_currency & balance could not be the same as the expected currency rate.
            The 'amount_currency' value will be set on compute_all(...)['taxes'] in multi-currency.
            :param base_line:   The account.move.line owning the taxes.
            :return:            The result of the compute_all method.
            '''
            move = base_line.move_id

            if move.is_invoice(include_receipts=True):
                handle_price_include = True
                sign = -1 if move.is_inbound() else 1
                quantity = base_line.quantity
                is_refund = move.move_type in ('out_refund', 'in_refund')
                price_unit_wo_discount = sign * base_line.price_unit * (1 - (base_line.discount / 100.0))
                if base_line.discount_amount and not base_line.discount:
                    price_unit_wo_discount = sign * (base_line.price_unit - base_line.discount_amount)
            else:
                handle_price_include = False
                quantity = 1.0
                tax_type = base_line.tax_ids[0].type_tax_use if base_line.tax_ids else None
                is_refund = (tax_type == 'sale' and base_line.debit) or (tax_type == 'purchase' and base_line.credit)
                price_unit_wo_discount = base_line.balance

            balance_taxes_res = base_line.tax_ids._origin.compute_all(
                price_unit_wo_discount,
                currency=base_line.currency_id,
                quantity=quantity,
                product=base_line.product_id,
                partner=base_line.partner_id,
                is_refund=is_refund,
                handle_price_include=handle_price_include,
            )

            if move.move_type == 'entry':
                repartition_field = is_refund and 'refund_repartition_line_ids' or 'invoice_repartition_line_ids'
                repartition_tags = base_line.tax_ids.mapped(repartition_field).filtered(
                    lambda x: x.repartition_type == 'base').tag_ids
                tags_need_inversion = (tax_type == 'sale' and not is_refund) or (tax_type == 'purchase' and is_refund)
                if tags_need_inversion:
                    balance_taxes_res['base_tags'] = base_line._revert_signed_tags(repartition_tags).ids
                    for tax_res in balance_taxes_res['taxes']:
                        tax_res['tag_ids'] = base_line._revert_signed_tags(
                            self.env['account.account.tag'].browse(tax_res['tag_ids'])).ids

            return balance_taxes_res

        taxes_map = {}

        # ==== Add tax lines ====
        to_remove = self.env['account.move.line']
        for line in self.line_ids.filtered('tax_repartition_line_id'):
            grouping_dict = self._get_tax_grouping_key_from_tax_line(line)
            grouping_key = _serialize_tax_grouping_key(grouping_dict)
            if grouping_key in taxes_map:
                # A line with the same key does already exist, we only need one
                # to modify it; we have to drop this one.
                to_remove += line
            else:
                taxes_map[grouping_key] = {
                    'tax_line': line,
                    'amount': 0.0,
                    'tax_base_amount': 0.0,
                    'grouping_dict': False,
                }
        self.line_ids -= to_remove

        # ==== Mount base lines ====
        for line in self.line_ids.filtered(lambda line: not line.tax_repartition_line_id):
            # Don't call compute_all if there is no tax.
            if not line.tax_ids:
                line.tax_tag_ids = [(5, 0, 0)]
                continue

            compute_all_vals = _compute_base_line_taxes(line)

            # Assign tags on base line
            line.tax_tag_ids = compute_all_vals['base_tags']

            tax_exigible = True
            for tax_vals in compute_all_vals['taxes']:
                grouping_dict = self._get_tax_grouping_key_from_base_line(line, tax_vals)
                grouping_key = _serialize_tax_grouping_key(grouping_dict)

                tax_repartition_line = self.env['account.tax.repartition.line'].browse(
                    tax_vals['tax_repartition_line_id'])
                tax = tax_repartition_line.invoice_tax_id or tax_repartition_line.refund_tax_id

                if tax.tax_exigibility == 'on_payment':
                    tax_exigible = False

                taxes_map_entry = taxes_map.setdefault(grouping_key, {
                    'tax_line': None,
                    'amount': 0.0,
                    'tax_base_amount': 0.0,
                    'grouping_dict': False,
                })
                taxes_map_entry['amount'] += tax_vals['amount']
                taxes_map_entry['tax_base_amount'] += self._get_base_amount_to_display(tax_vals['base'],
                                                                                       tax_repartition_line)
                taxes_map_entry['grouping_dict'] = grouping_dict
            line.tax_exigible = tax_exigible

        # ==== Process taxes_map ====
        for taxes_map_entry in taxes_map.values():
            # The tax line is no longer used in any base lines, drop it.
            if taxes_map_entry['tax_line'] and not taxes_map_entry['grouping_dict']:
                self.line_ids -= taxes_map_entry['tax_line']
                continue

            currency = self.env['res.currency'].browse(taxes_map_entry['grouping_dict']['currency_id'])

            # Don't create tax lines with zero balance.
            if currency.is_zero(taxes_map_entry['amount']):
                if taxes_map_entry['tax_line']:
                    self.line_ids -= taxes_map_entry['tax_line']
                continue

            # tax_base_amount field is expressed using the company currency.
            tax_base_amount = currency._convert(taxes_map_entry['tax_base_amount'], self.company_currency_id,
                                                self.company_id, self.date or fields.Date.context_today(self))

            # Recompute only the tax_base_amount.
            if taxes_map_entry['tax_line'] and recompute_tax_base_amount:
                taxes_map_entry['tax_line'].tax_base_amount = tax_base_amount
                continue

            balance = currency._convert(
                taxes_map_entry['amount'],
                self.journal_id.company_id.currency_id,
                self.journal_id.company_id,
                self.date or fields.Date.context_today(self),
            )
            to_write_on_line = {
                'amount_currency': taxes_map_entry['amount'],
                'currency_id': taxes_map_entry['grouping_dict']['currency_id'],
                'debit': balance > 0.0 and balance or 0.0,
                'credit': balance < 0.0 and -balance or 0.0,
                'tax_base_amount': tax_base_amount,
            }

            if taxes_map_entry['tax_line']:
                # Update an existing tax line.
                taxes_map_entry['tax_line'].update(to_write_on_line)
            else:
                create_method = in_draft_mode and self.env['account.move.line'].new or self.env[
                    'account.move.line'].create
                tax_repartition_line_id = taxes_map_entry['grouping_dict']['tax_repartition_line_id']
                tax_repartition_line = self.env['account.tax.repartition.line'].browse(tax_repartition_line_id)
                tax = tax_repartition_line.invoice_tax_id or tax_repartition_line.refund_tax_id
                taxes_map_entry['tax_line'] = create_method({
                    **to_write_on_line,
                    'name': tax.name,
                    'move_id': self.id,
                    'partner_id': line.partner_id.id,
                    'company_id': line.company_id.id,
                    'company_currency_id': line.company_currency_id.id,
                    'tax_base_amount': tax_base_amount,
                    'exclude_from_invoice_tab': True,
                    'tax_exigible': tax.tax_exigibility == 'on_invoice',
                    **taxes_map_entry['grouping_dict'],
                })

            if in_draft_mode:
                taxes_map_entry['tax_line'].update(
                    taxes_map_entry['tax_line']._get_fields_onchange_balance(force_computation=True))


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    discount_amount = fields.Float(string="Discount(amt)", digits="Product Price", default=0.0)
    global_discount_item = fields.Boolean()

    # @api.onchange('discount_amount')
    # def onchange_discount_amount(self):
    #     if self.discount_amount:
    #         self.discount = 0.0

    @api.onchange('discount', 'price_unit', 'quantity')
    def onchange_discount_percentage(self):
        for i in self:
            if i.price_unit and i.quantity != 0:
                i.discount_amount = (i.discount * i.price_unit * i.quantity) / 100

    def _get_price_total_and_subtotal(self, price_unit=None, quantity=None, discount=None, currency=None, product=None,
                                      partner=None, taxes=None, move_type=None, discount_amount=None):
        self.ensure_one()
        return self._get_price_total_and_subtotal_model(
            price_unit=price_unit or self.price_unit,
            quantity=quantity or self.quantity,
            discount=discount or self.discount,
            currency=currency or self.currency_id,
            product=product or self.product_id,
            partner=partner or self.partner_id,
            taxes=taxes or self.tax_ids,
            move_type=move_type or self.move_id.move_type,
            discount_amount=discount_amount or self.discount_amount
        )

    @api.model
    def _get_price_total_and_subtotal_model(self, price_unit, quantity, discount, currency, product, partner, taxes,
                                            move_type, discount_amount=None):
        ''' This method is used to compute 'price_total' & 'price_subtotal'.

        :param price_unit:  The current price unit.
        :param quantity:    The current quantity.
        :param discount:    The current discount.
        :param currency:    The line's currency.
        :param product:     The line's product.
        :param partner:     The line's partner.
        :param taxes:       The applied taxes.
        :param move_type:   The type of the move.
        :param discount_amount:    The current discount_amount.
        :return:            A dictionary containing 'price_subtotal' & 'price_total'.
        '''
        res = {}

        # Compute 'price_subtotal'.
        line_discount_price_unit = price_unit * (1 - (discount / 100.0))
        if discount_amount and not discount:
            line_discount_price_unit = price_unit - discount_amount
        subtotal = quantity * line_discount_price_unit

        # Compute 'price_total'.
        if taxes:
            taxes_res = taxes._origin.compute_all(line_discount_price_unit,
                                                  quantity=quantity, currency=currency, product=product,
                                                  partner=partner, is_refund=move_type in ('out_refund', 'in_refund'))
            res['price_subtotal'] = taxes_res['total_excluded']
            res['price_total'] = taxes_res['total_included']
        else:
            res['price_total'] = res['price_subtotal'] = subtotal
        # In case of multi currency, round before it's use for computing debit credit
        if currency:
            res = {k: currency.round(v) for k, v in res.items()}
        return res

    def _get_fields_onchange_balance(self, quantity=None, discount=None, amount_currency=None, move_type=None,
                                     currency=None, taxes=None, price_subtotal=None, force_computation=False, discount_amount=None):
        self.ensure_one()
        return self._get_fields_onchange_balance_model(
            quantity=quantity or self.quantity,
            discount=discount or self.discount,
            amount_currency=amount_currency or self.amount_currency,
            move_type=move_type or self.move_id.move_type,
            currency=currency or self.currency_id or self.move_id.currency_id,
            taxes=taxes or self.tax_ids,
            price_subtotal=price_subtotal or self.price_subtotal,
            force_computation=force_computation,
            discount_amount=discount_amount or self.discount_amount
        )

    @api.model
    def _get_fields_onchange_balance_model(self, quantity, discount, amount_currency, move_type, currency, taxes,
                                           price_subtotal, force_computation=False, discount_amount=None):
        ''' This method is used to recompute the values of 'quantity', 'discount', 'price_unit' due to a change made
        in some accounting fields such as 'balance'.

        This method is a bit complex as we need to handle some special cases.
        For example, setting a positive balance with a 100% discount.

        :param quantity:        The current quantity.
        :param discount:        The current discount.
        :param amount_currency: The new balance in line's currency.
        :param move_type:       The type of the move.
        :param currency:        The currency.
        :param taxes:           The applied taxes.
        :param price_subtotal:  The price_subtotal.
        :param discount_amount: The current discount_amount.
        :return:                A dictionary containing 'quantity', 'discount', 'price_unit'.
        '''
        if move_type in self.move_id.get_outbound_types():
            sign = 1
        elif move_type in self.move_id.get_inbound_types():
            sign = -1
        else:
            sign = 1
        amount_currency *= sign

        # Avoid rounding issue when dealing with price included taxes. For example, when the price_unit is 2300.0 and
        # a 5.5% price included tax is applied on it, a balance of 2300.0 / 1.055 = 2180.094 ~ 2180.09 is computed.
        # However, when triggering the inverse, 2180.09 + (2180.09 * 0.055) = 2180.09 + 119.90 = 2299.99 is computed.
        # To avoid that, set the price_subtotal at the balance if the difference between them looks like a rounding
        # issue.
        if not force_computation and currency.is_zero(amount_currency - price_subtotal):
            return {}

        taxes = taxes.flatten_taxes_hierarchy()
        if taxes and any(tax.price_include for tax in taxes):
            # Inverse taxes. E.g:
            #
            # Price Unit    | Taxes         | Originator Tax    |Price Subtotal     | Price Total
            # -----------------------------------------------------------------------------------
            # 110           | 10% incl, 5%  |                   | 100               | 115
            # 10            |               | 10% incl          | 10                | 10
            # 5             |               | 5%                | 5                 | 5
            #
            # When setting the balance to -200, the expected result is:
            #
            # Price Unit    | Taxes         | Originator Tax    |Price Subtotal     | Price Total
            # -----------------------------------------------------------------------------------
            # 220           | 10% incl, 5%  |                   | 200               | 230
            # 20            |               | 10% incl          | 20                | 20
            # 10            |               | 5%                | 10                | 10
            taxes_res = taxes._origin.compute_all(amount_currency, currency=currency, handle_price_include=False)
            for tax_res in taxes_res['taxes']:
                tax = self.env['account.tax'].browse(tax_res['id'])
                if tax.price_include:
                    amount_currency += tax_res['amount']

        discount_factor = 1 - (discount / 100.0)
        if discount_amount and not discount:
            discount_factor = discount_amount
        if amount_currency and discount_factor:
            # discount != 100%
            vals = {
                'quantity': quantity or 1.0,
                'price_unit': amount_currency /(quantity or 1.0) + discount_factor if  discount_amount and not discount else amount_currency / discount_factor / (quantity or 1.0),
            }
        elif amount_currency and not discount_factor:
            # discount == 100%
            vals = {
                'quantity': quantity or 1.0,
                'discount': 0.0,
                'discount_amount': 0.0,
                'price_unit': amount_currency / (quantity or 1.0),
            }
        elif not discount_factor:
            # balance of line is 0, but discount  == 100% so we display the normal unit_price
            vals = {}
        else:
            # balance is 0, so unit price is 0 as well
            vals = {'price_unit': 0.0}
        return vals

    @api.onchange('quantity', 'discount', 'price_unit', 'tax_ids', 'discount_amount')
    def _onchange_price_subtotal(self):
        discount_amt_line = self.filtered(
            lambda p: p.discount_amount and not p.discount)
        discount_per_line = self - discount_amt_line
        if discount_per_line:
            super(AccountMoveLine, discount_per_line)._onchange_price_subtotal()
        for line in discount_amt_line:
            if not line.move_id.is_invoice(include_receipts=True):
                continue

            line.update(line._get_price_total_and_subtotal())
            line.update(line._get_fields_onchange_subtotal())


    @api.model_create_multi
    def create(self, vals_list):
        # OVERRIDE
        prev_price_unit = []
        for vals in vals_list:
            if vals.get("discount_amount") and not vals.get("discount"):
                prev_price_unit.append(
                    {"price_unit": vals.get("price_unit")}
                )
        res = super(AccountMoveLine, self).create(vals_list)
        i = 0
        for rec in res:
            if rec.discount_amount and not rec.discount and prev_price_unit:
                rec.write(prev_price_unit[i])
                i += 1
        return res
        # ACCOUNTING_FIELDS = ('debit', 'credit', 'amount_currency')
        # BUSINESS_FIELDS = ('price_unit', 'quantity', 'discount', 'discount_amount', 'tax_ids')
        # list_of_vals = vals_list
        # lines = super(AccountMoveLine, self).create(vals_list)
        # to_process_invoice_lines = lines.filtered(lambda line: line.move_id.move_type == 'out_invoice' and line.exclude_from_invoice_tab is False)
        # if not to_process_invoice_lines:
        #     return lines
        # for line in to_process_invoice_lines:
        #     s=0
        #
        #
        # for vals in vals_list:
        #     move = self.env['account.move'].browse(vals['move_id'])
        #     vals.setdefault('company_currency_id',
        #                     move.company_id.currency_id.id)  # important to bypass the ORM limitation where monetary fields are not rounded; more info in the commit message
        #
        #     # Ensure balance == amount_currency in case of missing currency or same currency as the one from the
        #     # company.
        #     currency_id = vals.get('currency_id') or move.company_id.currency_id.id
        #     if currency_id == move.company_id.currency_id.id:
        #         balance = vals.get('debit', 0.0) - vals.get('credit', 0.0)
        #         vals.update({
        #             'currency_id': currency_id,
        #             'amount_currency': balance,
        #         })
        #     else:
        #         vals['amount_currency'] = vals.get('amount_currency', 0.0)
        #
        #     if move.is_invoice(include_receipts=True):
        #         currency = move.currency_id
        #         partner = self.env['res.partner'].browse(vals.get('partner_id'))
        #         taxes = self.new({'tax_ids': vals.get('tax_ids', [])}).tax_ids
        #         tax_ids = set(taxes.ids)
        #         taxes = self.env['account.tax'].browse(tax_ids)
        #
        #         # Ensure consistency between accounting & business fields.
        #         # As we can't express such synchronization as computed fields without cycling, we need to do it both
        #         # in onchange and in create/write. So, if something changed in accounting [resp. business] fields,
        #         # business [resp. accounting] fields are recomputed.
        #         if any(vals.get(field) for field in ACCOUNTING_FIELDS):
        #             price_subtotal = self._get_price_total_and_subtotal_model(
        #                 vals.get('price_unit', 0.0),
        #                 vals.get('quantity', 0.0),
        #                 vals.get('discount', 0.0),
        #                 currency,
        #                 self.env['product.product'].browse(vals.get('product_id')),
        #                 partner,
        #                 taxes,
        #                 move.move_type,
        #                 vals.get('discount_amount', 0.0)
        #             ).get('price_subtotal', 0.0)
        #             vals.update(self._get_fields_onchange_balance_model(
        #                 vals.get('quantity', 0.0),
        #                 vals.get('discount', 0.0),
        #                 vals['amount_currency'],
        #                 move.move_type,
        #                 currency,
        #                 taxes,
        #                 price_subtotal,
        #                 discount_amount=vals.get('discount_amount', 0.0)
        #             ))
        #             vals.update(self._get_price_total_and_subtotal_model(
        #                 vals.get('price_unit', 0.0),
        #                 vals.get('quantity', 0.0),
        #                 vals.get('discount', 0.0),
        #                 currency,
        #                 self.env['product.product'].browse(vals.get('product_id')),
        #                 partner,
        #                 taxes,
        #                 move.move_type,
        #                 vals.get('discount_amount', 0.0)
        #             ))
        #         elif any(vals.get(field) for field in BUSINESS_FIELDS):
        #             vals.update(self._get_price_total_and_subtotal_model(
        #                 vals.get('price_unit', 0.0),
        #                 vals.get('quantity', 0.0),
        #                 vals.get('discount', 0.0),
        #                 currency,
        #                 self.env['product.product'].browse(vals.get('product_id')),
        #                 partner,
        #                 taxes,
        #                 move.move_type,
        #                 vals.get('discount_amount', 0.0)
        #             ))
        #             vals.update(self._get_fields_onchange_subtotal_model(
        #                 vals['price_subtotal'],
        #                 move.move_type,
        #                 currency,
        #                 move.company_id,
        #                 move.date,
        #             ))
        #
        #
        #
        # moves = lines.mapped('move_id')
        # if self._context.get('check_move_validity', True):
        #     moves._check_balanced()
        # moves._check_fiscalyear_lock_date()
        # lines._check_tax_lock_date()
        # moves._synchronize_business_models({'line_ids'})
        #
        # return lines




