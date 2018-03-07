# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class PrestashopModelBinder(Component):
    _name = 'prestashop.binder'
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
        'prestashop.sale.order',
        'prestashop.sale.order.line',
        'prestashop.sale.order.state',
        'prestashop.delivery.carrier',
        'prestashop.cart',
        'prestashop.cart.line',
        'prestashop.stock.available',
    ]
