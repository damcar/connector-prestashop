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
        "product_multi_category",  # oca/product-attribute
        "connector_base_product",
        # "connector_ecommerce",  # oca/connector-ecommerce
        # "product_multi_image",  # oca/product-attribute
        "purchase",
        "sale",
        "delivery",
        # "product_variant_supplierinfo",  # oca/product-variant
        # TODO: perhaps not needed:
        # "product_variant_cost_price",  # oca/product-variant
    ],
    "external_dependencies": {
        'python': [
            # "html2text",
            "prestapyt",
            # tests dependencies
            # "freezegun",
            # "vcr",
            # "bs4",
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
        # 'data/cron.xml',
        # 'data/product_decimal_precision.xml',
        'data/cart.xml',
        'views/prestashop_model_view.xml',
        'views/product_template_view.xml',
        'views/prestashop_product_combination.xml',
        'views/product_product_view.xml',
        # 'views/product_category_view.xml',
        # 'views/image_view.xml',
        # 'views/delivery_view.xml',
        'views/res_partner_category.xml',
        'views/res_partner.xml',
        'views/delivery_carrier.xml',
        'views/sale_order.xml',
        'views/sale_order_state.xml',
        'views/prestashop_cart.xml',
        'views/connector_prestashop_menu.xml',
        # 'views/sale_view.xml',
        # 'views/account_view.xml',
        # 'views/stock_view.xml',
        # 'security/ir.model.access.csv',
        # 'security/prestashop_security.xml',
        # 'data/ecommerce_data.xml',
    ],
    'installable': True,
    "application": True,
}
