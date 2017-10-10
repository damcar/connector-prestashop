# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import Component


class PrestaShopMetadataBatchImporter(Component):
    """ Import the records directly, without delaying the jobs.

    Import the Magento Websites, Stores, Storeviews

    They are imported directly because this is a rare and fast operation,
    and we don't really bother if it blocks the UI during this time.
    (that's also a mean to rapidly check the connectivity with Magento).

    """

    _name = 'prestashop.metadata.batch.importer'
    _inherit = 'prestashop.direct.batch.importer'
    _apply_on = [
        'prestashop.shop.group',
        'prestashop.shop',
        'prestashop.res.lang',
        'prestashop.res.country',
        'prestashop.account.tax',
    ]
