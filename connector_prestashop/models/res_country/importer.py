# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import _
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping


class ResCountryImportMapper(Component):
    _name = 'prestashop.res.country.mapper'
    _inherit = 'prestashop.import.mapper'
    _apply_on = 'prestashop.res.country'

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def odoo_id(self, record):
        country = self.env['res.country'].search([]).filtered(
            lambda c: c.code.lower() == record['iso_code'].lower())
        if country:
            return {'odoo_id': country.id}


class ResCountryImporter(Component):
    _name = 'prestashop.res.country.importer'
    _inherit = 'prestashop.importer'
    _apply_on = 'prestashop.res.country'

    _translatable_fields = [
        'name',
    ]

    def _has_to_skip(self):
        """ Return True if the import can be skipped """
        country = self.env['res.country'].search([]).filtered(
            lambda c: c.code.lower() == self.prestashop_record[
                'iso_code'].lower())
        if not country:
            msg = _("Cannot find country %s with this code: %s" %
                    (self.main_lang_data['name'],
                     self.main_lang_data['iso_code']))
            self.backend_record.add_checkpoint_message(msg)
            return True
        return False
