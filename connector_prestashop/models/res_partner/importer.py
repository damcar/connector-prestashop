# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import _
from odoo.addons.component.core import Component
from ...components.mapper import normalize_boolean
from odoo.addons.connector.components.mapper import mapping, only_create, \
    external_to_m2o

import logging
_logger = logging.getLogger(__name__)

class PartnerImportMapper(Component):
    _name = 'prestashop.res.partner.mapper'
    _inherit = 'prestashop.import.mapper'
    _apply_on = 'prestashop.res.partner'

    direct = [
        ('date_add', 'date_add'),
        ('date_upd', 'date_upd'),
        ('email', 'email'),
        (normalize_boolean('newsletter'), 'newsletter'),
        (normalize_boolean('active'), 'active'),
        ('note', 'comment'),
        (external_to_m2o('id_shop_group'), 'shop_group_id'),
        (external_to_m2o('id_shop'), 'shop_id'),
        (external_to_m2o('id_default_group'), 'default_category_id'),
    ]

    @mapping
    def birthday(self, record):
        if record['birthday'] in ['0000-00-00', '']:
            return {}
        return {'birthday': record['birthday']}

    @mapping
    def name(self, record):
        parts = [record['firstname'], record['lastname']]
        name = ' '.join(p.strip() for p in parts if p.strip())
        return {'name': name}

    @mapping
    def groups(self, record):
        if self.backend_record.version == '1.6.0.9':
            group_key = 'groups'
        elif self.backend_record.version == '1.6.1.2':
            group_key = 'group'
        groups = record.get(
            'associations', {}).get('groups', {}).get(group_key, [])
        if not isinstance(groups, list):
            groups = [groups]
        model_name = 'prestashop.res.partner.category'
        partner_category_bindings = self.env[model_name].browse()
        binder = self.binder_for(model_name)
        for group in groups:
            partner_category_bindings |= binder.to_internal(group['id'])
        result = {'group_ids': [(6, 0, partner_category_bindings.ids)],
                  'category_id': [(4, b.odoo_id.id)
                                  for b in partner_category_bindings]}
        return result

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def lang(self, record):
        erp_lang = None
        if record.get('id_lang'):
            erp_lang = self.env['prestashop.res.lang'].search([('external_id', '=', record['id_lang'])], limit=1)
        if not erp_lang:
            erp_lang = self.env.ref('base.lang_en')
        return {'lang': erp_lang.code}

    @mapping
    def customer(self, record):
        return {'customer': True}

    @mapping
    def is_company(self, record):
        # This is sad because we _have_ to have a company partner if we want to
        # store multiple adresses... but... well... we have customers who want
        # to be billed at home and be delivered at work... (...)...
        return {'is_company': True}

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}


class PartnerImporter(Component):
    _name = 'prestashop.res.partner.importer'
    _inherit = 'prestashop.importer'
    _apply_on = ['prestashop.res.partner']

    def _import_dependencies(self):
        if self.backend_record.version == '1.6.0.9':
            group_key = 'groups'
        elif self.backend_record.version == '1.6.1.2':
            group_key = 'group'
        groups = self.prestashop_record.get('associations', {}) \
            .get('groups', {}).get(group_key, [])
        if not isinstance(groups, list):
            groups = [groups]
        for group in groups:
            self._import_dependency(group['id'],
                                    'prestashop.res.partner.category')

    def _after_import(self, binding):
        super(PartnerImporter, self)._after_import(binding)
        address_importer = self.component(usage='prestashop.address.importer',
                                          model_name='prestashop.address')
        address_importer.run(self.external_id)


class PartnerBatchImporter(Component):
    _name = 'prestashop.res.partner.batch.importer'
    _inherit = 'prestashop.delayed.batch.importer'
    _apply_on = ['prestashop.res.partner']

    def run(self, filters=None):
        since_date = filters.pop('since_date', None)
        if since_date:
            filters = {'date': '1', 'filter[date_upd]': '>[%s]' % (since_date)}
        super(PartnerBatchImporter, self).run(filters)


class AddressImportMapper(Component):
    _name = 'prestashop.address.mapper'
    _inherit = 'prestashop.import.mapper'
    _apply_on = 'prestashop.address'

    direct = [
        ('address1', 'street'),
        ('address2', 'street2'),
        ('city', 'city'),
        ('other', 'comment'),
        ('phone', 'phone'),
        ('phone_mobile', 'mobile'),
        ('postcode', 'zip'),
        ('date_add', 'date_add'),
        ('date_upd', 'date_upd'),
        (external_to_m2o('id_customer'), 'prestashop_partner_id'),
        ('deleted', 'deleted'),
    ]

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def parent_id(self, record):
        binder = self.binder_for('prestashop.res.partner')
        parent = binder.to_internal(record['id_customer'], unwrap=True)
        #parent = self.env['prestashop.res.partner'].search([('external_id', '=', record['id_customer'])], limit=1)
        return {'parent_id': parent.id}

    @mapping
    def name(self, record):
        parts = [record['firstname'], record['lastname']]
        if record['alias']:
            parts.append('(%s)' % record['alias'])
        name = ' '.join(p.strip() for p in parts if p.strip())
        return {'name': name}

    @mapping
    def customer(self, record):
        return {'customer': True}

    @mapping
    def country(self, record):
        if record.get('id_country'):
            country = self.env['prestashop.res.country'].search([('external_id', '=', record['id_country'])], limit=1)
            return {'country_id': country.id}
        return {}

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}

    @only_create
    @mapping
    def type(self, record):
        # do not set 'contact', otherwise the address fields are shared with
        # the parent
        return {'type': 'other'}


class AddressImporter(Component):
    _name = 'prestashop.address.importer'
    _inherit = 'prestashop.importer'
    _usage = 'prestashop.address.importer'

    def _check_vat(self, vat):
        vat_country, vat_number = vat[:2].lower(), vat[2:]
        partner_model = self.env['res.partner']
        return partner_model.simple_vat_check(vat_country, vat_number)

    def _after_import(self, binding):
        record = self.prestashop_record
        vat_number = None
        if record['vat_number']:
            vat_number = record['vat_number'].replace('.', '').replace(' ', '')
        # TODO move to custom localization module
        elif not record['vat_number'] and record.get('dni'):
            vat_number = record['dni'].replace('.', '').replace(
                ' ', '').replace('-', '')

        if vat_number:
            if self._check_vat(vat_number):
                binding.parent_id.write({'vat': vat_number})
            else:
                msg = _('Please check the VAT number: %s') % vat_number
                self.backend_record.add_checkpoint(binding, message=msg)

        if 'deleted' in record and record['deleted']:
            binding.parent_id.write({'active': False})

    def run(self, external_id):
        filters = {'filter[id_customer]': '%d' % (int(external_id))}
        record_ids = self.backend_adapter.search(filters)
        for record_id in record_ids:
            _logger.debug(record_id)
            super(AddressImporter, self).run(record_id)
