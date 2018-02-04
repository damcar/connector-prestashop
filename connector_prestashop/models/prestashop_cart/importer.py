# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, external_to_m2o
import logging

_logger = logging.getLogger(__name__)

try:
    from prestapyt import PrestaShopWebServiceError
except:
    _logger.debug('Cannot import from `prestapyt`')


class CartMapper(Component):
    _name = 'prestashop.cart.mapper'
    _inherit = 'prestashop.import.mapper'
    _apply_on = 'prestashop.cart'
    _map_child_usage = 'prestashop.cart.map.child'
    direct = [
        ('date_add', 'date_order'),
        ('date_add', 'date_add'),
        ('date_upd', 'date_upd'),
        (external_to_m2o('id_shop_group'), 'shop_group_id'),
        (external_to_m2o('id_shop'), 'shop_id'),
    ]

    def _get_cart_lines(self, record):
        if self.backend_record.version == '1.6.0.9':
            cart_row_key = 'cart_rows'
        elif self.backend_record.version == '1.6.1.2':
            cart_row_key = 'cart_row'
        carts = record['associations'].get(
            'cart_rows', {}).get(cart_row_key, [])
        if isinstance(carts, dict):
            return [carts]
        return carts

    children = [
        (_get_cart_lines, 'order_line', 'prestashop.cart.line'),
    ]

    def _map_child(self, map_record, from_attr, to_attr, model_name):
        """ Convert items of the record as defined by children """
        assert self._map_child_usage is not None, "_map_child_usage required"
        child_records = from_attr(self, map_record.source)
        mapper_child = self._get_map_child_component(model_name)
        items = mapper_child.get_items(child_records, map_record,
                                       to_attr, options=self.options)
        return items

    @mapping
    def partner_id(self, record):
        binder = self.binder_for('prestashop.res.partner')
        partner = binder.to_internal(record['id_customer'], unwrap=True)
        return {'partner_id': partner.id}

    @mapping
    def partner_invoice_id(self, record):
        binder = self.binder_for('prestashop.address')
        address = binder.to_internal(record['id_address_invoice'], unwrap=True)
        return {'partner_invoice_id': address.id}

    @mapping
    def partner_shipping_id(self, record):
        binder = self.binder_for('prestashop.address')
        shipping = binder.to_internal(record['id_address_delivery'], unwrap=True)
        return {'partner_shipping_id': shipping.id}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def carrier_id(self, record):
        if record['id_carrier'] == '0':
            return {}
        binder = self.binder_for('prestashop.delivery.carrier')
        carrier = binder.to_internal(record['id_carrier'], unwrap=True)
        return {'carrier_id': carrier.id}

    @mapping
    def user_id(self, record):
        return {'user_id': False}


class CartImporter(Component):
    _name = 'prestashop.cart.importer'
    _inherit = 'prestashop.importer'
    _apply_on = ['prestashop.cart']

    def _import_dependencies(self):
        record = self.prestashop_record

        self._import_dependency(
            record['id_customer'], 'prestashop.res.partner'
        )
        address_importer = self.component(usage='prestashop.address.importer',
                                  model_name='prestashop.address')
        if record['id_address_invoice'] != '0':
            self._import_dependency(record['id_address_invoice'], 'prestashop.address', importer=address_importer)
        if record['id_address_delivery'] != '0':
            self._import_dependency(record['id_address_delivery'], 'prestashop.address', importer=address_importer)
        if record['id_carrier'] != '0':
            self._import_dependency(record['id_carrier'],
                                    'prestashop.delivery.carrier')


class CartBatchImporter(Component):
    _name = 'prestashop.cart.batch.importer'
    _inherit = 'prestashop.delayed.batch.importer'
    _apply_on = ['prestashop.cart']

    def run(self, filters=None):
        since_date = filters.pop('since_date', None)
        if since_date:
            filters = {'date': '1', 'filter[date_upd]': '>[%s]' % (since_date), 'filter[id_customer]': '>[0]',
                       'filter[minimum_amount]': '>[0]'}
        super(CartBatchImporter, self).run(filters)


class CartLineMapper(Component):
    _name = 'prestashop.cart.line.mapper'
    _inherit = 'prestashop.import.mapper'
    _apply_on = 'prestashop.cart.line'

    direct = [
        ('quantity', 'product_uom_qty'),
    ]

    @mapping
    def product_id(self, record):
        if int(record.get('id_product_attribute', 0)):
            combination_binder = self.binder_for(
                'prestashop.product.combination'
            )
            product = combination_binder.to_odoo(
                record['id_product_attribute'],
                unwrap=True,
            )
        else:
            binder = self.binder_for('prestashop.product.template')
            template = binder.to_internal(record['id_product'], unwrap=True)
            product = self.env['product.product'].search([
                ('product_tmpl_id', '=', template.id),
                ('company_id', '=', self.backend_record.company_id.id)],
                limit=1,
            )
        if not product:
            return {}
        return {
            'product_id': product.id,
            'product_uom': product and product.uom_id.id,
        }

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


class CartMapChild(Component):
    _name = 'prestashop.cart.map.child'
    _inherit = 'base.map.child.import'
    _usage = 'prestashop.cart.map.child'

    def format_items(self, items_values):
        lines = [(5, 0, 0)]
        binder = self.binder_for('prestashop.cart.line')
        for item in items_values:
            lines.append((0, 0, item))
        return lines
