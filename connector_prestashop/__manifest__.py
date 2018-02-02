# -*- coding: utf-8 -*-
# Copyright 2011-2013 Camptocamp
# Copyright 2011-2013 Akretion
# Copyright 2015 AvanzOSC
# Copyright 2015-2016 Tecnativa
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "PrestaShop-Odoo connector",
    "version": "11.0.1.0.0",
    "license": "AGPL-3",
    "depends": [
        "account",
        "product",
        "product_multi_category",
        "connector_base_product",
        "purchase",
        "sale",
        "delivery",
    ],
    "external_dependencies": {
        'python': [
            "prestapyt",
        ],
    },
    "author": "Akretion,"
              "Camptocamp,"
              "AvanzOSC,"
              "Tecnativa,"
              "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/connector-prestashop",
    "category": "Connector",
    'demo': [
        'demo/backend.xml',
    ],
    'data': [
        'data/cart.xml',
        'data/cron.xml',
        'views/prestashop_model_view.xml',
        'views/product_template_view.xml',
        'views/prestashop_product_combination.xml',
        'views/product_product_view.xml',
        'views/res_partner_category.xml',
        'views/res_partner.xml',
        'views/delivery_carrier.xml',
        'views/sale_order.xml',
        'views/sale_order_state.xml',
        'views/prestashop_cart.xml',
        'views/connector_prestashop_menu.xml',
    ],
    'installable': True,
    "application": True,
}
