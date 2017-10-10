# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models, fields, api
from odoo.addons.component.core import Component


class PrestashopShop(models.Model):
    _name = 'prestashop.shop'
    _inherit = 'prestashop.binding'
    _description = 'PrestaShop Shop'

    @api.multi
    @api.depends('shop_group_id', 'shop_group_id.backend_id')
    def _compute_backend_id(self):
        for shop in self:
            shop.backend_id = shop.shop_group_id.backend_id.id

    name = fields.Char(
        string='Name',
        help="The name of the method on the backend",
        required=True
    )
    shop_group_id = fields.Many2one(
        comodel_name='prestashop.shop.group',
        string='PrestaShop Shop Group',
        required=True,
        ondelete='cascade',
    )
    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Warehouse',
        required=True,
        readonly=True,
        ondelete='cascade',
        oldname='openerp_id',
    )
    backend_id = fields.Many2one(
        compute='_compute_backend_id',
        comodel_name='prestashop.backend',
        string='PrestaShop Backend',
        store=True,
    )


class PrestaShopShopAdapter(Component):
    _name = 'prestashop.shop.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.shop'

    _prestashop_model = 'shops'
    # _admin_path = 'system_store/editGroup/group_id/{id}'
