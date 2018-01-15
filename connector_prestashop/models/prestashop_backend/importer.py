# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import Component


class PrestaShopMetadataBatchImporter(Component):
    _name = 'prestashop.metadata.batch.importer'
    _inherit = 'prestashop.direct.batch.importer'
    _apply_on = [
        'prestashop.shop.group',
        'prestashop.shop',
        'prestashop.res.lang',
        'prestashop.res.country',
        'prestashop.account.tax',
        'prestashop.sale.order.state',
    ]
