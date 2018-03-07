# -*- coding: utf-8 -*-
# © 2013 Guewen Baconnier,Camptocamp SA,Akretion
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent


class PrestaShopImportMapper(AbstractComponent):
    _name = 'prestashop.import.mapper'
    _inherit = ['base.prestashop.connector', 'base.import.mapper']
    _usage = 'import.mapper'


class PrestaShopExportMapper(AbstractComponent):
    _name = 'prestashop.export.mapper'
    _inherit = ['base.prestashop.connector', 'base.export.mapper']
    _usage = 'export.mapper'


def normalize_boolean(field):
    def modifier(self, record, to_attr):
        if record[field] == '0':
            return False
        return True
    return modifier
