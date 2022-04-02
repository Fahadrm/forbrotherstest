# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)

class StockBasket(models.Model):
    _name = 'stock.basket'
    _description = 'Basket'

    name = fields.Char(string="Basket")
    picking_id = fields.Many2one('stock.picking',string="Current Picking")
    status = fields.Selection([
        ('vacant', 'Vacant'),
        ('occupy', 'Occupy'),
    ], default="vacant", store=True, )



    @api.constrains('name')
    def _check_unique_name(self):
        for line in self:
            if line.name:
                if len(self.search([('name', '=', line.name)])) > 1:
                    raise ValidationError("Name Already Exists")
            else:
                pass

class stockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    basket_id = fields.Many2one('stock.basket',string='Basket')
    basket_verified = fields.Boolean(string="Basket verified")
class StockPicking(models.Model):
    _inherit = "stock.picking"

    # @api.depends('basket_ids')
    # def _get_verification_done(self):
    #     for res in self:
    #         if len(res.basket_ids) ==0:
    #             self.basket_verification_done = True
    #         else:
    #             self.basket_verification_done = False
    basket_ids = fields.Many2many(comodel_name="stock.basket",string="Basket", compute="_get_basket_ids")
    # basket_ids = fields.One2many("stock.basket","picking_id",string="Basket")
    # stock_basket_id = fields.One2many("stock.basket.lines", "stock_basket_line_id", string="Basket")
    # basket_verification_done = fields.Boolean(string="Basket verification done",compute='_get_verification_done')
    def _get_basket_ids(self):
        for res in self:
            basket_ids = []
            for line in res.move_line_ids_without_package:
                basket_ids.append(line.basket_id.id)
            res.basket_ids = basket_ids
    @api.model
    def _get_move_line_ids_fields_to_read(self):
        """ read() on picking.move_line_ids only returns the id and the display
        name however a lot more data from stock.move.line are used by the client
        action.
        """
        res = super(StockPicking, self)._get_move_line_ids_fields_to_read()
        res.append('basket_id')
        return res
    # def write(self, vals):
    #     res = super(StockPicking, self).write(vals)
    #     for change in self.basket_ids:
    #         if change.name:
    #             basket = change.id
    #             customer_group = self.env['stock.basket'].browse(basket).write(
    #                 {
    #                     'status': 'occupy'
    #                 }
    #             )
    #             change.status ='occupy'
    #     return res
    def set_basket_status(self,basket):
        basket_id = self.env['stock.basket'].search([('name','=',basket)]).write({'status':'occupy'})
        _logger.info('basket_id after write %s',basket_id)
        if basket_id:
            return {'status':True,'result':'Basket successfully allocated'}
        return {'status':False,'result':'Something happened while allocating the basket'}
    def set_basket(self,move_line_id,basket=None):
        _logger.info('inside set basekt  function')
        _logger.info('move_line_id %s',move_line_id)
        _logger.info('basket %s',basket)

        # print('move_line_id',move_line_id)
        # print('basket',basket)
        basket_id = self.env['stock.basket'].search([('name','=',basket)])
        _logger.info('basket_id %s',basket_id)
        # picking_id = self.env['stock.picking'].browse([picking_id])
        # print('move_line_id',move_line_id)
        move_line_id = self.env['stock.move.line'].browse([move_line_id])
        _logger.info('move_line_id %s',move_line_id)
        result = {'status':False,'result':'Something wrong with basket code'}
        # print('move_line_id',move_line_id)
        # if basket_id and picking_id:
        if basket_id:
            _logger.info('inside basket if')
            if move_line_id:
                _logger.info('inside moveline if')
                # basket_alread_added = picking_id.basket_ids.filtered(lambda x: x.name == basket)
                # if basket_alread_added:
                #     result = {'status':False,'result':'Basket already added to this picking'}
                #     return result
                if basket_id.status == 'occupy':
                    return {'status':False,'result':'Basket is already occupied.'}
                elif basket_id.picking_id and basket_id.picking_id.id != move_line_id.picking_id.id:
                    return {'status':False,'result':'This basket is already assigned to another pikcing '+ basket_id.picking_id.name+'.'}
                # vals = {'name':basket,'status':'occupy'}
                # basket_id.write({'status':'occupy','picking_id':picking_id.id})
                else:
                    move_line_id.write({'basket_id':basket_id.id})
                    basket_id.write({'picking_id':move_line_id.picking_id.id})
                    _logger.info('after move line write')
                    # basket_id.write({'status':'occupy','picking_id':picking_id.id})
                    # write = picking_id.write({'basket_ids':[(4,basket_id.id)],})
                    result = {'status':True,'result':'Basket successfully added'}
                    _logger.info('before return result')
                    return result

            else:
                _logger.info('inside else of move line id')
                result = {'status':False,'result':'There is no moveline found.'}
                return result
        else:
            _logger.info('inside else ofbasket_id')

            return {'status':False,'result':'No basket found.'}
        return result
# class StockBasketLines(models.Model):
#     _name = 'stock.basket.lines'
#     _description = 'Basket'
#
#     stock_basket_line_id = fields.Many2one("stock.basket",string="Basket")
