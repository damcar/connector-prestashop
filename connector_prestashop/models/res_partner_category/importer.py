# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping


class PartnerCategoryImportMapper(Component):
    _name = 'prestashop.res.partner.category.mapper'
    _inherit = 'prestashop.import.mapper'
    _apply_on = 'prestashop.res.partner.category'

    direct = [
        ('name', 'name'),
        ('date_add', 'date_add'),
        ('date_upd', 'date_upd'),
    ]

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


class PartnerCategoryImporter(Component):
    _name = 'prestashop.res.partner.category.importer'
    _inherit = 'prestashop.importer'
    _apply_on = ['prestashop.res.partner.category']

    _translatable_fields = [
        'name',
    ]
