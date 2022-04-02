# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
import datetime
from datetime import datetime


class WeekDays(models.Model):
    _name = 'week.days'

    name = fields.Char(string="Week")

class deliverWeekDays(models.Model):
    _name = 'deliver.week.days'

    name = fields.Char(string="Week")

class Partner(models.Model):
    _inherit = 'res.partner'
    # _inherit = ['res.partner','mail.thread']


    week_days = fields.Many2many('week.days',string='Visit')
    delivery_week_days = fields.Many2many('deliver.week.days', string='Delivery')


    # week_days = fields.Selection(
    #     [
    #         ('Saturday', 'Saturday'),
    #         ('Sunday', 'Sunday'),
    #         ('Monday', 'Monday'),
    #         ('Tuesday', 'Tuesday'),
    #         ('Wednesday', 'Wednesday'),
    #         ('Thursday', 'Thursday'),
    #         ('Friday', 'Friday')
    #     ],
    #     string='Week',
    #     help="""
    #         chhose week days.
    #         """
    # )

# class Resusers(models.Model):
#     _inherit = 'res.users'

    def process_week_days(self):
        s = datetime.today().strftime('%A')
        mail=[]
        delete_thread = self.env['mail.thread'].browse(tuple(mail))
        delete_thread.unlink()
        partners = self.env['res.partner'].search([])
        for i in partners:
            final_user_ids = i.week_days.mapped("name")
            deliver_user_ids = i.delivery_week_days.mapped("name")
            if s in final_user_ids:
                # product_user = self.env['res.users'].search([('id', 'in', literal_eval(users_from_settings))])
                notification_ids = []
                for purchase in i.user_id:
                    notification_ids.append((0, 0, {
                        'res_partner_id': purchase.partner_id.id,
                        'notification_type': 'inbox'}))

                # thread_pool = self.env['mail.thread']
                i.message_post(body=_("Meeting Scheduled with <br> customer name: %s ") % (i.name),
                                       message_type='notification',
                                       subtype_xmlid='mail.mt_comment',
                                       # author_id='self.env.user.partner_id.id',
                                       notification_ids=notification_ids)

            if s in deliver_user_ids:
                notification_ids = []
                for purchase in i.user_id:
                    notification_ids.append((0, 0, {
                            'res_partner_id': purchase.partner_id.id,
                            'notification_type': 'inbox'}))

                i.message_post(body=_("%s has to Deliver today ") % (i.name),
                                   message_type='notification',
                                   subtype_xmlid='mail.mt_comment',
                                   # author_id='self.env.user.partner_id.id',
                                   notification_ids=notification_ids)

        return
