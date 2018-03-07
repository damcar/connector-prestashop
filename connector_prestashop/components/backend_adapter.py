# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging
import base64
from odoo.addons.component.core import AbstractComponent

_logger = logging.getLogger(__name__)

try:
    from prestapyt import PrestaShopWebServiceDict, PrestaShopWebServiceError
except:
    _logger.debug("Cannot import 'prestapyt'")


class PrestashopWebServiceImage(PrestaShopWebServiceDict):

    def get_image(self, resource, resource_id=None, image_id=None,
                  options=None):
        full_url = self._api_url + 'images/' + resource
        if resource_id is not None:
            full_url += "/%s" % (resource_id,)
            if image_id is not None:
                full_url += "/%s" % (image_id,)
        if options is not None:
            self._validate_query_options(options)
            full_url += "?%s" % (self._options_to_querystring(options),)
        _logger.debug(full_url)
        response = self._execute(full_url, 'GET')
        if response.content:
            image_content = base64.b64encode(response.content)
        else:
            image_content = ''

        record = {
            'type': response.headers['content-type'],
            'content': image_content,
            'id_' + resource[:-1]: resource_id,
            'id_image': image_id,
        }
        record['full_public_url'] = self.get_image_public_url(record)
        return record

    def get_image_public_url(self, record):
        url = self._api_url.replace('/api', '')
        url += 'img/p/' + '/'.join(list(record['id_image']))
        extension = ''
        if record['type'] == 'image/jpeg':
            extension = '.jpg'
        url += '/' + record['id_image'] + extension
        return url


class PrestashopLocation(object):

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


class PrestashopAPI(object):

    def __init__(self, location):
        """
        :param location: Prestashop location
        :type location: :class:`PrestashopLocation`
        """
        self._location = location
        self._api = None

    @property
    def api(self):
        if self._api is None:
            api = PrestashopWebServiceImage(
                self._location.location,
                self._location.webservice_key,
            )
            self._api = api
        return self._api

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self._api = None

    def call(self, method, model, **kwargs):
        _logger.debug(method)
        _logger.debug(model)
        _logger.debug(kwargs)
        result = getattr(self.api, method)(model, **kwargs)
        return result

    def call_update(self, method, model, resource_id, fields):
        _logger.debug(method)
        _logger.debug(model)
        _logger.debug(resource_id)
        _logger.debug(fields)
        result = getattr(self.api, method)(model, resource_id, fields)
        return result

class PrestashopCRUDAdapter(AbstractComponent):
    """ External Records Adapter for PrestaShop """
    _name = 'prestashop.crud.adapter'
    _inherit = ['base.backend.adapter', 'base.prestashop.connector']
    _usage = 'backend.adapter'

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

    def get_image(self, resource_id, image_id, filters=None):
        """ Get image """
        raise NotImplementedError

    def _call(self, method, model, **kwargs):
        try:
            prestashop_api = getattr(self.work, 'prestashop_api')
        except AttributeError:
            raise AttributeError(
                'You must provide a prestashop_api attribute with a '
                'PrestashopAPI instance to be able to use the '
                'Backend Adapter.'
            )
        return prestashop_api.call(method, model, **kwargs)

    def _call_update(self, method, model, resource_id, fields):
        try:
            prestashop_api = getattr(self.work, 'prestashop_api')
        except AttributeError:
            raise AttributeError(
                'You must provide a prestashop_api attribute with a '
                'PrestashopAPI instance to be able to use the '
                'Backend Adapter.'
            )
        return prestashop_api.call_update(method, model, resource_id, fields)


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
            self._prestashop_model, str(filters))
        return self._call('search', self._prestashop_model, options=filters)

    def read(self, id, attributes=None):
        """ Returns the information of a record

        :rtype: dict
        """
        _logger.debug(
            'method read, model %s id %s, attributes %s',
            self._prestashop_model, str(id), str(attributes))
        _logger.debug(self._prestashop_model)
        _logger.debug(id)
        _logger.debug(attributes)
        res = self._call('get', self._prestashop_model, resource_id=id,
                         options=attributes)
        first_key = list(res.keys())[0]
        return res[first_key]

    def create(self, attributes=None):
        """ Create a record on the external system """
        _logger.debug(
            'method create, model %s, attributes %s',
            self._prestashop_model, str(attributes))
        res = self.client.add(self._prestashop_model, {
            self._export_node_name: attributes
        })
        if self._export_node_name_res:
            return res['prestashop'][self._export_node_name_res]['id']
        return res

    def write(self, id, attributes=None):
        """ Update records on the external system """
        _logger.debug(
            'method read, model %s id %s, attributes %s',
            self._prestashop_model, str(id), str(attributes))
        _logger.debug(self._prestashop_model)
        _logger.debug(id)
        _logger.debug(attributes)
        return self._call_update('partial_edit', self._prestashop_model, id, attributes)

    def delete(self, resource, ids):
        _logger.debug('method delete, model %s, ids %s',
                      resource, str(ids))
        # Delete a record(s) on the external system
        return self.client.delete(resource, ids)

    def head(self, id=None):
        """ Head """
        return self.client.head(self._prestashop_model, resource_id=id)

    def get_image(self, resource_id, image_id, filters=None):
        return self._call('get_image', self._prestashop_model,
                          resource_id=resource_id, image_id=image_id,
                          options=filters)
