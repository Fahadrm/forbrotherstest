from odoo import api, fields, models
from odoo import models
from odoo.tools import float_compare


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def _prepare_account_move_line(self, move=False):
        vals = super()._prepare_account_move_line(move)
        all_mrp=""
        if self.move_ids:
            all_mrp = ','.join(
                map(str, [mrp.name for moves in self.move_ids for move_line in moves.move_line_ids if moves.move_line_ids for mrp in move_line.product_mrp if move_line.product_mrp]))

        vals.update({'stock_mrps': all_mrp})
        return vals



class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    stock_mrps = fields.Char('MRP')

