# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class PrestaShopModelBinder(Component):
    """ Bind records and give odoo/prestashop ids correspondence

    Binding models are models called ``magento.{normal_model}``,
    like ``magento.res.partner`` or ``magento.product.product``.
    They are ``_inherits`` of the normal models and contains
    the Magento ID, the ID of the Magento Backend and the additional
    fields belonging to the Magento instance.
    """
    _name = 'prstashop.binder'
    _inherit = ['base.binder', 'base.prestashop.connector']
    _apply_on = [
        'prestashop.shop.group',
        'prestashop.shop',
        'prestashop.res.lang',
        'prestashop.res.country',
        'prestashop.account.tax',
        'prestashop.res.partner',
        'prestashop.address',
        'prestashop.res.partner.category',
        'prestashop.product.category',
        'prestashop.product.template',
        'prestashop.groups.pricelist',
        'prestashop.product.product',
        'prestashop.product.combination',
        'prestashop.product.combination.option',
        'prestashop.product.combination.option.value',
        # 'magento.stock.picking',
        # 'magento.sale.order',
        # 'magento.sale.order.line',
        # 'magento.account.invoice',
    ]
