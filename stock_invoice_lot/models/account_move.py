# Copyright 2013-15 Agile Business Group sagl (<http://www.agilebg.com>)
# Copyright 2015-2016 AvanzOSC
# Copyright 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# Copyright 2017 Jacques-Etienne Baudoux <je@bcim.be>
# Copyright 2020 Manuel Calero - Tecnativa
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models
from collections import defaultdict


class AccountMove(models.Model):
    _inherit = "account.move"

    picking_ids = fields.Many2many(
        comodel_name="stock.picking",
        string="Related Pickings",
        store=True,
        compute="_compute_picking_ids",
        help="Related pickings "
        "(only when the invoice has been generated from a sale order).",
    )

    @api.depends("invoice_line_ids", "invoice_line_ids.move_line_ids")
    def _compute_picking_ids(self):
        for invoice in self:
            invoice.picking_ids = invoice.mapped(
                "invoice_line_ids.move_line_ids.picking_id"
            )

    def action_show_picking(self):
        """This function returns an action that display existing pickings
        of given invoice.
        It can either be a in a list or in a form view, if there is only
        one picking to show.
        """
        self.ensure_one()
        form_view_name = "stock.view_picking_form"
        action = self.env.ref("stock.action_picking_tree_all")
        result = action.read()[0]
        if len(self.picking_ids) > 1:
            result["domain"] = "[('id', 'in', %s)]" % self.picking_ids.ids
        else:
            form_view = self.env.ref(form_view_name)
            result["views"] = [(form_view.id, "form")]
            result["res_id"] = self.picking_ids.id
        return result


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    move_line_ids = fields.Many2many(
        comodel_name="stock.move",
        relation="stock_move_invoice_line_rel",
        column1="invoice_line_id",
        column2="move_id",
        string="Related Stock Moves",
        readonly=True,
        help="Related stock moves "
        "(only when the invoice has been generated from a sale order).",
    )

    prod_lot_ids = fields.Many2many(
        comodel_name="stock.production.lot",
        compute="_compute_prod_lots",
        string="Production Lots",
    )

    @api.depends("move_line_ids")
    def _compute_prod_lots(self):
        for line in self:
            line.prod_lot_ids = line.mapped("move_line_ids.move_line_ids.lot_id")

    def lots_grouped_by_quantity(self):
        lot_dict = defaultdict(float)
        for sml in self.mapped("move_line_ids.move_line_ids"):
            lot_dict[sml.lot_id.name] += sml.qty_done
            # lot_dict['expire_date'] =','.join(
            #         map(str, [picking.expiry_date.strftime('%d%m%Y') for picking in sml if picking.expiry_date]))
        return lot_dict

    # @api.depends("invoice_line_ids", "invoice_line_ids.move_line_ids")
    # def _compute_picking_ids(self):
    #     for invoice in self:
    #         invoice.picking_ids = invoice.mapped(
    #             "invoice_line_ids.move_line_ids.picking_id"
    #         )
    #         if invoice.picking_ids:
    #             invoice.del_number = ','.join(
    #                 map(str, [i.name for picking in invoice.picking_ids for i in picking if i.name]))
    #             # ', '.join(invoice.picking_ids.mapped('name'))
    #             # invoice.del_date = ','.join(map(str, [i.scheduled_date for picking in invoice.picking_ids for i in picking if i.scheduled_date]))
    #             # ', '.join(invoice.picking_ids.mapped('scheduled_date'))
    #             invoice.cpo_reference = ','.join(
    #                 map(str, [i.cpo_reference for picking in invoice.picking_ids for i in picking if i.cpo_reference]))
    #             # ', '.join(invoice.picking_ids.mapped('cpo_reference'))
    #             # invoice.cpo_date = ','.join(map(str, [i.cpo_date for picking in invoice.picking_ids for i in picking if i.cpo_date]))
    #             # ','.join(map(str, invoice.picking_ids.mapped('cpo_date')))
    #             # ', '.join(invoice.picking_ids.mapped('cpo_date'))
