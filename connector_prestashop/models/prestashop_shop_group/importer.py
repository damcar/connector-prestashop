# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
from odoo.tools.translate import _


class ShopGroupImportMapper(Component):
    _name = 'prestashop.shop.group.mapper'
    _inherit = 'prestashop.import.mapper'
    _apply_on = 'prestashop.shop.group'

    @mapping
    def name(self, record):
        name = record['name']
        if name is None:
            name = _('Undefined')
        return {'name': name}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


class ShopGroupImporter(Component):
    _name = 'prestashop.shop.group.importer'
    _inherit = 'prestashop.importer'
    _apply_on = 'prestashop.shop.group'
