# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping


class SaleOrderStateMapper(Component):
    _name = 'prestashop.sale.order.state.mapper'
    _inherit = 'prestashop.import.mapper'
    _apply_on = 'prestashop.sale.order.state'

    direct = [
        ('name', 'name'),
    ]

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}


class SaleOrderStateImporter(Component):
    _name = 'prestashop.sale.order.state.importer'
    _inherit = 'prestashop.importer'
    _apply_on = ['prestashop.sale.order.state']

    _translatable_fields = [
        'name',
    ]
