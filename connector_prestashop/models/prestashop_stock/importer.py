# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, external_to_m2o
import logging

_logger = logging.getLogger(__name__)


class StockAvailableImportMapper(Component):
    _name = 'prestashop.stock.availbale.mapper'
    _inherit = 'prestashop.import.mapper'
    _apply_on = 'prestashop.stock.available'

    direct = [
        ('quantity', 'quantity'),
        (external_to_m2o('id_product'), 'product_id'),
    ]

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


class StockAvailableImporter(Component):
    _name = 'prestashop.stock.available.importer'
    _inherit = 'prestashop.importer'
    _apply_on = 'prestashop.stock.available'
    _usage = 'prestashop.stock.available.importer'

    def run(self, external_id):
        filters = {'filter[id_product]': '%d' % (int(external_id))}
        record_ids = self.backend_adapter.search(filters)
        for record_id in record_ids:
            _logger.debug(record_id)
            super(StockAvailableImporter, self).run(record_id)

