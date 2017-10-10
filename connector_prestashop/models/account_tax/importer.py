# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import _
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
from odoo.addons.connector.unit.mapper import external_to_m2o
from odoo.addons.connector.exception import MappingError, InvalidDataError


# class AccountTaxImporter(AutoMatchingImporter):
#     _model_name = 'prestashop.account.tax'
#     _erp_field = 'amount'
#     _ps_field = 'rate'
#
#     def _compare_function(self, ps_val, erp_val, ps_dict, erp_dict):
#         if self.backend_record.taxes_included and erp_dict['price_include']:
#             taxes_inclusion_test = True
#         else:
#             taxes_inclusion_test = not erp_dict['price_include']
#         if not taxes_inclusion_test:
#             return False
#         return (erp_dict['type_tax_use'] == 'sale' and
#                 erp_dict['amount_type'] == 'percent' and
#                 abs(erp_val - float(ps_val)) < 0.01 and
#                 self.backend_record.company_id.id == erp_dict['company_id'][0])


class AccountTaxImportMapper(Component):
    _name = 'prestashop.account.tax.mapper'
    _inherit = 'prestashop.import.mapper'
    _apply_on = 'prestashop.account.tax'

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def odoo_id(self, record):
        taxe = self.env['account.tax'].search([('type_tax_use', '=', 'sale'), ('amount_type', '=', 'percent'), ('company_id', '=', self.backend_record.company_id.id)]).filtered(
            lambda c: abs(c.amount - float(record['rate'])) < 0.01)
        if len(taxe) > 1:
            taxe = taxe[0]
        if taxe:
            return {'odoo_id': taxe.id}


class AccountTaxImporter(Component):
    _name = 'prestashop.account.tax.importer'
    _inherit = 'prestashop.importer'
    _apply_on = 'prestashop.account.tax'

    _translatable_fields = [
    ]

    def _has_to_skip(self):
        """ Return True if the import can be skipped """
        country = self.env['account.tax'].search([('type_tax_use', '=', 'sale'), ('amount_type', '=', 'percent'), ('company_id', '=', self.backend_record.company_id.id)]).filtered(
            lambda c: abs(c.amount - float(self.prestashop_record['rate'])) < 0.01)
        print(country)
        if not country:
            msg = _("Cannot find tax %s" % (self.main_lang_data['name']))
            self.backend_record.add_checkpoint_message(msg)
            return True
        return False