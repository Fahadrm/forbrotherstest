# -*- coding: utf-8 -*-
# from odoo import http


# class KanbanMobileView(http.Controller):
#     @http.route('/kanban_mobile_view/kanban_mobile_view/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/kanban_mobile_view/kanban_mobile_view/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('kanban_mobile_view.listing', {
#             'root': '/kanban_mobile_view/kanban_mobile_view',
#             'objects': http.request.env['kanban_mobile_view.kanban_mobile_view'].search([]),
#         })

#     @http.route('/kanban_mobile_view/kanban_mobile_view/objects/<model("kanban_mobile_view.kanban_mobile_view"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('kanban_mobile_view.object', {
#             'object': obj
#         })
