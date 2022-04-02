# -*- coding: utf-8 -*-
# from odoo import http


# class UserWeekActivity(http.Controller):
#     @http.route('/user_week_activity/user_week_activity/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/user_week_activity/user_week_activity/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('user_week_activity.listing', {
#             'root': '/user_week_activity/user_week_activity',
#             'objects': http.request.env['user_week_activity.user_week_activity'].search([]),
#         })

#     @http.route('/user_week_activity/user_week_activity/objects/<model("user_week_activity.user_week_activity"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('user_week_activity.object', {
#             'object': obj
#         })
