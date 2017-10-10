# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo import fields, _
from odoo.addons.component.core import AbstractComponent, Component
from odoo.addons.connector.exception import IDMissingInBackend
from odoo.addons.queue_job.exception import NothingToDoJob, RetryableJobError, FailedJobError


_logger = logging.getLogger(__name__)


class PrestaShopImporter(AbstractComponent):
    """ Base importer for PrestaShop """

    _name = 'prestashop.importer'
    _inherit = ['base.importer', 'base.prestashop.connector']
    _usage = 'record.importer'

    def __init__(self, work_context):
        """
        :param environment: current environment (backend, session, ...)
        :type environment: :py:class:`connector.connector.ConnectorEnvironment`
        """
        super(PrestaShopImporter, self).__init__(work_context)
        self.external_id = None
        self.prestashop_record = None

    def _get_prestashop_data(self):
        """ Return the raw prestashop data for ``self.prestashop_id`` """
        return self.backend_adapter.read(self.external_id)

    def _before_import(self):
        """ Hook called before the import, when we have the PrestaShop
        data"""
        return

    def _import_dependency(self, external_id, binding_model,
                           importer=None, always=False,
                           **kwargs):
        """
        Import a dependency. The importer class is a subclass of
        ``PrestashopImporter``. A specific class can be defined.

        :param prestashop_id: id of the prestashop id to import
        :param binding_model: name of the binding model for the relation
        :type binding_model: str | unicode
        :param importer_cls: :py:class:`openerp.addons.connector.\
                                        connector.ConnectorUnit`
                             class or parent class to use for the export.
                             By default: PrestashopImporter
        :type importer_cls: :py:class:`openerp.addons.connector.\
                                       connector.MetaConnectorUnit`
        :param always: if True, the record is updated even if it already
                       exists,
                       it is still skipped if it has not been modified on
                       PrestaShop
        :type always: boolean
        :param kwargs: additional keyword arguments are passed to the importer
        """
        if not external_id:
            return
        binder = self.binder_for(binding_model)
        if always or not binder.to_internal(external_id):
            if importer is None:
                importer = self.component(usage='record.importer',
                                          model_name=binding_model)
            try:
                importer.run(external_id)
            except NothingToDoJob:
                _logger.info(
                    'Dependency import of %s(%s) has been ignored.',
                    binding_model._name, external_id
                )

    def _import_dependencies(self):
        """ Import the dependencies for the record"""
        return

    def _map_data(self, data):
        """ Returns an instance of
        :py:class:`~openerp.addons.connector.unit.mapper.MapRecord`

        """
        return self.mapper.map_record(data)

    def _validate_data(self, data):
        """ Check if the values to import are correct

        Pro-actively check before the ``Model.create`` or
        ``Model.update`` if some fields are missing

        Raise `InvalidDataError`
        """
        return

    def _has_to_skip(self):
        """ Return True if the import can be skipped """
        return False

    def _get_binding(self):
        """Return the openerp id from the prestashop id"""
        return self.binder.to_internal(self.external_id)

    def _create_data(self, map_record, **kwargs):
        return map_record.values(for_create=True, **kwargs)

    def _create(self, data):
        """ Create the OpenERP record """
        # special check on data before import
        self._validate_data(data)
        model = self.model.with_context(connector_no_export=True)
        binding = model.create(data)
        _logger.debug('%d created from prestashop %s', binding, self.external_id)
        return binding

    def _update_data(self, map_record, **kwargs):
        return map_record.values(**kwargs)

    def _update(self, binding, data):
        """ Update an OpenERP record """
        # special check on data before import
        self._validate_data(data)
        binding.with_context(connector_no_export=True).write(data)
        _logger.debug('%d updated from prestashop %s', binding, self.external_id)
        return

    def _after_import(self, binding):
        """ Hook called at the end of the import """
        return

    def run(self, external_id, force=False):
        """ Run the synchronization

        :param prestashop_id: identifier of the record on PrestaShop
        """
        self.external_id = external_id
        lock_name = 'import({}, {}, {}, {})'.format(
            self.backend_record._name,
            self.backend_record.id,
            self.work.model_name,
            self.external_id,
        )

        try:
            self.prestashop_record = self._get_prestashop_data()
        except IDMissingInBackend:
            return _('Record does no longer exist in Magento')
        #################################
        # languages
        # find the translatable fields of the model
        self.main_lang_data = self.prestashop_record
        self.default_language = self.backend_record.get_default_language().code
        self.other_langs_data = None
        # fields = self.model.fields_get()
        # translatable_fields = [field for field, attrs in fields.iteritems()
        #                        if attrs.get('translate')]
        # _fields = self._translatable_fields[model_name]
        # translatable_fields = [x for x in self._translatable_fields]
        # print(translatable_fields)
        # frerer
        languages = self.backend_record.get_all_languages()
        if self._translatable_fields:
            split_record = {}
            if not languages:
                raise FailedJobError(
                    _('No language mapping defined. '
                      'Run "Synchronize base data".')
                )
            for language_id, language_code in languages.iteritems():
                split_record[language_code] = self.prestashop_record.copy()
            # _fields = self._translatable_fields[model_name]
            # if fields:
            #     _fields = [x for x in _fields if x in fields]
            print(self._translatable_fields)
            for field in self._translatable_fields:
                for language in self.prestashop_record[field]['language']:
                    current_id = int(language['attrs']['id'])
                    code = languages.get(current_id)
                    # if not code:
                        # TODO: be nicer here.
                        # Currently if you have a language in PS
                        # that is not present in odoo
                        # the basic metadata sync is broken.
                        # We should present skip the language
                        # and maybe show a message to users.
                        # raise FailedJobError(
                        #     _('No language could be found for the Prestashop lang '
                        #       'with id "%s". Run "Synchronize base data" again.') %
                        #     (current_id,)
                        # )
                    if code:
                        split_record[code][field] = language['value']
            self.main_lang_data = split_record[self.default_language]
            if self.default_language in split_record:
                del split_record[self.default_language]
            self.other_langs_data = split_record
        #################################
        skip = self._has_to_skip()
        if skip:
            return skip

        binding = self._get_binding()

        # if not force and self._is_uptodate(binding):
        #     return _('Already up-to-date.')

        # Keep a lock on this import until the transaction is committed
        # The lock is kept since we have detected that the informations
        # will be updated into Odoo
        self.advisory_lock_or_retry(lock_name)
        self._before_import()

        # import the missing linked resources
        self._import_dependencies()

        map_record = self._map_data(self.main_lang_data)

        if binding:
            record = self._update_data(map_record)
            self._update(binding, record)
        else:
            record = self._create_data(map_record)
            binding = self._create(record)

        self.binder.bind(self.external_id, binding)

        ###
        if self.other_langs_data:
            for lang_code, lang_record in self.other_langs_data.iteritems():
                map_record = self._map_data(lang_record)
                data = self._update_data(map_record)
                binding.with_context(lang=lang_code, connector_no_export=True).write(data)
                # binding.with_context(
                #     lang=lang_code,
                #     connector_no_export=True,
                # ).write(map_record.values())
        ###

        self._after_import(binding)


class BatchImporter(AbstractComponent):
    """ The role of a BatchImporter is to search for a list of
    items to import, then it can either import them directly or delay
    the import of each item separately.
    """

    _name = 'prestashop.batch.importer'
    _inherit = ['base.importer', 'base.prestashop.connector']
    _usage = 'batch.importer'

    page_size = 1000

    def run(self, filters=None, **kwargs):
        """ Run the synchronization """
        if filters is None:
            filters = {}
        if 'limit' in filters:
            self._run_page(filters, **kwargs)
            return
        page_number = 0
        filters['limit'] = '%d,%d' % (
            page_number * self.page_size, self.page_size)
        record_ids = self._run_page(filters, **kwargs)
        while len(record_ids) == self.page_size:
            page_number += 1
            filters['limit'] = '%d,%d' % (
                page_number * self.page_size, self.page_size)
            record_ids = self._run_page(filters, **kwargs)

    def _run_page(self, filters, **kwargs):
        record_ids = self.backend_adapter.search(filters)

        for record_id in record_ids:
            self._import_record(record_id, **kwargs)
        return record_ids

    def _import_record(self, external_id):
        """ Import a record directly or delay the import of the record.

        Method to implement in sub-classes.
        """
        raise NotImplementedError


class DirectBatchImporter(AbstractComponent):
    """ Import the records directly, without delaying the jobs. """

    _name = 'prestashop.direct.batch.importer'
    _inherit = 'prestashop.batch.importer'

    def _import_record(self, external_id):
        """ Import the record directly """
        self.model.import_record(self.backend_record, external_id)


class DelayedBatchImporter(AbstractComponent):
    """ Delay import of the records """

    _name = 'prestashop.delayed.batch.importer'
    _inherit = 'prestashop.batch.importer'

    def _import_record(self, external_id, job_options=None, **kwargs):
        """ Delay the import of the records"""
        delayable = self.model.with_delay(**job_options or {})
        delayable.import_record(self.backend_record, external_id, **kwargs)


# class TranslationImporter(Component):
#     _name = 'prestashop.translation.importer'
#     _inherit = 'prestashop.importer'
#     _usage = 'translation.importer'
#
#     def _get_magento_data(self, storeview_id=None):
#         """ Return the raw Magento data for ``self.external_id`` """
#         return self.backend_adapter.read(self.external_id, storeview_id)
#
#     def run(self, external_id, binding, mapper=None):
#         self.external_id = external_id
#         storeviews = self.env['magento.storeview'].search(
#             [('backend_id', '=', self.backend_record.id)]
#         )
#         default_lang = self.backend_record.default_lang_id
#         lang_storeviews = [sv for sv in storeviews
#                            if sv.lang_id and sv.lang_id != default_lang]
#         if not lang_storeviews:
#             return
        # print('**********************************************************')
        # print(self.prestashop_record)
        # find the translatable fields of the model
        # fields = self.model.fields_get()
        # translatable_fields = [field for field, attrs in fields.iteritems()
        #                        if attrs.get('translate')]
        # if mapper is None:
        #     mapper = self.mapper
        # else:
        #     mapper = self.component_by_name(mapper)

        # for storeview in lang_storeviews:
        #     lang_record = self._get_magento_data(storeview.external_id)
        #     map_record = mapper.map_record(lang_record)
        #     record = map_record.values()
        #
        #     data = dict(
        #         (field, value) for field, value in record.iteritems()
        #         if field in translatable_fields)
        #
        #     binding.with_context(connector_no_export=True,
        #                          lang=storeview.lang_id.code).write(data)
