# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp
from odoo.addons.component.core import Component
import logging

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.product.template',
        inverse_name='odoo_id',
        copy=False,
        string='PrestaShop Bindings',
    )

    def recompute_price(self):
        self.ensure_one()
        for variant in self.product_variant_ids:
            if variant.default_on:
                base_price = variant.list_price - variant.impact_price
                self.list_price = base_price


class PrestashopProductTemplate(models.Model):
    _name = 'prestashop.product.template'
    _inherit = 'prestashop.binding'
    _inherits = {'product.template': 'odoo_id'}

    odoo_id = fields.Many2one(
        comodel_name='product.template',
        required=True,
        ondelete='cascade',
        string='Template',
        oldname='openerp_id',
    )
    # TODO FIXME what name give to field present in
    # prestashop_product_product and product_product
    always_available = fields.Boolean(
        string='Active',
        default=True,
        help='If checked, this product is considered always available')
    description_html = fields.Html(
        string='Description',
        translate=True,
        help="HTML description from PrestaShop",
    )
    description_short_html = fields.Html(
        string='Short Description',
        translate=True,
    )
    date_add = fields.Datetime(
        string='Created at (in PrestaShop)',
        readonly=True
    )
    date_upd = fields.Datetime(
        string='Updated at (in PrestaShop)',
        readonly=True
    )
    default_shop_id = fields.Many2one(
        comodel_name='prestashop.shop',
        string='Default shop',
        required=True
    )
    link_rewrite = fields.Char(
        string='Friendly URL',
        translate=True,
    )
    available_for_order = fields.Boolean(
        string='Available for Order Taking',
        default=True,
    )
    combinations_ids = fields.One2many(
        comodel_name='prestashop.product.combination',
        inverse_name='template_id',
        string='Combinations'
    )
    on_sale = fields.Boolean(string='Show on sale icon')
    wholesale_price = fields.Float(
        string='Cost Price',
        digits=dp.get_precision('Product Price'),
    )


class TemplateAdapter(Component):
    _name = 'prestashop.product.template.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.product.template'

    _prestashop_model = 'products'
