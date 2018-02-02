# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import odoo.addons.decimal_precision as dp
import logging
from odoo import models, fields, api
from odoo.addons.component.core import Component


_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.sale.order',
        inverse_name='odoo_id',
        string='PrestaShop Bindings',
    )
    shop_id = fields.Many2one(
        comodel_name='prestashop.shop',
        string='PrestaShop Shop',
    )
    shop_group_id = fields.Many2one(
        comodel_name='prestashop.shop.group',
        string='PrestaShop Shop Group',
    )
    sale_order_state_id = fields.Many2one(
        comodel_name='prestashop.sale.order.state',
        string='PrestaShop State',
    )


class PrestashopSaleOrder(models.Model):
    _name = 'prestashop.sale.order'
    _inherit = 'prestashop.binding'
    _inherits = {'sale.order': 'odoo_id'}

    odoo_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale Order',
        required=True,
        ondelete='cascade',
        oldname='openerp_id',
    )
    prestashop_order_line_ids = fields.One2many(
        comodel_name='prestashop.sale.order.line',
        inverse_name='prestashop_order_id',
        string='PrestaShop Order Lines',
    )
    prestashop_invoice_number = fields.Char('PrestaShop Invoice Number')
    prestashop_delivery_number = fields.Char('PrestaShop Delivery Number')
    total_amount = fields.Float(
        string='Total amount in PrestaShop',
        digits=dp.get_precision('Account'),
        readonly=True,
    )
    total_amount_tax_included = fields.Float(
        string='Total amount tax included in PrestaShop',
        digits=dp.get_precision('Account'),
        readonly=True,
    )
    total_amount_tax_excluded = fields.Float(
        string='Total amount tax excluded in PrestaShop',
        digits=dp.get_precision('Account'),
        readonly=True,
    )
    total_amount_tax = fields.Float(
        string='Total tax in PrestaShop',
        digits=dp.get_precision('Account'),
        readonly=True,
    )
    total_shipping = fields.Float(
        string='Total shipping in PrestaShop',
        digits=dp.get_precision('Account'),
        readonly=True,
    )
    total_shipping_tax_included = fields.Float(
        string='Total shipping tax included in PrestaShop',
        digits=dp.get_precision('Account'),
        readonly=True,
    )
    total_shipping_tax_excluded = fields.Float(
        string='Total shipping tax excluded in PrestaShop',
        digits=dp.get_precision('Account'),
        readonly=True,
    )
    total_discounts = fields.Float(
        string='Total discounts in PrestaShop',
        digits=dp.get_precision('Account'),
        readonly=True,
    )
    total_discounts_tax_excluded = fields.Float(
        string='Total discounts tax excluded in PrestaShop',
        digits=dp.get_precision('Account'),
        readonly=True,
    )
    total_discounts_tax_included = fields.Float(
        string='Total discounts tax included in PrestaShop',
        digits=dp.get_precision('Account'),
        readonly=True,
    )
    date_add = fields.Datetime(
        string='Created At (on PrestaShop)',
        readonly=True,
    )
    date_upd = fields.Datetime(
        string='Updated At (on PrestaShop)',
        readonly=True,
    )


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.sale.order.line',
        inverse_name='odoo_id',
        string='PrestaShop Bindings',
    )
    prestashop_is_shipping = fields.Boolean(
        string="Shipping Line",
        default=False
    )
    prestashop_is_discount = fields.Boolean(
        string="Discount Line",
        default=False
    )


class PrestashopSaleOrderLine(models.Model):
    _name = 'prestashop.sale.order.line'
    _inherit = 'prestashop.binding'
    _inherits = {'sale.order.line': 'odoo_id'}

    odoo_id = fields.Many2one(
        comodel_name='sale.order.line',
        string='Sale Order line',
        required=True,
        ondelete='cascade',
        oldname='openerp_id',
    )
    prestashop_order_id = fields.Many2one(
        comodel_name='prestashop.sale.order',
        string='PrestaShop Sale Order',
        required=True,
        ondelete='cascade',
        index=True,
    )
    product_price = fields.Float(
        string='Product price in PrestaShop',
        digits=dp.get_precision('Account'),
        readonly=True,
    )
    unit_price_tax_incl = fields.Float(
        string='Unit price tax included in PrestaShop',
        digits=dp.get_precision('Account'),
        readonly=True,
    )
    unit_price_tax_excl = fields.Float(
        string='Unit Price tax excluded in PrestaShop',
        digits=dp.get_precision('Account'),
        readonly=True,
    )

    @api.model
    def create(self, vals):
        ps_sale_order = self.env['prestashop.sale.order'].search([
            ('id', '=', vals['prestashop_order_id'])
        ], limit=1)
        vals['order_id'] = ps_sale_order.odoo_id.id
        return super(PrestashopSaleOrderLine, self).create(vals)


class SaleOrderAdapter(Component):
    _name = 'prestashop.sale.order.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.sale.order'

    _prestashop_model = 'orders'
