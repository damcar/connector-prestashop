# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models, fields, api
from odoo.addons.component.core import Component


class PrestashopStockAvailable(models.Model):
    _name = 'prestashop.stock.available'
    _inherit = 'prestashop.binding'
    _description = 'PrestaShop Stock available'

    quantity = fields.Float(
        string='Computed Quantity',
        help="Last computed quantity to send to PrestaShop."
    )
    product_id = fields.Many2one(
        comodel_name='prestashop.product.template',
        string='PrestaShop product template',
        required=True,
        ondelete='cascade',
    )
    backend_id = fields.Many2one(
        comodel_name='prestashop.backend',
        string='PrestaShop Backend',
        related='product_id.backend_id',
        store=True,
        readonly=True,
    )


class PrestashopShopAdapter(Component):
    _name = 'prestashop.stock.availbale.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.stock.available'

    _prestashop_model = 'stock_availables'
