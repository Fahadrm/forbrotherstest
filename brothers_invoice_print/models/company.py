from odoo import api, fields, models

class Company(models.Model):

    _inherit = "res.company"

    customer_care = fields.Char(string="Customer Care")
    whatsapp = fields.Char(string="WhatsApp")

