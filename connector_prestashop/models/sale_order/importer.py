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


class SaleOrderMapper(Component):
    _name = 'prestashop.sale.order.mapper'
    _inherit = 'prestashop.import.mapper'
    _apply_on = 'prestashop.sale.order'
    _map_child_usage = 'import.map.child.test'
    direct = [
        ('date_add', 'date_order'),
        ('date_add', 'date_add'),
        ('date_upd', 'date_upd'),
        ('invoice_number', 'prestashop_invoice_number'),
        ('delivery_number', 'prestashop_delivery_number'),
        ('total_paid', 'total_amount'),
        ('total_paid_tax_incl', 'total_amount_tax_included'),
        ('total_paid_tax_excl', 'total_amount_tax_excluded'),
        ('total_shipping', 'total_shipping'),
        ('total_shipping_tax_incl', 'total_shipping_tax_included'),
        ('total_shipping_tax_excl', 'total_shipping_tax_excluded'),
        ('total_discounts', 'total_discounts'),
        ('total_discounts_tax_included', 'total_discounts_tax_included'),
        ('total_discounts_tax_excluded', 'total_discounts_tax_excluded'),
        (external_to_m2o('id_shop_group'), 'shop_group_id'),
        (external_to_m2o('id_shop'), 'shop_id'),
        (external_to_m2o('current_state'), 'sale_order_state_id'),
        ('reference', 'name'),
    ]

    def _get_sale_order_lines(self, record):
        if self.backend_record.version == '1.6.0.9':
            order_row_key = 'order_rows'
        elif self.backend_record.version == '1.6.1.2':
            order_row_key = 'order_row'
        orders = record['associations'].get(
            'order_rows', {}).get(order_row_key, [])
        if isinstance(orders, dict):
            return [orders]
        return orders

    children = [
        (_get_sale_order_lines,
         'prestashop_order_line_ids', 'prestashop.sale.order.line'),
    ]

    def _add_shipping_line(self, map_record, values):
        record = map_record.source
        binder = self.binder_for('prestashop.sale.order')
        prestashop_order = binder.to_internal(record.get('id'))
        amount_incl = float(record.get('total_shipping_tax_incl') or 0.0)
        amount_excl = float(record.get('total_shipping_tax_excl') or 0.0)
        line_builder = self.component(usage='order.line.builder.shipping')
        # TODO : incl or excl
        line_builder.price_unit = amount_excl
        if values.get('carrier_id'):
            carrier = self.env['delivery.carrier'].browse(values['carrier_id'])
            line_builder.product = carrier.product_id
        vals = line_builder.get_line()
        vals['prestashop_is_shipping'] = True
        order = prestashop_order.odoo_id
        line_obj = order.order_line.filtered(lambda line: line.prestashop_is_shipping == True)
        if order and line_obj:
            vals['order_id'] = order.id
            line = (1, line_obj.id, vals)
        else:
            line = (0, 0, vals)
        values['order_line'].append(line)
        return values

    def _add_discount_line(self, map_record, values):
        record = map_record.source
        binder = self.binder_for('prestashop.sale.order')
        prestashop_order = binder.to_internal(record.get('id'))
        line_obj = False
        order = False
        if prestashop_order:
            order = prestashop_order.odoo_id
            line_obj = order.order_line.filtered(lambda line: line.product_id.id == self.backend_record.discount_product_id.id)
        amount_excl = float(record.get('total_discounts_tax_incl') or 0.0)
        amount_incl = float(record.get('total_discounts_tax_excl') or 0.0)
        if not (amount_excl or amount_incl) and not line_obj:
            return values
        line_builder = self.component(usage='order.line.builder.gift')
        # TODO : incl or excl
        line_builder.price_unit = amount_excl
        line_builder.product = self.backend_record.discount_product_id
        vals = line_builder.get_line()
        if order:
            if line_obj:
                if not (amount_excl or amount_incl):
                    line = (2, line_obj.id, 0)
                else:
                    vals['order_id'] = order.id
                    line = (1, line_obj.id, vals)
            else:
                vals['order_id'] = order.id
                line = (0, 0, vals)
        else:
            line = (0, 0, vals)
        values['order_line'].append(line)
        return values

    def _map_child(self, map_record, from_attr, to_attr, model_name):
        """ Convert items of the record as defined by children """
        assert self._map_child_usage is not None, "_map_child_usage required"
        child_records = from_attr(self, map_record.source)
        mapper_child = self._get_map_child_component(model_name)
        items = mapper_child.get_items(child_records, map_record,
                                       to_attr, options=self.options)
        return items

    def finalize(self, map_record, values):
        values.setdefault('order_line', [])
        values = self._add_shipping_line(map_record, values)
        values = self._add_discount_line(map_record, values)
        onchange = self.component(
            usage='ecommerce.onchange.manager.sale.order'
        )
        return onchange.play(values, values['prestashop_order_line_ids'])

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
    def total_tax_amount(self, record):
        tax = (float(record['total_paid_tax_incl']) - float(record['total_paid_tax_excl']))
        return {'total_amount_tax': tax}

    @mapping
    def user_id(self, record):
        """ Do not assign to a Salesperson otherwise sales orders are hidden
        for the salespersons (access rules)"""
        return {'user_id': False}

    @mapping
    def warehouse_id(self, record):
        warehouse = self.backend_record.warehouse_id
        if warehouse:
            return {'warehouse_id': warehouse.id}

    @mapping
    def sales_team(self, record):
        team = self.backend_record.sale_team_id
        if team:
            return {'team_id': team.id}


class SaleOrderImporter(Component):
    _name = 'prestashop.sale.order.importer'
    _inherit = 'prestashop.importer'
    _apply_on = ['prestashop.sale.order']

    # _translatable_fields = [
    # ]

    def __init__(self, environment):
        super(SaleOrderImporter, self).__init__(environment)
        self.line_template_errors = []

    def _import_dependencies(self):
        record = self.prestashop_record
        self._import_dependency(
            record['id_customer'], 'prestashop.res.partner'
        )
        self._import_dependency(
            record['id_address_invoice'], 'prestashop.address'
        )
        self._import_dependency(
            record['id_address_delivery'], 'prestashop.address'
        )
        if record['id_carrier'] != '0':
            self._import_dependency(record['id_carrier'],
                                    'prestashop.delivery.carrier')
        if self.backend_record.version == '1.6.0.9':
            order_row_key = 'order_rows'
        elif self.backend_record.version == '1.6.1.2':
            order_row_key = 'order_row'
        rows = record['associations'] \
            .get('order_rows', {}) \
            .get(order_row_key, [])
        if isinstance(rows, dict):
            rows = [rows]
        for row in rows:
            self._import_dependency(row['product_id'], 'prestashop.product.template')

    def _create(self, data):
        binding = super(SaleOrderImporter, self)._create(data)
        if binding:
            binding.odoo_id.onchange_partner_shipping_id()
        if binding.fiscal_position_id:
            binding.odoo_id._compute_tax_id()
        return binding


class SaleOrderBatchImporter(Component):
    _name = 'prestashop.sale.order.batch.importer'
    _inherit = 'prestashop.delayed.batch.importer'
    _apply_on = ['prestashop.sale.order']

    def run(self, filters=None):
        since_date = filters.pop('since_date', None)
        if since_date:
            filters = {'date': '1', 'filter[date_upd]': '>[%s]' % (since_date)}
            updated_ids = self.backend_adapter.search(filters)
            for test_id in updated_ids:
                self._import_record(test_id)


class SaleOrderLineMapper(Component):
    _name = 'prestashop.sale.order.line.mapper'
    _inherit = 'prestashop.import.mapper'
    _apply_on = 'prestashop.sale.order.line'

    direct = [
        ('product_name', 'name'),
        ('id', 'sequence'),
        ('product_quantity', 'product_uom_qty'),
        ('id', 'external_id'),
        ('product_price', 'product_price'),
        ('unit_price_tax_incl', 'unit_price_tax_incl'),
        ('unit_price_tax_excl', 'unit_price_tax_excl'),
    ]

    @mapping
    def price_unit(self, record):
        # TODO : incl or excl
        key = 'unit_price_tax_excl'
        price_unit = record[key]
        return {'price_unit': price_unit}

    @mapping
    def product_id(self, record):
        if int(record.get('product_attribute_id', 0)):
            combination_binder = self.binder_for(
                'prestashop.product.combination'
            )
            product = combination_binder.to_internal(
                record['product_attribute_id'],
                unwrap=True,
            )
        else:
            binder = self.binder_for('prestashop.product.template')
            template = binder.to_internal(record['product_id'], unwrap=True)
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

    @mapping
    def order_id(self, record):
        val = {}
        binder = self.binder_for('prestashop.sale.order.line')
        line = binder.to_internal(record['id'], unwrap=True)
        if line:
            val['order_id'] = line.order_id.id
        return val


class ImportMapChild(Component):
    _name = 'sale.order.child.import'
    _inherit = 'base.map.child.import'
    _usage = 'import.map.child.test'

    def format_items(self, items_values):
        lines = []
        binder = self.binder_for('prestashop.sale.order.line')
        for item in items_values:
            line = binder.to_internal(item['external_id'], unwrap=True)
            if line:
                # item['order_id'] = line.order_id.id
                lines.append((1, line.prestashop_bind_ids.id, item))
            else:
                lines.append((0, 0, item))
        return lines
