# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create, \
    external_to_m2o
from odoo.addons.connector.exception import MappingError, InvalidDataError
import datetime
import logging
import base64

_logger = logging.getLogger(__name__)

try:
    import html2text
except ImportError:
    _logger.debug('Cannot import `html2text`')

try:
    from bs4 import BeautifulSoup
except ImportError:
    _logger.debug('Cannot import `bs4`')

try:
    from prestapyt import PrestaShopWebServiceError
except ImportError:
    _logger.debug('Cannot import from `prestapyt`')


class TemplateMapper(Component):
    _name = 'prestashop.product.template.mapper'
    _inherit = 'prestashop.import.mapper'
    _apply_on = 'prestashop.product.template'

    direct = [
        ('weight', 'weight'),
        ('wholesale_price', 'wholesale_price'),
        ('wholesale_price', 'standard_price'),
        (external_to_m2o('id_shop_default'), 'default_shop_id'),
        ('link_rewrite', 'link_rewrite'),
        ('available_for_order', 'available_for_order'),
        ('on_sale', 'on_sale'),
        ('reference', 'default_code'),
        ('ean13', 'barcode'),
    ]

    def _apply_taxes(self, price):
        tax = self.backend_record.product_tax_id
        if tax.price_include:
            return price
        else:
            return price / (1 + tax.amount / 100)

    @mapping
    def list_price(self, record):
        price = 0.0
        if record['price'] != '':
            price = float(record['price'])
        price = self._apply_taxes(price)
        return {'list_price': price}

    @mapping
    def name(self, record):
        if record['name']:
            return {'name': record['name']}
        return {'name': 'noname'}

    @mapping
    def date_add(self, record):
        if record['date_add'] == '0000-00-00 00:00:00':
            return {'date_add': datetime.datetime.now()}
        return {'date_add': record['date_add']}

    @mapping
    def date_upd(self, record):
        if record['date_upd'] == '0000-00-00 00:00:00':
            return {'date_upd': datetime.datetime.now()}
        return {'date_upd': record['date_upd']}

    # @only_create
    # @mapping
    # def odoo_id(self, record):
    #     """ Will bind the product to an existing one with the same code """
    #     product = self.env['product.template'].search(
    #         [('default_code', '=', record['reference'])], limit=1)
    #     if product:
    #         return {'odoo_id': product.id}

    def _template_code_exists(self, code):
        model = self.env['product.template']
        template_ids = model.search([
            ('default_code', '=', code),
            ('company_id', '=', self.backend_record.company_id.id),
        ], limit=1)
        return len(template_ids) > 0

    def clear_html_field(self, content):
        html = html2text.HTML2Text()
        html.ignore_images = True
        html.ignore_links = True
        return html.handle(content)

    @staticmethod
    def sanitize_html(content):
        content = BeautifulSoup(content, 'html.parser')
        # Prestashop adds both 'lang="fr-ch"' and 'xml:lang="fr-ch"'
        # but Odoo tries to parse the xml for the translation and fails
        # due to the unknow namespace
        for child in content.find_all(lambda tag: tag.has_attr('xml:lang')):
            del child['xml:lang']
        return content.prettify()

    @mapping
    def descriptions(self, record):
        return {
            'description': self.clear_html_field(
                record.get('description_short', '')),
            'description_html': self.sanitize_html(
                record.get('description', '')),
            'description_short_html': self.sanitize_html(
                record.get('description_short', '')),
        }

    @mapping
    def active(self, record):
        return {'always_available': bool(int(record['active']))}

    @mapping
    def sale_ok(self, record):
        # if this product has combinations, we do not want to sell this
        # product, but its combinations (so sale_ok = False in that case).
        return {'sale_ok': True}

    @mapping
    def purchase_ok(self, record):
        return {'purchase_ok': True}

    @mapping
    def categ_ids(self, record):
        if self.backend_record.version == '1.6.0.9':
            category_key = 'categories'
        elif self.backend_record.version == '1.6.1.2':
            category_key = 'category'
        ps_categories = record['associations'].get('categories', {}).get(
            category_key, [])
        if not isinstance(ps_categories, list):
            ps_categories = [ps_categories]
        categories = self.env['product.category'].browse()
        binder = self.binder_for('prestashop.product.category')
        for ps_category in ps_categories:
            categories |= binder.to_internal(ps_category['id'], unwrap=True)
        return {'categ_ids': [(6, 0, categories.ids)]}

    @mapping
    def categ_id(self, record):
        if not int(record['id_category_default']):
            return
        binder = self.binder_for('prestashop.product.category')
        category = binder.to_internal(
            record['id_category_default'],
            unwrap=True,
        )
        print('-----------')
        print(record['id_category_default'])
        print(category)
        print('-----------')
        if category:
            return {'categ_id': category.id}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}

    @mapping
    def taxes_id(self, record):
        tax = self.backend_record.product_tax_id
        return {'taxes_id': [(6, 0, [tax.id])]}

    @mapping
    def type(self, record):
        # If the product has combinations, this main product is not a real
        # product. So it is set to a 'service' kind of product. Should better
        # be a 'virtual' product... but it does not exist...
        # The same if the product is a virtual one in prestashop.
        product_type = 'product'
        print('1-----------')
        print(record['type'])
        if record['type']['value'] and record['type']['value'] == 'virtual':
            product_type = 'service'
        print(product_type)
        print('1-----------')
        return {'type': product_type}


class ProductTemplateImporter(Component):
    _name = 'prestashop.product.template.importer'
    _inherit = 'prestashop.importer'
    _apply_on = ['prestashop.product.template']

    _translatable_fields = [
        'name',
        'description',
        'link_rewrite',
        'description_short',
        'meta_title',
        'meta_description',
        'meta_keywords',
    ]

    def _after_import(self, binding):
        super(ProductTemplateImporter, self)._after_import(binding)
        print('AFTER IMPORT1')
        print(binding.type)
        self.import_combinations(binding)
        print('AFTER IMPORT 2END')
        print(binding.type)
        self.attribute_line(binding)
        print('AFTER IMPORT 3END')
        print(binding.type)
        self.delete_default_product(binding)
        print('AFTER IMPORT 4END')
        print(binding.type)
        # image_importer = self.component(usage='product.image.importer')
        # image_importer.run(self.external_id, binding)

    def delete_default_product(self, binding):
        if binding.product_variant_count != 1:
            for product in binding.product_variant_ids:
                if not product.attribute_value_ids:
                    product.unlink()

    # def attribute_line(self, binding):
    #     attr_line_value_ids = []
    #     for attr_line in binding.attribute_line_ids:
    #         attr_line_value_ids.extend(attr_line.value_ids.ids)
    #     template_id = binding.odoo_id.id
    #     products = self.env['product.product'].search([
    #         ('product_tmpl_id', '=', template_id)]
    #     )
    #     if products:
    #         attribute_ids = []
    #         for product in products:
    #             for attribute_value in product.attribute_value_ids:
    #                 attribute_ids.append(attribute_value.attribute_id.id)
    #                 # filter unique id for create relation
    #         for attribute_id in set(attribute_ids):
    #             values = products.mapped('attribute_value_ids').filtered(
    #                 lambda x: (x.attribute_id.id == attribute_id and
    #                            x.id not in attr_line_value_ids))
    #             if values:
    #                 self.env['product.attribute.line'].create({
    #                     'attribute_id': attribute_id,
    #                     'product_tmpl_id': template_id,
    #                     'value_ids': [(6, 0, values.ids)],
    #                 })

    def attribute_line(self, binding):
        old_attribute = {}
        new_attribute = {}
        for attr_line in binding.attribute_line_ids:
            old_attribute[attr_line.attribute_id.id] = attr_line.value_ids.ids
        template_id = binding.odoo_id.id
        products = self.env['product.product'].search([
            ('product_tmpl_id', '=', template_id)]
        )
        for product in products:
            for attribute_value in product.attribute_value_ids:
                attribute_id = attribute_value.attribute_id.id
                value_id = attribute_value.id
                if attribute_id not in new_attribute.keys():
                    new_attribute[attribute_id] = [value_id]
                else:
                    new_attribute[attribute_id].append(value_id)
        attribute_line_obj = self.env['product.attribute.line']
        attributes = set(old_attribute) & set(new_attribute)
        for id in attributes:
            lines = attribute_line_obj.search(
                [('attribute_id', '=', id),
                 ('product_tmpl_id', '=', template_id)])
            lines.write({'value_ids': [(6, 0, new_attribute[id])]})
        attributes = set(old_attribute) - set(new_attribute)
        for id in attributes:
            lines = attribute_line_obj.search(
                [('attribute_id', '=', id),
                 ('product_tmpl_id', '=', template_id)])
            lines.unlink()
        attributes = set(new_attribute) - set(old_attribute)
        for id in attributes:
            attribute_line_obj.create({
                'attribute_id': attribute_id,
                'product_tmpl_id': template_id,
                'value_ids': [(6, 0, new_attribute[id])],
            })

    def _import_combination(self, combination, **kwargs):
        self._import_dependency(combination['id'],
                                'prestashop.product.combination',
                                always=True,
                                **kwargs)

    def import_combinations(self, binding):
        prestashop_record = self._get_prestashop_data()
        associations = prestashop_record.get('associations', {})
        if self.backend_record.version == '1.6.0.9':
            ps_key = 'combinations'
        elif self.backend_record.version == '1.6.1.2':
            ps_key = 'combination'
        combinations = associations.get('combinations', {}).get(ps_key, [])
        if not isinstance(combinations, list):
            combinations = [combinations]
        products_save = []
        if combinations:
            for combination in combinations:
                self._import_combination(combination)
                products_save.append(int(combination['id']))
        products = self.env['prestashop.product.combination'].search(
            [('template_id', '=', binding.id),
             ('external_id', 'not in', products_save)])
        for product in products:
            product.odoo_id.unlink()

    def _import_dependencies(self):
        self._import_default_category()
        self._import_categories()

    def _import_default_category(self):
        record = self.prestashop_record
        if int(record['id_category_default']):
            self._import_dependency(record['id_category_default'],
                                    'prestashop.product.category')

    def _import_categories(self):
        record = self.prestashop_record
        associations = record.get('associations', {})
        if self.backend_record.version == '1.6.0.9':
            category_key = 'categories'
        elif self.backend_record.version == '1.6.1.2':
            category_key = 'category'
        categories = associations.get('categories', {}).get(category_key, [])
        if not isinstance(categories, list):
            categories = [categories]
        for category in categories:
            self._import_dependency(category['id'],
                                    'prestashop.product.category')


class ProductTemplateBatchImporter(Component):
    _name = 'prestashop.product.template.batch.importer'
    _inherit = 'prestashop.delayed.batch.importer'
    _apply_on = ['prestashop.product.template']

    def run(self, filters=None):
        since_date = filters.pop('since_date', None)
        if since_date:
            filters = {'date': '1', 'filter[date_upd]': '>[%s]' % (since_date)}
            # filters = {'date': '1', 'filter[id]': '788'}
            updated_ids = self.backend_adapter.search(filters)
            for test_id in updated_ids:
                self._import_record(test_id)


class CatalogImageImporter(Component):
    _name = 'prestashop.product.image.importer'
    _inherit = 'prestashop.importer'
    _apply_on = ['prestashop.product.template']
    _usage = 'product.image.importer'

    def _get_image(self, product_id, image_id, filters):
        return self.backend_adapter.get_image(product_id, image_id, filters)

    def _write_image_data(self, binding, binary):
        binding = binding.with_context(connector_no_export=True)
        binding.write({'image': binary})

    def run(self, external_id, binding):
        self.external_id = external_id
        prestashop_record = self._get_prestashop_data()
        if prestashop_record['id_default_image']['value']:
            images = self._get_image(external_id,
                                     prestashop_record['id_default_image'][
                                         'value'], {})
            self._write_image_data(binding, images['content'])
