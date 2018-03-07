# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import Component
from odoo import _

import logging
_logger = logging.getLogger(__name__)


class StockAvailableExporter(Component):
    _name = 'prestashop.stock.available.exporter'
    _inherit = 'prestashop.exporter'
    _apply_on = 'prestashop.stock.available'
    _usage = 'prestashop.stock.available.exporter'

    def run(self, binding, external_id, fields):
        _logger.debug('#############')
        _logger.debug('Binding: %s' % binding)
        _logger.debug('SELF: %s' % self)
        _logger.debug('external_id: %s' % external_id)
        _logger.debug('export_quantity: %s - %s' % (external_id, fields))
        self.backend_adapter.write(external_id, fields)
        _logger.debug('#############')
        return True
