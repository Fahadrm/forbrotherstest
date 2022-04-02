# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
import re

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression


from odoo import models, fields, api


class Customercode(models.Model):
    _name = 'customer.code'
    _description = 'Customer Code'

    name = fields.Char()
    partner_id = fields.Many2one('res.partner', 'Customer',)


class Locationcode(models.Model):
    _name = 'location.code'
    _description = 'Locations'

    name = fields.Char()
    product_id = fields.Many2one('product.product', 'Product', )





class CustomerInfo(models.Model):
    _name = "product.customerinfo"
    _inherit = "product.supplierinfo"
    _description = "Customer Pricelist"
    _order = 'id'

    name = fields.Many2one(
        'res.partner', 'Customer',
        ondelete='cascade', required=True,
        help="Customer of this product", check_company=True)
    product_name = fields.Char(
        'Customer Product Name',
        help="This Customer's product name will be used when printing a request for quotation. Keep empty to use the internal one.")
    product_code = fields.Many2one('customer.code', 'Customer Code', ondelete='set null')

    company_id = fields.Many2one(
        'res.company', 'Company',
        default=lambda self: self.env.company.id, index=1)
    currency_id = fields.Many2one(
        'res.currency', 'Currency',
        default=lambda self: self.env.company.currency_id.id,
        required=True)
    product_id = fields.Many2one(
        'product.product', 'Product Variant', check_company=True,
        help="If not set, the vendor price will apply to all variants of this product.")
    product_tmpl_id = fields.Many2one(
        'product.template', 'Product Template', check_company=True,
        index=True, ondelete='cascade')


class ProductTemplate(models.Model):
    _inherit = "product.template"


    customer_ids = fields.One2many('product.customerinfo', 'product_tmpl_id', 'Vendors', depends_context=('company',),)
    product_location_ids = fields.Many2one('location.code',string="Location")

class ProductProduct(models.Model):
    _inherit = "product.product"

    def name_get(self):
        """
            Add GSTIN number in name as suffix so user can easily find the right journal.
            Used super to ensure nothing is missed.
        """
        result = super().name_get()
        result_dict = dict(result)
        partner_id = self._context.get('partner_id')
        if partner_id:
            partner_ids = [partner_id, self.env['res.partner'].browse(partner_id).commercial_partner_id.id]
        else:
            partner_ids = []
        product_template_ids = self.sudo().mapped('product_tmpl_id').ids
        supplier_info = self.env['product.supplierinfo'].sudo().search([
            ('product_tmpl_id', 'in', product_template_ids),
            ('name', 'in', partner_ids),
        ])
        indian_journals = self.filtered(lambda j: j.company_id.country_id.code == 'IN' and
            j.l10n_in_gstin_partner_id and j.l10n_in_gstin_partner_id.vat)
        for journal in indian_journals:
            name = result_dict[journal.id]
            name += "- %s" % (journal.l10n_in_gstin_partner_id.vat)
            result_dict[journal.id] = name
        return list(result_dict.items())


    def name_get(self):
        res = super(ProductProduct, self.with_context(customerinfo=True)).name_get()
        return res

    @api.model
    def _name_search(
            self, name="", args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        res = super(ProductProduct, self)._name_search(
            name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid
        )
        res_ids = list(res)
        res_ids_len = len(res_ids)
        if not limit or res_ids_len >= limit:
            limit = (limit - res_ids_len) if limit else False
        if (
                not name
                and limit
                or not self._context.get("partner_id")
                or res_ids_len >= limit
        ):
            return res_ids
        limit -= res_ids_len
        customerinfo_ids = self.env["product.customerinfo"]._search(
            [
                ("name", "=", self._context.get("partner_id")),
                "|",
                ("product_code.name", operator, name),
                ("product_name", operator, name),
            ],
            limit=limit,
            access_rights_uid=name_get_uid,
        )
        if not customerinfo_ids:
            return res_ids
        res_templates = self.browse(res_ids).mapped("product_tmpl_id")
        product_tmpls = (
                self.env["product.customerinfo"]
                .browse(customerinfo_ids)
                .mapped("product_tmpl_id")
                - res_templates
        )
        product_ids = list(
            self._search(
                [("product_tmpl_id", "in", product_tmpls.ids)],
                limit=limit,
                access_rights_uid=name_get_uid,
            )
        )
        res_ids.extend(product_ids)
        return res_ids

    # def _prepare_domain_customerinfo(self, params):
    #     self.ensure_one()
    #     partner_id = params.get("partner_id")
    #     return [
    #         ("name", "=", partner_id),
    #         "|",
    #         ("product_id", "=", self.id),
    #         "&",
    #         ("product_tmpl_id", "=", self.product_tmpl_id.id),
    #         ("product_id", "=", False),
    #     ]
    #
    # def _select_customerinfo(
    #         self, partner=False, _quantity=0.0, _date=None, _uom_id=False, params=False
    # ):
    #     """Customer version of the standard `_select_seller`. """
    #     # TODO: For now it is just the function name with same arguments, but
    #     #  can be changed in future migrations to be more in line Odoo
    #     #  standard way to select supplierinfo's.
    #     if not params:
    #         params = dict()
    #     params.update({"partner_id": partner.id})
    #     domain = self._prepare_domain_customerinfo(params)
    #     res = self.env["product.customerinfo"].search(
    #         domain, order="product_id, sequence", limit=1
    #     )
    #     return res