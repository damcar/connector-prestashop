# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import _
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
from odoo.addons.connector.unit.mapper import external_to_m2o
from odoo.addons.connector.exception import MappingError, InvalidDataError

# from openerp import _
# from openerp.addons.connector.unit.mapper import (mapping,
#                                                   ImportMapper)
# from openerp.addons.connector.unit.mapper import backend_to_m2o
# from ...unit.importer import TranslatableRecordImporter, DelayedBatchImporter
# from ...backend import prestashop
#
import datetime
# import logging
# _logger = logging.getLogger(__name__)
try:
    from prestapyt import PrestaShopWebServiceError
except:
    _logger.debug('Cannot import from `prestapyt`')


class ProductCategoryBatchImporter(Component):
    _name = 'prestashop.product.category.batch.importer'
    _inherit = 'prestashop.delayed.batch.importer'
    _apply_on = ['prestashop.product.category']

    def run(self, filters=None):
        since_date = filters.pop('since_date', None)
        if since_date:
            filters = {'date': '1', 'filter[date_upd]': '>[%s]' % (since_date)}
            updated_ids = self.backend_adapter.search(filters)
            for test_id in updated_ids:
                self._import_record(test_id)


class ProductCategoryMapper(Component):
    _name = 'prestashop.product.category.mapper'
    _inherit = 'prestashop.import.mapper'
    _apply_on = 'prestashop.product.category'

    direct = [
        # ('position', 'sequence'),
        ('description', 'description'),
        ('link_rewrite', 'link_rewrite'),
        ('meta_description', 'meta_description'),
        ('meta_keywords', 'meta_keywords'),
        ('meta_title', 'meta_title'),
        (external_to_m2o('id_shop_default'), 'default_shop_id'),
        ('active', 'active'),
        ('position', 'position')
    ]

    @mapping
    def name(self, record):
        if record['name'] is None:
            return {'name': ''}
        return {'name': record['name']}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def parent_id(self, record):
        if record['id_parent'] == '0':
            return {}
        binder = self.binder_for()
        parent_binding = binder.to_internal(record['id_parent'])
        if not parent_binding:
            raise MappingError("The product category with "
                               "prestashop id %s is not imported." %
                               record['id_parent'])

        parent = parent_binding.odoo_id
        return {
            'parent_id': parent.id,
            # 'magento_parent_id': parent_binding.id
        }
        # category = self.binder_for('prestashop.product.category').to_odoo(record['id_parent'], unwrap=True)
        # return {
        #     'parent_id': category.id,
        # }

    @mapping
    def data_add(self, record):
        if record['date_add'] == '0000-00-00 00:00:00':
            return {'date_add': datetime.datetime.now()}
        return {'date_add': record['date_add']}

    @mapping
    def data_upd(self, record):
        if record['date_upd'] == '0000-00-00 00:00:00':
            return {'date_upd': datetime.datetime.now()}
        return {'date_upd': record['date_upd']}









# @prestashop
# class ProductCategoryImporter(TranslatableRecordImporter):
#     _model_name = [
#         'prestashop.product.category',
#     ]
#
#     _translatable_fields = {
#         'prestashop.product.category': [
#             'name',
#             'description',
#             'link_rewrite',
#             'meta_description',
#             'meta_keywords',
#             'meta_title'
#         ],
#     }
#
#     def _import_dependencies(self):
#         record = self.prestashop_record
#         if record['id_parent'] != '0':
#             try:
#                 self._import_dependency(record['id_parent'],
#                                         'prestashop.product.category')
#             except PrestaShopWebServiceError, e:
#                 msg = _(
#                     'Parent category for `%s` '
#                     'cannot be imported. '
#                     'Error: %s'
#                 )
#                 binder = self.binder_for()
#                 category = binder.to_odoo(record['id'])
#                 if category:
#                     name = category.name
#                 else:
#                     not imported yet, retrieve name in default lang
                    # values = self._split_per_language(
                    #     record, fields=['name', ])
                    # name = values[self._default_language]['name']

                # self.backend_record.add_checkpoint(
                #     model=category._name,
                #     record_id=category.id,
                #     message=msg % (name, str(e))
                # )


class ProductCategoryImporter(Component):
    _name = 'prestashop.product.category.importer'
    _inherit = 'prestashop.importer'
    _apply_on = ['prestashop.product.category']

    def _import_dependencies(self):
        record = self.prestashop_record
        if record['id_parent'] != '0':
            try:
                self._import_dependency(record['id_parent'],
                                        'prestashop.product.category')
            except PrestaShopWebServiceError, e:
                msg = _(
                    'Parent category (id %s) for "%s" with id %s '
                    'cannot be imported. '
                    'Error: %s'
                )
                raise InvalidDataError(msg % (self.main_lang_data['id_parent'],
                                              self.main_lang_data['name'],
                                              self.main_lang_data['id'], e))
                # self.backend_record.add_checkpoint(
                #     model=category._name,
                #     record_id=category.id,
                #     message=msg % (name, str(e))
                # )
                # self.backend_record.add_checkpoint(category)

    # def _after_import(self, binding):
    #     """ Hook called at the end of the import """
    #     translation_importer = self.component(usage='translation.importer')
    #     translation_importer.run(
    #         self.external_id,
    #         binding,
    #         mapper='prestashop.product.category.mapper'
    #     )

        # image_importer = self.component(usage='product.image.importer')
        # image_importer.run(self.external_id, binding)
        #
        # if self.magento_record['type_id'] == 'bundle':
        #     bundle_importer = self.component(usage='product.bundle.importer')
        #     bundle_importer.run(binding, self.magento_record)
