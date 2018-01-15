# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models, fields, api
from odoo.addons.component.core import Component


class ProductCategory(models.Model):
    _inherit = 'product.category'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.product.category',
        inverse_name='odoo_id',
        string="PrestaShop Bindings",
    )
    default_shop_id = fields.Many2one(comodel_name='prestashop.shop')
    description = fields.Html(
        string='Description', translate=True,
        help='HTML description from PrestaShop')
    link_rewrite = fields.Char(string='Friendly URL', translate=True)
    meta_description = fields.Char('Meta description', translate=True)
    meta_keywords = fields.Char(string='Meta keywords', translate=True)
    meta_title = fields.Char(string='Meta title', translate=True)
    position = fields.Integer(string='Position')
    active = fields.Boolean(string="Active")


class PrestashopProductCategory(models.Model):
    _name = 'prestashop.product.category'
    _inherit = 'prestashop.binding'
    _inherits = {'product.category': 'odoo_id'}

    odoo_id = fields.Many2one(
        comodel_name='product.category',
        required=True,
        ondelete='cascade',
        string='Product Category',
        oldname='openerp_id',
    )
    date_add = fields.Datetime(
        string='Created At (on PrestaShop)',
        readonly=True
    )
    date_upd = fields.Datetime(
        string='Updated At (on PrestaShop)',
        readonly=True
    )


class ProductCategoryAdapter(Component):
    _name = 'prestashop.product.category.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.product.category'

    _prestashop_model = 'categories'
