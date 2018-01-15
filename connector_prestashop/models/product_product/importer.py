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
        # backend_adapter = self.unit_for(
        #     BackendAdapter, 'prestashop.product.combination.option.value')
        # backend_adapter = self.component(usage='product.combination.option.value.importer')
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

    # @mapping
    # def product_tmpl_id(self, record):
    #     template = self.get_main_template_binding(record)
    #     return {'product_tmpl_id': template.odoo_id.id}

    # @mapping
    # def from_main_template(self, record):
    #     main_template = self.get_main_template_binding(record)
    #     result = {}
    #     for attribute in self.from_main:
    #         if attribute not in main_template:
    #             continue
    #         if hasattr(main_template[attribute], 'id'):
    #             result[attribute] = main_template[attribute].id
    #         elif type(main_template[attribute]) is models.BaseModel:
    #             ids = []
    #             for element in main_template[attribute]:
    #                 ids.append(element.id)
    #             result[attribute] = [(6, 0, ids)]
    #         else:
    #             result[attribute] = main_template[attribute]
    #     return result

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

    # @mapping
    # def name(self, record):
    #     template = self.get_main_template_binding(record)
    #     options = []
    #     for option_value_object in self._get_option_value(record):
    #         key = option_value_object.attribute_id.name
    #         value = option_value_object.name
    #         options.append('%s:%s' % (key, value))
    #     return {'name_template': template.name}

    # def add_attribute_price(self, record, option_value_object):
    #     price_obj = self.env['product.attribute.price']
    #     price_obj.search([('product_tmpl_id', '=', template_binding.odoo_id.id), ('value_id', '', '')])

    def add_attribute_price(self, template_id, value_id, price_extra):
        price_obj = self.env['product.attribute.price']
        price_ids = price_obj.search([('product_tmpl_id', '=', template_id), ('value_id', '=', value_id)])
        if price_ids:
            price_obj.write({'price_extra': price_extra})
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
        print('************* : %s' % results)
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

    # def _template_code_exists(self, code):
    #     model = self.session.env['product.product']
    #     combination_binder = self.binder_for('prestashop.product.combination')
    #     template_ids = model.search([
    #         ('default_code', '=', code),
    #         ('company_id', '=', self.backend_record.company_id.id),
    #     ], limit=1)
    #     return template_ids and not combination_binder.to_backend(
    #         template_ids, wrap=True)

    # @mapping
    # def default_code(self, record):
    #     code = record.get('reference')
    #     print('______________________________')
    #     print(code)
    #     if not code:
    #         code = "%s_%s" % (record['id_product'], record['id'])
    #     if not self._template_code_exists(code):
    #         return {'default_code': code}
    #     i = 1
    #     current_code = '%s_%s' % (code, i)
    #     while self._template_code_exists(current_code):
    #         i += 1
    #         current_code = '%s_%s' % (code, i)
    #     return {'default_code': code}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    # @mapping
    # def barcode(self, record):
    #     barcode = record.get('barcode') or record.get('ean13')
    #     check_ean = self.env['barcode.nomenclature'].check_ean
    #     if barcode in ['', '0']:
    #         backend_adapter = self.unit_for(
    #             GenericAdapter, 'prestashop.product.template')
    #         template = backend_adapter.read(record['id_product'])
    #         barcode = template.get('barcode') or template.get('ean13')
    #     if barcode and barcode != '0' and check_ean(barcode):
    #         return {'barcode': barcode}
    #     return {}

    # def _get_tax_ids(self, record):
    #     product_tmpl_adapter = self.unit_for(
    #         GenericAdapter, 'prestashop.product.template')
    #     tax_group = product_tmpl_adapter.read(record['id_product'])
    #     tax_group = self.binder_for('prestashop.account.tax.group').to_odoo(
    #         tax_group['id_tax_rules_group'], unwrap=True)
    #     return tax_group.tax_ids
    #
    # def _apply_taxes(self, tax, price):
    #     if self.backend_record.taxes_included == tax.price_include:
    #         return price
    #     factor_tax = tax.price_include and (1 + tax.amount / 100) or 1.0
    #     if self.backend_record.taxes_included:
    #         if not tax.price_include:
    #             return price / factor_tax
    #     else:
    #         if tax.price_include:
    #             return price * factor_tax

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

    # @only_create
    # @mapping
    # def odoo_id(self, record):
    #     product = self.env['product.product'].search([
    #         ('default_code', '=', record['reference']),
    #         ('prestashop_bind_ids', '=', False),
    #     ], limit=1)
    #     if product:
    #         return {'odoo_id': product.id}


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

    # @mapping
    # def price(self, record):
    #     return {'price_extra': 50}


class ProductProductBatchImporter(Component):
    _name = 'prestashop.product.product.batch.importer'
    _inherit = 'prestashop.delayed.batch.importer'
    _apply_on = ['prestashop.product.product']
