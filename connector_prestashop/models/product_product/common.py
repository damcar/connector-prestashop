# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields
from odoo.addons import decimal_precision as dp
from odoo.addons.component.core import Component


class ProductProduct(models.Model):
    _inherit = 'product.product'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.product.combination',
        inverse_name='odoo_id',
        copy=False,
        string='PrestaShop Bindings',
    )
    default_on = fields.Boolean(string='Default On')
    impact_price = fields.Float(
        string="Price Impact",
        digits=dp.get_precision('Product Price')
    )


class PrestashopProductCombination(models.Model):
    _name = 'prestashop.product.combination'
    _inherit = 'prestashop.binding'
    _inherits = {'product.product': 'odoo_id'}

    odoo_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True,
        ondelete='cascade',
        oldname='openerp_id',
    )
    template_id = fields.Many2one(
        comodel_name='prestashop.product.template',
        string='Main Template',
        required=True,
        ondelete='cascade',
    )


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.product.combination.option',
        inverse_name='odoo_id',
        string='PrestaShop Bindings (combinations)',
    )


class PrestashopProductCombinationOption(models.Model):
    _name = 'prestashop.product.combination.option'
    _inherit = 'prestashop.binding'
    _inherits = {'product.attribute': 'odoo_id'}

    odoo_id = fields.Many2one(
        comodel_name='product.attribute',
        string='Attribute',
        required=True,
        ondelete='cascade',
        oldname='openerp_id',
    )
    prestashop_position = fields.Integer('PrestaShop Position')
    group_type = fields.Selection([
        ('color', 'Color'),
        ('radio', 'Radio'),
        ('select', 'Select')], string='Type', default='select')
    public_name = fields.Char(string='Public Name', translate=True)


class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.product.combination.option.value',
        inverse_name='odoo_id',
        string='PrestaShop Bindings',
    )


class PrestashopProductCombinationOptionValue(models.Model):
    _name = 'prestashop.product.combination.option.value'
    _inherit = 'prestashop.binding'
    _inherits = {'product.attribute.value': 'odoo_id'}

    odoo_id = fields.Many2one(
        comodel_name='product.attribute.value',
        string='Attribute',
        required=True,
        ondelete='cascade',
        oldname='openerp_id',
    )
    prestashop_position = fields.Integer(
        string='PrestaShop Position',
        default=1,
    )
    combination_option_id = fields.Many2one(
        comodel_name='prestashop.product.combination.option')


class ProductCombinationAdapter(Component):
    _name = 'prestashop.product.combination.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.product.combination'

    _prestashop_model = 'combinations'


class ProductCombinationOptionAdapter(Component):
    _name = 'prestashop.product.combination.option.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.product.combination.option'

    _prestashop_model = 'product_options'


class ProductCombinationOptionValueAdapter(Component):
    _name = 'prestashop.product.combination.option.value.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.product.combination'
    _usage = 'test'

    _prestashop_model = 'product_option_values'


class ProductCombinationOptionValueAdapter2(Component):
    _name = 'prestashop.product.combination.option.value.adapter2'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.product.combination.option.value'

    _prestashop_model = 'product_option_values'
