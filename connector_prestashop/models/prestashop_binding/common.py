# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, models, fields
from odoo.addons.queue_job.job import job, related_action
# from openerp.addons.connector.session import ConnectorSession
# from ...unit.importer import import_record


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

    # @api.multi
    # def resync(self):
    #     session = ConnectorSession.from_env(self.env)
    #     func = import_record
    #     if self.env.context.get('connector_delay'):
    #         func = import_record.delay
    #     for record in self:
    #         func(session, self._name, record.backend_id.id,
    #              record.prestashop_id)
    #     return True

    @job(default_channel='root.prestashop')
    # @related_action(action='related_action_magento_link')
    @api.model
    def import_batch(self, backend, filters=None):
        """ Prepare the import of records modified on PrestaShop """
        if filters is None:
            filters = {}
        with backend.work_on(self._name) as work:
            importer = work.component(usage='batch.importer')
            return importer.run(filters=filters)

    @job(default_channel='root.prestashop')
    # @related_action(action='related_action_magento_link')
    @api.model
    def import_record(self, backend, external_id, force=False):
        """ Import a PrestaShop record """
        with backend.work_on(self._name) as work:
            importer = work.component(usage='record.importer')
            return importer.run(external_id, force=force)

# class PrestashopBindingOdoo(models.AbstractModel):
#     _name = 'prestashop.binding.odoo'
#     _inherit = 'prestashop.binding'
#     _description = 'PrestaShop Binding with Odoo binding (abstract)'
#
#     def _get_selection(self):
#         records = self.env['ir.model'].search([])
#         return [(r.model, r.name) for r in records] + [('', '')]
#
#     # 'odoo_id': odoo-side id must be re-declared in concrete model
#     # for having a many2one instead of a reference field
#     odoo_id = fields.Reference(
#         required=True,
#         ondelete='cascade',
#         string='Odoo binding',
#         selection=_get_selection,
#     )
#
#     _sql_constraints = [
#         ('prestashop_erp_uniq', 'unique(backend_id, odoo_id)',
#          'An ERP record with same ID already exists on PrestaShop.'),
#     ]
