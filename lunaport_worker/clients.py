# -*- encoding: utf-8 -*-
"""
    lunaport_worker.clients
    ~~~~~~~~~~~~~~~~~~~~~~~

    Client libs for 3rd party services interaction.
    Issue trackers: JIRA, Star track.
"""

import os
import socket
from functools import wraps
import re
import json
import marshal
import pprint
pp = pprint.PrettyPrinter(indent=4).pprint

import requests
from requests import Request, Session

from . import __version__

url_auth_regex = re.compile(r"[a-zA-Z:_]*@", re.IGNORECASE)


class BaseClinetError(Exception):
    def __init__(self, msg, url=None, status_code=None, resp_body=None,
                 orig_e=None):
        self.orig_e = orig_e
        self.msg = msg
        self.url = url
        self.status_code = status_code
        self.resp_body = resp_body

    def __str__(self):
        result = [self.msg]
        if self.url:
            result.append('URL:{}'.format(self.url))
        if self.status_code:
            result.append('HTTP STATUS CODE:{}'.format(self.status_code))
        if self.resp_body:
            try:
                result.append('RESP BODY:{}'.format(self.resp_body))
            except UnicodeEncodeError:
                pass

        return repr(';'.join(result))


def panic(e=None, resp=None, text=None, exc=BaseClinetError):
    msg = ''
    kw = {}

    if text:
        msg += text
    if e:
        msg += str(e)
        kw['orig_e'] = e

    if resp is None:
        raise exc(msg, **kw)

    if getattr(resp, 'url', None):
        kw['url'] = url_auth_regex.sub(':<>@', resp.url)

    raise exc(msg, **kw)


class JIRARESTClinet(object):
    """HTTP client for both APIs: KSHM and Tank.

        Attributes:
            base: str, base uri for querying.
            to: float, HTTP request time out.
    """
    __version__ = __version__
    _endpoint_tmpl = 'https://{}/rest/api/latest/'

    def __init__(self, fqdn='jira.host',
                 endpoint_tmpl=None, to=10.0, oauth=None):
        self.to = to
        self.fqdn = fqdn
        self.endpoint_tmpl = endpoint_tmpl or self._endpoint_tmpl
        self.oauth = oauth
        self.s = Session()

    def compose_endpoint(f):
        """
        Check the required parameters, generate API endpoint addr
        like http://api.host.org/api/v2.1
        First f positional argument shud be class instance(aka self),
        so don't use this decorator with static methods.

        :param f:
            function obj to wrap.

        :return: function obj with modified params: `to`, `endpoint`.
        """
        @wraps(f)
        def decorated(*args, **kw):
            self = args[0]

            to = kw.get('to', None) or self.to
            assert to, '*to* - Time out parameter missing'
            fqdn = kw.get('fqdn', None) or self.fqdn
            assert fqdn, '*fqdn* - domain name parameter missing'
            endpoint_tmpl = kw.get('endpoint_tmpl', None) or self.endpoint_tmpl
            assert endpoint_tmpl, '*endpoint_tmpl* parameter missing'
            oauth = kw.get('oauth', None) or self.oauth
            assert oauth, '*oauth* parameter missing'

            kw.update({
                'endpoint': endpoint_tmpl.format(fqdn),
                'to': to,
                'oauth': oauth,
            })

            if kw.get('fqdn', None):
                del kw['fqdn']  # no more needed. use endpoint param.
            return f(*args, **kw)

        return decorated

    def http_call(self, r, **kw):
        """
        Send HTTP request to remote side, handle common errors(TCP and HTTP
        timeouts, wrongs status codes and deserialization).

        .. seealso::

               `Requests lib responce obj
               <http://www.python-requests.org/en/latest/api/#requests.Response>`_

        :param r:
            `requests.models.Request` object.
        :param to:
            `float`, imeout awaiting http response in seconds.
        :param codes_allowed:
            list of `int`, acceptable HTTP responce status codes.
        :param ret_obj:
            `bool`, return `responce obj` without status code validation if True.

        :return: `responce object`
        """
        try:
            resp = self.s.send(r, timeout=kw.get('to', None))
        except requests.exceptions.ConnectionError, e:
            raise BaseClinetError(
                'Can\'t connect to API host @see orig_e attr for details.',
                url=r.url, orig_e=e)
        except socket.error, e:
            raise BaseClinetError(str(e), url=r.url, orig_e=e)
        except requests.exceptions.Timeout, e:
            raise BaseClinetError(str(e), url=r.url, orig_e=e)

        if kw.get('ret_obj', None):  # return resp without any validations
            return resp

        codes_allowed = kw.get('codes_allowed', None) or [200, ]
        if resp.status_code not in codes_allowed:
            msg = [
                'Wrong HTTP response status code:{}'.format(resp.status_code),
                'acceptable codes list: {}'.format([c for c in codes_allowed])
            ]
            raise BaseClinetError(' '.join(msg), url=r.url,
                                  status_code=resp.status_code,
                                  resp_body=resp.text)
        return resp

    @compose_endpoint
    def issue(self, issue_id, fields=None, to=None, endpoint=None, oauth=None,
              codes_allowed=[200, ], ret_obj=False, **kw):
        """ Retrieve  tank(load generation server) status.
        Args:
            issue_id - str, like SOMEPROJ-123
            to - float, timeout awaiting http response in seconds.
            endpoint - str, API base url.
            oauth - str, oauth token.
            codes_allowed - list of int.
            ret_obj - bool.

        Returns:
            resp - responce object.
        """
        assert all([to, endpoint, oauth])
        url = '{}issue/{}'.format(endpoint, issue_id)
        params = None
        if fields:
            params = {
                'fields': fields,
            }
        hdrs = {
            'Authorization': 'OAuth {}'.format(oauth),
        }
        resp = self.http_call(Request('GET', url, headers=hdrs, params=params).prepare(),
                              to=to, codes_allowed=codes_allowed,
                              ret_obj=ret_obj)
        if callable(resp.json):
            return resp.json()
        return None

    @compose_endpoint
    def proj(self, proj_name, to=None, endpoint=None, oauth=None,
             codes_allowed=[200, ], ret_obj=False, **kw):
        """ Retrieve  tank(load generation server) status.
        Args:
            proj_name - str
            to - float, timeout awaiting http response in seconds.
            endpoint - str, API base url.
            oauth - str, oauth token.
            codes_allowed - list of int.
            ret_obj - bool.

        Returns:
            resp - responce object.
        """
        assert all([to, endpoint, oauth])
        url = '{}project/{}'.format(endpoint, proj_name.upper())
        hdrs = {
            'Authorization': 'OAuth {}'.format(oauth),
        }
        resp = self.http_call(Request('GET', url, headers=hdrs).prepare(),
                              to=to, codes_allowed=codes_allowed,
                              ret_obj=ret_obj)
        if callable(resp.json):
            return resp.json()
        return None

    @compose_endpoint
    def post_comment(self, issue_id, msg, to=None, endpoint=None, oauth=None,
                     codes_allowed=[200, 201], ret_obj=False, **kw):
        """ Retrieve  tank(load generation server) status.
        Args:
            issue_id - str, like SOMEPROJ-123
            to - float, timeout awaiting http response in seconds.
            endpoint - str, API base url.
            oauth - str, oauth token.
            codes_allowed - list of int.
            ret_obj - bool.

        Returns:
            resp - responce object.
        """
        assert all([to, endpoint, oauth])
        url = '{}issue/{}/comment'.format(endpoint, issue_id)
        hdrs = {
            'Authorization': 'OAuth {}'.format(oauth),
            'Content-Type': 'application/json',
            'Accept': '*/*',
        }
        body_json = json.dumps({'body': msg})
        resp = self.http_call(
            Request('POST', url, headers=hdrs, data=body_json).prepare(),
            to=to, codes_allowed=codes_allowed, ret_obj=ret_obj)

        if callable(resp.json):
            return resp.json()
        return None
