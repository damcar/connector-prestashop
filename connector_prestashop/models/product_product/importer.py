# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import _
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create
from odoo.addons.connector.components.mapper import external_to_m2o
from odoo.addons.connector.components.backend_adapter import BackendAdapter


class ProductCombinationImporter(Component):
    _name = 'prestashop.product.combination.importer'
    _inherit = 'prestashop.importer'
    _apply_on = ['prestashop.product.combination']

    def _import_dependencies(self):
        record = self.prestashop_record
        if self.backend_record.version == '1.6.0.9':
            ps_key = 'product_option_values'
        elif self.backend_record.version == '1.6.1.2':
            ps_key = 'product_option_value'
        option_values = record.get('associations', {}).get(
            'product_option_values', {}).get(ps_key, [])
        if not isinstance(option_values, list):
            option_values = [option_values]

        backend_adapter = self.component(usage='test')
        for option_value in option_values:
            test = backend_adapter.read(option_value['id'])
            self._import_dependency(
                test['id_attribute_group'],
                'prestashop.product.combination.option')
            self._import_dependency(
                test['id'],
                'prestashop.product.combination.option.value')


class ProductCombinationMapper(Component):
    _name = 'prestashop.product.combination.mapper'
    _inherit = 'prestashop.import.mapper'
    _apply_on = 'prestashop.product.combination'

    direct = [
        ('reference', 'default_code'),
        ('barcode', 'barcode'),
    ]

    from_main = []

    @mapping
    def combination_default(self, record):
        return {'default_on': bool(int(record['default_on'] or 0))}

    def get_main_template_binding(self, record):
        template_binder = self.binder_for('prestashop.product.template')
        return template_binder.to_internal(record['id_product'])

    def _get_option_value(self, record):
        if self.backend_record.version == '1.6.0.9':
            product_option_value_key = 'product_option_values'
        elif self.backend_record.version == '1.6.1.2':
            product_option_value_key = 'product_option_value'
        option_values = record.get('associations', {}).get(
            'product_option_values', {}).get(product_option_value_key, [])
        if type(option_values) is dict:
            option_values = [option_values]
        for option_value in option_values:
            option_value_binder = self.binder_for(
                'prestashop.product.combination.option.value')
            option_value_binding = option_value_binder.to_internal(
                option_value['id']
            )
            assert option_value_binding, "must have a binding for the option"
            yield option_value_binding.odoo_id

    def add_attribute_price(self, template_id, value_id, price_extra):
        price_obj = self.env['product.attribute.price']

        price_ids = price_obj.search([('product_tmpl_id', '=', template_id), ('value_id', '=', value_id)])
        if price_ids:
            price_ids.write({'price_extra': price_extra})
        else:
            price_obj.create({
                'product_tmpl_id': template_id,
                'value_id': value_id,
                'price_extra': price_extra,
            })

    @mapping
    def attribute_value_ids(self, record):
        results = []
        template_binding = self.get_main_template_binding(record)
        for option_value_object in self._get_option_value(record):
            value_id = option_value_object.id
            results.append(value_id)
            price_extra = float(record['price'] or '0.0')
            self.add_attribute_price(template_binding.odoo_id.id, value_id, price_extra)

        return {'attribute_value_ids': [(6, 0, results)]}

    @mapping
    def template_id(self, record):
        template_binding = self.get_main_template_binding(record)
        return {
            'product_tmpl_id': template_binding.odoo_id.id,
            'template_id': template_binding.id,
            'type': template_binding.type,
            'categ_id': template_binding.categ_id.id
        }

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def specific_price(self, record):
        product = self.binder_for(
            'prestashop.product.combination').to_internal(
            record['id'], unwrap=True
        )
        product_template = self.binder_for(
            'prestashop.product.template').to_internal(record['id_product'])
        impact = float(record['price'] or '0.0')
        cost_price = float(record['wholesale_price'] or '0.0')
        return {
            'list_price': product_template.list_price,
            'standard_price': cost_price or product_template.wholesale_price,
            'impact_price': impact
        }


class ProductCombinationOptionImporter(Component):
    _name = 'prestashop.product.combination.option.importer'
    _inherit = 'prestashop.importer'
    _apply_on = ['prestashop.product.combination.option']

    _translatable_fields = [
        'name',
    ]

    def _import_values(self, attribute_binding):
        record = self.prestashop_record
        if self.backend_record.version == '1.6.0.9':
            ps_key = 'product_option_values'
        elif self.backend_record.version == '1.6.1.2':
            ps_key = 'product_option_value'
        option_values = record.get('associations', {}).get(
            'product_option_values', {}).get(ps_key, [])
        if not isinstance(option_values, list):
            option_values = [option_values]
        for option_value in option_values:
            self._import_dependency(
                option_value['id'],
                'prestashop.product.combination.option.value'
            )

    def _after_import(self, binding):
        super(ProductCombinationOptionImporter, self)._after_import(binding)
        self._import_values(binding)


class ProductCombinationOptionMapper(Component):
    _name = 'prestashop.product.combination.option.mapper'
    _inherit = 'prestashop.import.mapper'
    _apply_on = 'prestashop.product.combination.option'

    direct = [
        ('name', 'name'),
    ]

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @only_create
    @mapping
    def odoo_id(self, record):
        name = record['name']
        binding = self.env['product.attribute'].search(
            [('name', '=', name)],
            limit=1,
        )
        if binding:
            return {'odoo_id': binding.id}


class ProductCombinationOptionValueImporter(Component):
    _name = 'prestashop.product.combination.option.value.importer'
    _inherit = 'prestashop.importer'
    _apply_on = ['prestashop.product.combination.option.value']

    _translatable_fields = [
        'name',
    ]


class ProductCombinationOptionValueMapper(Component):
    _name = 'prestashop.product.combination.option.value.mapper'
    _inherit = 'prestashop.import.mapper'
    _apply_on = 'prestashop.product.combination.option.value'

    direct = [
        ('name', 'name'),
    ]

    @only_create
    @mapping
    def odoo_id(self, record):
        attribute_binder = self.binder_for(
            'prestashop.product.combination.option'
        )
        attribute = attribute_binder.to_internal(
            record['id_attribute_group'],
            unwrap=True
        )
        assert attribute
        binding = self.env['product.attribute.value'].search(
            [('name', '=', record['name']),
             ('attribute_id', '=', attribute.id)],
            limit=1,
        )
        if binding:
            return {'odoo_id': binding.id}

    @mapping
    def attribute_id(self, record):
        binder = self.binder_for('prestashop.product.combination.option')
        attribute = binder.to_internal(record['id_attribute_group'], unwrap=True)
        return {'attribute_id': attribute.id}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


class ProductProductBatchImporter(Component):
    _name = 'prestashop.product.product.batch.importer'
    _inherit = 'prestashop.delayed.batch.importer'
    _apply_on = ['prestashop.product.product']
