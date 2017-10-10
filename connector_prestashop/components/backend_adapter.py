# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import socket
import logging
import xmlrpclib

from odoo.addons.component.core import AbstractComponent
from odoo.addons.queue_job.exception import RetryableJobError
from odoo.addons.connector.exception import NetworkRetryableError
from datetime import datetime

_logger = logging.getLogger(__name__)

try:
    from prestapyt import PrestaShopWebServiceDict, PrestaShopWebServiceError
except:
    _logger.debug("Cannot import 'prestapyt'")


class PrestaShopLocation(object):

    def __init__(self, location, webservice_key):
        self._location = location
        self.webservice_key = webservice_key

    @property
    def location(self):
        location = self._location
        if not location.endswith('/api'):
            location = location + '/api'
        if not location.startswith('http'):
            location = 'http://' + location
        return location


class PrestaShopAPI(object):

    def __init__(self, location):
        """
        :param location: PrestaShop location
        :type location: :class:`PrestaShopLocation`
        """
        self._location = location
        self._api = None

    @property
    def api(self):
        if self._api is None:
            api = PrestaShopWebServiceDict(
                self._location.location,
                self._location.webservice_key,
            )
            # api.__enter__()
            self._api = api
        return self._api

    def __enter__(self):
        # we do nothing, api is lazy
        print('--enter--')
        return self

    def __exit__(self, type, value, traceback):
        print('--exit--')
        # if self._api is not None:
        #     self._api.__exit__(type, value, traceback)
#
#     def test(self):
#         result = self.api.head('', resource_id=None)

    def call(self, method, model, **kwargs):
        result = getattr(self.api, method)(model, **kwargs)
        return result


    # def call(self, method, arguments):
    #     try:
    #         # When Magento is installed on PHP 5.4+, the API
    #         # may return garble data if the arguments contain
    #         # trailing None.
    #         if isinstance(arguments, list):
    #             while arguments and arguments[-1] is None:
    #                 arguments.pop()
    #         start = datetime.now()
    #         try:
    #             result = self.api.call(method, arguments)
    #         except:
    #             _logger.error("api.call('%s', %s) failed", method, arguments)
    #             raise
    #         else:
    #             _logger.debug("api.call('%s', %s) returned %s in %s seconds",
    #                           method, arguments, result,
    #                           (datetime.now() - start).seconds)
    #         # Uncomment to record requests/responses in ``recorder``
    #         # record(method, arguments, result)
    #         return result
    #     except (socket.gaierror, socket.error, socket.timeout) as err:
    #         raise NetworkRetryableError(
    #             'A network error caused the failure of the job: '
    #             '%s' % err)
    #     except xmlrpclib.ProtocolError as err:
    #         if err.errcode in [502,   # Bad gateway
    #                            503,   # Service unavailable
    #                            504]:  # Gateway timeout
    #             raise RetryableJobError(
    #                 'A protocol error caused the failure of the job:\n'
    #                 'URL: %s\n'
    #                 'HTTP/HTTPS headers: %s\n'
    #                 'Error code: %d\n'
    #                 'Error message: %s\n' %
    #                 (err.url, err.headers, err.errcode, err.errmsg))
    #         else:
    #             raise


class PrestaShopCRUDAdapter(AbstractComponent):
    """ External Records Adapter for PrestaShop """

    _name = 'prestashop.crud.adapter'
    _inherit = ['base.backend.adapter', 'base.prestashop.connector']
    _usage = 'backend.adapter'

    # def __init__(self, work_context):
    #     """
    #
    #     :param environment: current environment (backend, session, ...)
    #     :type environment: :py:class:`connector.connector.ConnectorEnvironment`
    #     """
    #     super(PrestaShopCRUDAdapter, self).__init__(work_context)
    #     self.prestashop = PrestaShopLocation(
    #         self.backend_record.location.encode(),
    #         self.backend_record.webservice_key
    #     )
    #     self.client = PrestaShopWebServiceDict(
    #         self.prestashop.api_url,
    #         self.prestashop.webservice_key,
    #     )

    def search(self, filters=None):
        """ Search records according to some criterias
        and returns a list of ids """
        raise NotImplementedError

    def read(self, id, attributes=None):
        """ Returns the information of a record """
        raise NotImplementedError

    def search_read(self, filters=None):
        """ Search records according to some criterias
        and returns their information"""
        raise NotImplementedError

    def create(self, data):
        """ Create a record on the external system """
        raise NotImplementedError

    def write(self, id, data):
        """ Update records on the external system """
        raise NotImplementedError

    def delete(self, id):
        """ Delete a record on the external system """
        raise NotImplementedError

    def head(self, id=None):
        """ Head """
        raise NotImplementedError

    def _call(self, method, model, **kwargs):
        try:
            prestashop_api = getattr(self.work, 'prestashop_api')
        except AttributeError:
            raise AttributeError(
                'You must provide a prestashop_api attribute with a '
                'PrestaShopAPI instance to be able to use the '
                'Backend Adapter.'
            )
        return prestashop_api.call(method, model, **kwargs)


class GenericAdapter(AbstractComponent):

    _name = 'prestashop.adapter'
    _inherit = 'prestashop.crud.adapter'
    _prestashop_model = None

    def search(self, filters=None):
        """ Search records according to some criterias
        and returns a list of ids

        :rtype: list
        """
        _logger.debug(
            'method search, model %s, filters %s',
            self._prestashop_model, unicode(filters))
        # return self.client.search(self._prestashop_model, filters)
        return self._call('search', self._prestashop_model, options=filters)

    def read(self, id, attributes=None):
        """ Returns the information of a record

        :rtype: dict
        """
        _logger.debug(
            'method read, model %s id %s, attributes %s',
            self._prestashop_model, str(id), unicode(attributes))
        # res = self.client.get(self._prestashop_model, id, options=attributes)
        res = self._call('get', self._prestashop_model, resource_id=id, options=attributes)
        first_key = res.keys()[0]
        return res[first_key]

    def create(self, attributes=None):
        """ Create a record on the external system """
        _logger.debug(
            'method create, model %s, attributes %s',
            self._prestashop_model, unicode(attributes))
        res = self.client.add(self._prestashop_model, {
            self._export_node_name: attributes
        })
        if self._export_node_name_res:
            return res['prestashop'][self._export_node_name_res]['id']
        return res

    def write(self, id, attributes=None):
        """ Update records on the external system """
        attributes['id'] = id
        _logger.debug(
            'method write, model %s, attributes %s',
            self._prestashop_model,
            unicode(attributes)
        )
        res = self.client.edit(
            self._prestashop_model, {self._export_node_name: attributes})
        if self._export_node_name_res:
            return res['prestashop'][self._export_node_name_res]['id']
        return res

    def delete(self, resource, ids):
        _logger.debug('method delete, model %s, ids %s',
                      resource, unicode(ids))
        # Delete a record(s) on the external system
        return self.client.delete(resource, ids)

    def head(self, id=None):
        """ Head """
        return self.client.head(self._prestashop_model, resource_id=id)
        # return self._call()
        # return self._call().head(self._prestashop_model, resource_id=id)
