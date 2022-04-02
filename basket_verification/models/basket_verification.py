# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import UserError, ValidationError
class BasketVerification(models.TransientModel):
    _name = 'basket.verification'
    _description = 'Basket Verification'

    name = fields.Many2one("stock.basket", string="Basket")
    picking_id = fields.Many2one('stock.picking',string='Picking')
    partner_id = fields.Many2one('res.partner',related="picking_id.partner_id", string='Customer')
    move_line_ids_without_package = fields.Many2many('stock.move.line',string="Detailed Operations")



    @api.onchange('name')
    def onchange_name(self):
        for res in self:
            basket_id = self.env['stock.basket'].search([('name','=',res.name.id),('status','=','occupy')])
            res.picking_id = basket_id.picking_id.id
            res.move_line_ids_without_package = basket_id.picking_id.move_line_ids_without_package.ids

    def set_basket_free(self):
        for baskets in self:
            basket_id = self.env['stock.basket'].search([('name','=',baskets.name.id),('status','=','occupy')])
            picking_id = basket_id.picking_id
            if basket_id:
                remove_basket = picking_id.write({'basket_ids':[(3,basket_id.id)]})
                baskets.name.write({'status': 'vacant',
                                    'picking_id':None})
                baskets.name = None
            else:
                raise UserError(_('The selected basket han not yet allocated.'))
                baskets.name = None
        return {
    'name': 'Basket Verification',
    'view_mode': 'form',
    'view_id': False,
    'res_model': self._name,
    'domain': [],
    'context': dict(self._context, active_ids=self.ids),
    'type': 'ir.actions.act_window',
    'target': 'new',
    'res_id': self.id,
}
