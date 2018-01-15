# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models, fields, api
from odoo.addons.component.core import Component


class PrestashopDeliveryCarrier(models.Model):
    _name = 'prestashop.delivery.carrier'
    _inherit = 'prestashop.binding'
    _inherits = {'delivery.carrier': 'odoo_id'}

    odoo_id = fields.Many2one(
        comodel_name='delivery.carrier',
        string='Delivery carrier',
        required=True,
        ondelete='cascade',
        oldname='openerp_id',
    )


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.delivery.carrier',
        inverse_name='odoo_id',
        string='PrestaShop Bindings',
    )
    id_reference = fields.Integer(
        string='Reference ID',
        help="In PrestaShop, carriers can be copied with the same 'Reference "
             "ID' (only the last copied carrier will be synchronized with the "
             "ERP)"
    )
    active_ext = fields.Boolean(
        string='Active in PrestaShop',
    )


class DeliveryCarrierAdapter(Component):
    _name = 'prestashop.delivery.carrier.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.delivery.carrier'

    _prestashop_model = 'carriers'
