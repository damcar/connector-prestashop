# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp
from odoo.addons.component.core import Component
from odoo.addons.queue_job.job import job
import logging

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.product.template',
        inverse_name='odoo_id',
        copy=False,
        string='PrestaShop Bindings',
    )

    def recompute_price(self):
        self.ensure_one()
        for variant in self.product_variant_ids:
            if variant.default_on:
                base_price = variant.list_price - variant.impact_price
                self.list_price = base_price

    @api.multi
    def update_prestashop_quantities(self):
        for template in self:
            # Recompute product template PrestaShop qty
            template.mapped('prestashop_bind_ids').recompute_prestashop_qty()
            # Recompute variant PrestaShop qty
            template.mapped(
                'product_variant_ids.prestashop_bind_ids'
            ).recompute_prestashop_qty()
        return True


class PrestashopProductTemplate(models.Model):
    _name = 'prestashop.product.template'
    _inherit = 'prestashop.binding'
    _inherits = {'product.template': 'odoo_id'}

    odoo_id = fields.Many2one(
        comodel_name='product.template',
        required=True,
        ondelete='cascade',
        string='Template',
        oldname='openerp_id',
    )
    # TODO FIXME what name give to field present in
    # prestashop_product_product and product_product
    always_available = fields.Boolean(
        string='Active',
        default=True,
        help='If checked, this product is considered always available')
    description_html = fields.Html(
        string='Description',
        translate=True,
        help="HTML description from PrestaShop",
    )
    description_short_html = fields.Html(
        string='Short Description',
        translate=True,
    )
    date_add = fields.Datetime(
        string='Created at (in PrestaShop)',
        readonly=True
    )
    date_upd = fields.Datetime(
        string='Updated at (in PrestaShop)',
        readonly=True
    )
    default_shop_id = fields.Many2one(
        comodel_name='prestashop.shop',
        string='Default shop',
        required=True
    )
    link_rewrite = fields.Char(
        string='Friendly URL',
        translate=True,
    )
    available_for_order = fields.Boolean(
        string='Available for Order Taking',
        default=True,
    )
    combinations_ids = fields.One2many(
        comodel_name='prestashop.product.combination',
        inverse_name='template_id',
        string='Combinations'
    )
    on_sale = fields.Boolean(string='Show on sale icon')
    wholesale_price = fields.Float(
        string='Cost Price',
        digits=dp.get_precision('Product Price'),
    )

    @job(default_channel='root.prestashop')
    @api.multi
    def export_record(self, external_id, fields=None):
        """ Export a record on Prestashop """
        self.ensure_one()
        with self.backend_id.work_on('prestashop.stock.available') as work:
            exporter = work.component(usage='prestashop.stock.available.exporter')
            return exporter.run(self, external_id, fields)

    @api.multi
    def recompute_prestashop_qty(self):
        for product_binding in self:
            new_qty = product_binding._prestashop_qty()
            _logger.debug('&&&&&&&&&&')
            _logger.debug('odoo id: %s' % self.odoo_id)
            prestashop_stock = self.env['prestashop.stock.available'].search([('product_id', '=', self.odoo_id.id)])
            if prestashop_stock:
                _logger.debug('Prestashop stock obj: %s' % prestashop_stock)
                external_id = prestashop_stock.external_id
                _logger.debug('Prestashop stock external id: %s' % external_id)
                _logger.debug('&&&&&&&&&&')
                product_binding.export_record(external_id, {'quantity':new_qty})
                prestashop_stock.write({
                    'quantity': new_qty
                })
            else:
                _logger.error('Prestashop stock available for Odoo id: %s' % self.odoo_id.id)
        return True

    def _prestashop_qty(self):
        locations = self.env['stock.location'].search(
            [('id', 'child_of', self.backend_id.warehouse_id.lot_stock_id.id),
             ('usage', '=', 'internal')]
        )
        return self.with_context(location=locations.ids).qty_available


class TemplateAdapter(Component):
    _name = 'prestashop.product.template.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.product.template'

    _prestashop_model = 'products'
