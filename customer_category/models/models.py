# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CustomerCategory(models.Model):
    _name = 'customer.category'
    _description = 'Customer Category'

    name = fields.Char(string="Name")


class Partner(models.Model):
    _inherit = 'res.partner'

    customer_category_id = fields.Many2one('customer.category', string='Customer Category')

