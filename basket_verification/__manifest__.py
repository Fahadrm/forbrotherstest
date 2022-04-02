# -*- coding: utf-8 -*-
{
    'name': "Basket verification",

    'summary': """
        Basket verification""",

    'description': """
         1.create basket
        2.assign basket to stock
        3.set the basket free with verification
    """,

    'author': "Loyal IT Solutions Pvt Ltd",
    'website': "http://www.loyalitsolutions.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','stock','stock_barcode'],
    'qweb': [
        "static/src/xml/qweb_templates.xml",
    ],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/basket.xml',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
