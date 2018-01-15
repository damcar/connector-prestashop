# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models, fields, api
from odoo.addons.component.core import Component


class PrestashopSaleOrderState(models.Model):
    _name = 'prestashop.sale.order.state'
    _inherit = 'prestashop.binding'

    name = fields.Char('Name', translate=True)
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
    )


class SaleOrderStateAdapter(Component):
    _name = 'prestashop.sale.order.state.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.sale.order.state'

    _prestashop_model = 'order_states'
