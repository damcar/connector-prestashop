# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, external_to_m2o


class CarrierImportMapper(Component):
    _name = 'prestashop.delivery.carrier.mapper'
    _inherit = 'prestashop.import.mapper'
    _apply_on = 'prestashop.delivery.carrier'

    direct = [
        ('name', 'name'),
        ('id_reference', 'id_reference'),
    ]

    @mapping
    def active(self, record):
        return {'active_ext': record['active'] == '1'}

    @mapping
    def product_id(self, record):
        if self.backend_record.shipping_product_id:
            return {'product_id': self.backend_record.shipping_product_id.id}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}


class DeliveryCarrierImporter(Component):
    _name = 'prestashop.delivery.carrier.importer'
    _inherit = 'prestashop.importer'
    _apply_on = 'prestashop.delivery.carrier'
