# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date


class StockFlowReport(models.TransientModel):
    _name = "stock.flow.report"
    _description = "Stock Flow Report"

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company,required=True)
    date_from = fields.Date(string='Start Date',required=True,default=date.today(),)
    date_to = fields.Date(string='End Date',required=True,default=date.today(),)
    product_id = fields.Many2one('product.product',string="Product")
    category_id = fields.Many2one('product.category', 'Product Category')
    brand_id = fields.Many2one('product.brand', string='Brand')




    def check_report(self):

        self.ensure_one()
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        # datas['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        datas['model'] = 'account.move'
        datas['form'] = self.read()[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]

        return self.env.ref('stock_flow_report.action_report_stock_flow_report').report_action(self, data=datas)


    def export_xls(self):
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        # datas['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        datas['model'] = 'account.move'
        datas['form'] = self.read()[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]

        return self.env.ref('stock_flow_report.action_stock_flow_report').report_action(self, data=datas)
