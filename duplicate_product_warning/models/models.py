# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import Warning,ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

  

    @api.onchange('order_line')
    def onchange_product_in_line(self):
        for sale in self:
            exist_product_list = []
            for line in sale.order_line:
                if line.product_id.id in exist_product_list:
                    message = {
                             'title': _('Duplication!'),
                             'message': _('Product should be one per line.')
                         }
                    return {'warning': message}
                         # raise (_('Product should be one per line.'))
                exist_product_list.append(line.product_id.id)


