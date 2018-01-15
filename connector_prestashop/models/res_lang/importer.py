# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping


class ResLangImportMapper(Component):
    _name = 'prestashop.res.lang.mapper'
    _inherit = 'prestashop.import.mapper'
    _apply_on = 'prestashop.res.lang'

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def odoo_id(self, record):
        lang = self.env['res.lang'].search(
            ['|', ('active', '=', True), ('active', '=', False)]).filtered(
            lambda l: l.iso_code.lower() == record['iso_code'].lower())
        if lang:
            return {'odoo_id': lang.id}

    @mapping
    def active(self, record):
        return {'active': (record.get('active') == '1')}


class ResLangImporter(Component):
    _name = 'prestashop.res.lang.importer'
    _inherit = 'prestashop.importer'
    _apply_on = 'prestashop.res.lang'

    # _translatable_fields = [
    # ]
