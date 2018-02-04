# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, models, fields
from odoo.addons.queue_job.job import job, related_action
# from openerp.addons.connector.session import ConnectorSession
# from ...unit.importer import import_record
import logging
_logger = logging.getLogger(__name__)


class PrestashopBinding(models.AbstractModel):
    _name = 'prestashop.binding'
    _inherit = 'external.binding'
    _description = 'PrestaShop Binding (abstract)'

    # odoo_id =  odoo-side id must be declared in concrete model
    backend_id = fields.Many2one(
        comodel_name='prestashop.backend',
        string='PrestaShop Backend',
        required=True,
        ondelete='restrict'
    )
    external_id = fields.Integer('ID on PrestaShop')

    _sql_constraints = [
        ('prestashop_uniq', 'unique(backend_id, external_id)',
         'A record with same ID on PrestaShop already exists.'),
    ]

    @job(default_channel='root.prestashop')
    @api.model
    def import_batch(self, backend, filters=None):
        """ Prepare the import of records modified on PrestaShop """
        if filters is None:
            filters = {}
        _logger.debug('IMPORT BATCH')
        _logger.debug('Filters: %s' % filters)
        with backend.work_on(self._name) as work:
            importer = work.component(usage='batch.importer')
            return importer.run(filters=filters)

    @job(default_channel='root.prestashop')
    @api.model
    def import_record(self, backend, external_id, force=False):
        """ Import a PrestaShop record """
        with backend.work_on(self._name) as work:
            importer = work.component(usage='record.importer')
            return importer.run(external_id, force=force)
