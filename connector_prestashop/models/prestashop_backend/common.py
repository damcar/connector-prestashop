# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import models, fields, api, _, exceptions
from odoo.exceptions import UserError
from odoo.addons.connector.models import checkpoint
from contextlib import contextmanager

from ...components.backend_adapter import PrestashopLocation, PrestashopAPI


_logger = logging.getLogger(__name__)


class PrestashopBackend(models.Model):
    _name = 'prestashop.backend'
    _description = 'PrestaShop Backend Configuration'
    _inherit = 'connector.backend'

    @api.model
    def _select_versions(self):
        """ Available versions

        Can be inherited to add custom versions.
        """
        return [
            ('1.5', '< 1.6.0.9'),
            ('1.6.0.9', '1.6.0.9 - 1.6.0.10'),
            ('1.6.0.11', '>= 1.6.0.11 - <1.6.1.2'),
            ('1.6.1.2', '=1.6.1.2')
        ]
    version = fields.Selection(
        selection='_select_versions',
        string='Version',
        required=True,
    )
    location = fields.Char('Location')
    webservice_key = fields.Char(
        string='Webservice key',
        help="You have to put it in 'username' of the PrestaShop "
             "Webservice api path invite"
    )
    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Warehouse',
        required=True,
        help='Warehouse used to compute the stock quantities.'
    )
    stock_location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Stock Location',
        help='Location used to import stock quantities.'
    )
    pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        string='Pricelist',
        required=True,
        default=lambda self: self._default_pricelist_id(),
        help="Pricelist used in sales orders",
    )
    sale_team_id = fields.Many2one(
        comodel_name='crm.team',
        string='Sales Team',
        help="Sales Team assigned to the imported sales orders.",
    )

    refund_journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Refund Journal',
    )
    taxes_included = fields.Boolean("Use tax included prices")
    import_partners_since = fields.Datetime('Import partners since')
    import_orders_since = fields.Datetime('Import Orders since')
    import_carts_since = fields.Datetime('Import Carts since')
    import_products_since = fields.Datetime('Import Products since')
    import_refunds_since = fields.Datetime('Import Refunds since')
    import_suppliers_since = fields.Datetime('Import Suppliers since')
    language_ids = fields.One2many(
        comodel_name='prestashop.res.lang',
        inverse_name='backend_id',
        string='Languages',
        domain=['|', ('active', '=', True), ('active', '=', False)],
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        index=True,
        required=True,
        default=lambda self: self.env['res.company']._company_default_get(
            'prestashop.backend'),
        string='Company',
    )
    discount_product_id = fields.Many2one(
        comodel_name='product.product',
        index=True,
        required=True,
        string='Discount Product',
    )
    shipping_product_id = fields.Many2one(
        comodel_name='product.product',
        index=True,
        required=True,
        string='Shipping Product',
    )
    product_tax_id = fields.Many2one(
        comodel_name='account.tax',
        required=True,
        string='Default Tax on Product',
        domain=[('type_tax_use', '=', 'sale')],
    )

    @api.model
    def _default_pricelist_id(self):
        return self.env['product.pricelist'].search([], limit=1)

    @api.multi
    def get_default_language(self):
        self.ensure_one()
        language = self.language_ids.filtered(lambda r: r.default == True)
        return language.odoo_id

    @api.multi
    def get_all_languages(self):
        self.ensure_one()
        languages = {}
        for lang in self.language_ids:
            languages[lang.external_id] = lang.odoo_id.code
        return languages

    @contextmanager
    @api.multi
    def work_on(self, model_name, **kwargs):
        self.ensure_one()
        lang = self.get_default_language()
        if lang.code != self.env.context.get('lang'):
            self = self.with_context(lang=lang.code)
        prestashop_location = PrestashopLocation(
            self.location,
            self.webservice_key,
        )

        with PrestashopAPI(prestashop_location) as prestashop_api:
            _super = super(PrestashopBackend, self)
            # from the components we'll be able to do: self.work.magento_api
            with _super.work_on(model_name, prestashop_api=prestashop_api, **kwargs) as work:
                yield work

    @api.multi
    def add_checkpoint(self, record, message=""):
        self.ensure_one()
        record.ensure_one()
        return checkpoint.add_checkpoint(self.env, record._name, record.id,
                                         self._name, self.id, message=message)

    @api.multi
    def add_checkpoint_message(self, message):
        self.ensure_one()
        return checkpoint.add_checkpoint_message(self.env, self._name, self.id,
                                                 message)

    @api.multi
    def synchronize_metadata(self):
        try:
            for backend in self:
                for model_name in ('prestashop.shop.group',
                                   'prestashop.shop',
                                   'prestashop.res.lang',):
                    # import directly, do not delay because this
                    # is a fast operation, a direct return is fine
                    # and it is simpler to import them sequentially
                    self.env[model_name].import_batch(backend)
            return True
        except Exception as e:
            _logger.error(e, exc_info=True)
            raise UserError(
                _("Check your configuration, we can't get the data. "
                  "Here is the error:\n%s") % e)

    @api.multi
    def synchronize_basedata(self):
        try:
            for backend in self:
                for model_name in ('prestashop.res.country',
                                   'prestashop.sale.order.state',):
                    # import directly, do not delay because this
                    # is a fast operation, a direct return is fine
                    # and it is simpler to import them sequentially
                    self.env[model_name].import_batch(backend)
            return True
        except Exception as e:
            _logger.error(e, exc_info=True)
            raise UserError(
                _("Check your configuration, we can't get the data. "
                  "Here is the error:\n%s") % e)

    @api.multi
    def import_customers_since(self):
        for backend in self:
            since_date = backend.import_partners_since
            self.env['prestashop.res.partner'].with_delay().import_batch(backend, filters={'since_date': since_date})
            backend.write({'import_partners_since': fields.Datetime.now()})

    @api.multi
    def import_products(self):
        _logger.debug('CALL: import_products')
        for backend in self:
            since_date = backend.import_products_since
            for model_name in ['prestashop.product.template']:
                self.env[model_name].with_delay().import_batch(backend, filters={'since_date': since_date})
            backend.write({'import_products_since': fields.Datetime.now()})

    @api.multi
    def import_carts(self):
        _logger.debug('CALL: import_carts')
        for backend in self:
            since_date = backend.import_carts_since
            for model_name in ['prestashop.cart']:
                self.env[model_name].with_delay().import_batch(backend, filters={'since_date': since_date})
            backend.write({'import_carts_since': fields.Datetime.now()})

    @api.multi
    def import_sale_orders(self):
        _logger.debug('CALL: import_sale_orders')
        for backend in self:
            since_date = backend.import_orders_since
            for model_name in ['prestashop.sale.order']:
                backend.env[model_name].with_delay().import_batch(backend, filters={'since_date': since_date})
            backend.write({'import_orders_since': fields.Datetime.now()})

    # CRON Methods
    @api.model
    def cron_import_all(self):
        _logger.debug('Cron call: import_all')
        backend_ids = self.env['prestashop.backend'].search([])
        backend_ids.import_customers_since()
        backend_ids.import_products()
        backend_ids.import_carts()
        backend_ids.import_sale_orders()

    @api.model
    def cron_import_customers(self):
        _logger.debug('Cron call: import_customers_since')
        backend_ids = self.env['prestashop.backend'].search([])
        backend_ids.import_customers_since()

    @api.model
    def cron_import_products(self):
        _logger.debug('Cron call: import_products')
        backend_ids = self.env['prestashop.backend'].search([])
        backend_ids.import_products()

    @api.model
    def cron_import_carts(self):
        _logger.debug('Cron call: import_carts')
        backend_ids = self.env['prestashop.backend'].search([])
        backend_ids.import_carts()

    @api.model
    def cron_import_sale_orders(self):
        _logger.debug('Cron call: import_sale_orders')
        backend_ids = self.env['prestashop.backend'].search([])
        backend_ids.import_sale_orders()


