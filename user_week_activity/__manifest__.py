# -*- coding: utf-8 -*-
{
    'name': "user_week_activity",

    'summary': """
       user scheduled activity""",

    'description': """
       user scheduled activity
    """,

    'author': "Loyal IT Solutions PVT LTD",
    'website': "http://www.loyalitsolutions.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','mail','sale'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/week.xml',
        'views/views.xml',
        'views/templates.xml',
        'data/data.xml'
    ],

    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
