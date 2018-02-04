# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import odoo.addons.decimal_precision as dp
import logging
from odoo import models, fields, api, _
from odoo.addons.component.core import Component


_logger = logging.getLogger(__name__)


class PrestashopCart(models.Model):
    _name = 'prestashop.cart'
    _inherit = ['prestashop.binding', 'sale.order']

    date_order = fields.Datetime(string='Date')
    order_line = fields.One2many('prestashop.cart.line', 'order_id',
                                 string='Cart Lines',
                                 states={'cancel': [('readonly', True)],
                                         'done': [('readonly', True)]},
                                 copy=True, auto_join=True)
    date_add = fields.Datetime(
        string='Created At (on PrestaShop)',
        readonly=True,
    )
    date_upd = fields.Datetime(
        string='Updated At (on PrestaShop)',
        readonly=True,
    )

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('prestashop.cart') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('prestashop.cart') or _('New')
        result = super(PrestashopCart, self).create(vals)
        return result


class PrestashopCartLine(models.Model):
    _name = 'prestashop.cart.line'
    _inherit = ['prestashop.binding', 'sale.order.line']

    order_id = fields.Many2one('prestashop.cart', string='Order Reference',
                               required=True, ondelete='cascade', index=True,
                               copy=False)


class CartAdapter(Component):
    _name = 'prestashop.cart.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.cart'

    _prestashop_model = 'carts'
