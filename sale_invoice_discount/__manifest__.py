# -*- coding: utf-8 -*-
{
    'name': "Discounts on Sale Order and Invoice",

    'summary': """
        Discount
        1.Discount amount in sale order line and global discount(both percentage and fixed) in sale order. 
        2.Discount amount in account invoice and bill lines and global discount (both percentage and fixed) in invoice and bill.
        """,

    'description': """
        Discount
        1.Discount amount in sale order line and global discount(both percentage and fixed) in sale order. 
        2.Discount amount in account invoice and bill lines and global discount (both percentage and fixed) in invoice and bill.
       
    """,

    'author': "Loyal IT Solutions Pvt Ltd",
    'website': "http://www.loyalitsolutions.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '14.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'account'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/sale.xml',
        'views/account.xml',


    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
