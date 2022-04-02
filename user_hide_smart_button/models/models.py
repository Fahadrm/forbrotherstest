# -*- coding: utf-8 -*-

from odoo import models, fields, api

# class Website(models.Model):
#     _inherit = 'product.template'
#
#
#     def user_access(self):
#         website_user = self.env.user.has_group('website.group_website_designer')
#         users = self.env.uid
#         flag=False
#         # user_document = self.env['res.users'].browse(users)
#
#         if website_user:
#             flag = True
#         else:
#             flag = False
#         return flag
