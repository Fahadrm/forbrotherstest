# -*- coding: utf-8 -*-
# from odoo import http


# class UserHideSmartButton(http.Controller):
#     @http.route('/user_hide_smart_button/user_hide_smart_button/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/user_hide_smart_button/user_hide_smart_button/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('user_hide_smart_button.listing', {
#             'root': '/user_hide_smart_button/user_hide_smart_button',
#             'objects': http.request.env['user_hide_smart_button.user_hide_smart_button'].search([]),
#         })

#     @http.route('/user_hide_smart_button/user_hide_smart_button/objects/<model("user_hide_smart_button.user_hide_smart_button"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('user_hide_smart_button.object', {
#             'object': obj
#         })
