
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
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

    round_active = fields.Boolean('Enabled Discount',
                                  default=lambda self: self.env["ir.config_parameter"].sudo().get_param(
                                      "account.enable_discount"))

    total_discount = fields.Monetary(string='Total Discount', readonly=True, compute='_compute_total_discount',
                                     store=True,
                                     track_visibility='always')
    amount_undiscounted = fields.Float('Amount Before Discount', compute='_compute_amount_undiscounted', digits=0)

    def _compute_amount_undiscounted(self):
        for invoice in self:
            total = 0.0
            for line in invoice.invoice_line_ids:
                line_discount = line.price_unit * ((line.discount or 0.0) / 100.0) * line.quantity
                if line.discount_amount and not line.discount:
                    line_discount = line.discount_amount * line.quantity
                total += line.price_subtotal + line_discount
            invoice.amount_undiscounted = total

    @api.depends('invoice_line_ids.discount', 'invoice_line_ids.discount_amount', 'amount_discount')
    def _compute_total_discount(self):
        for invoice in self:
            total_discount = 0.0
            for line in invoice.invoice_line_ids:
                total_discount += (line.discount_amount * line.quantity) + (
                            (line.price_unit * line.discount * line.quantity) / 100)
            total_discount += invoice.amount_discount
            invoice.update({
                'total_discount': total_discount,
            })

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

    @api.model_create_multi
    def create(self, vals_list):
        """If we create the invoice with the discounts already set like from
        a sales order, we must compute the global discounts as well"""
        moves = super().create(vals_list)
        # move_with_global_discounts = moves.filtered("global_discount_ids")
        for move in moves:
            move.with_context(check_move_validity=False)._onchange_invoice_line_ids()
        return moves

    def _recompute_tax_lines(self, recompute_tax_base_amount=False):
        vals = {}
        for line in self.invoice_line_ids.filtered("discount_amount"):
            vals[line] = {"price_unit": line.price_unit}
            price_unit = line.price_unit - line.discount_amount
            line.update({"price_unit": price_unit})
        res = super(AccountMove, self)._recompute_tax_lines(
            recompute_tax_base_amount=recompute_tax_base_amount
        )
        for line in vals.keys():
            line.update(vals[line])
        return res


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    discount_amount = fields.Float(
        string="Discount (Fixed)",
        digits="Product Price",
        default=0.00,
        help="Fixed amount discount.",
    )
    global_discount_item = fields.Boolean()

    @api.onchange("discount")
    def _onchange_discount(self):
        if self.discount:
            self.discount_amount = 0.0

    @api.onchange("discount_amount")
    def _onchange_discount_amount(self):
        if self.discount_amount:
            self.discount = 0.0

    @api.constrains("discount", "discount_amount")
    def _check_only_one_discount(self):
        for rec in self:
            for line in rec:
                if line.discount and line.discount_amount:
                    raise ValidationError(
                        _("You can only set one type of discount per line.")
                    )

    @api.onchange("quantity", "discount", "price_unit", "tax_ids", "discount_amount")
    def _onchange_price_subtotal(self):
        return super(AccountMoveLine, self)._onchange_price_subtotal()

    @api.model
    def _get_price_total_and_subtotal_model(
        self,
        price_unit,
        quantity,
        discount,
        currency,
        product,
        partner,
        taxes,
        move_type,
    ):
        if self.discount_amount != 0:
            discount = ((self.discount_amount) / price_unit) * 100 or 0.00
        return super(AccountMoveLine, self)._get_price_total_and_subtotal_model(
            price_unit, quantity, discount, currency, product, partner, taxes, move_type
        )

    @api.model
    def _get_fields_onchange_balance_model(
        self,
        quantity,
        discount,
        amount_currency,
        move_type,
        currency,
        taxes,
        price_subtotal,
        force_computation=False,
    ):
        if self.discount_amount != 0:
            discount = ((self.discount_amount) / self.price_unit) * 100 or 0.00
        return super(AccountMoveLine, self)._get_fields_onchange_balance_model(
            quantity,
            discount,
            amount_currency,
            move_type,
            currency,
            taxes,
            price_subtotal,
            force_computation=force_computation,
        )

    @api.model_create_multi
    def create(self, vals_list):
        prev_discount = []
        for vals in vals_list:
            if vals.get("discount_amount"):
                prev_discount.append(
                    {"discount_amount": vals.get("discount_amount"), "discount": 0.00}
                )
                fixed_discount = (
                    vals.get("discount_amount") / vals.get("price_unit")
                ) * 100
                vals.update({"discount": fixed_discount, "discount_amount": 0.00})
            elif vals.get("discount"):
                prev_discount.append({"discount": vals.get("discount")})
        res = super(AccountMoveLine, self).create(vals_list)
        i = 0
        for rec in res:
            if rec.discount and prev_discount:
                rec.write(prev_discount[i])
                i += 1
        return res
