# Copyright 2011 Catch.com, Inc.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

'''A python interface to the Catch API'''

__author__ = 'ariel@catch.com'
__version__ = '0.5'

import mimetypes, base64, httplib, urllib, os, sys, urlparse, datetime
import simplejson as json

class User(dict):
    """
    A class representing the User structure used by the Catch API.
    """

    def __init__(self, session, *args, **kwds):
        super(User, self).__init__(*args, **kwds)
        self._session = session

    @property
    def access_token(self):
        return self.get('access_token', None)

    @property
    def tags(self):
        data = self._session._request("GET", '/v1/tags.json', body={'access_token': self.access_token})
        for tag in data['tags']:
            tag['modified'] = datetime.datetime.strptime(tag['modified'], '%Y-%m-%dT%H:%M:%S.%fZ')
        return tuple(data['tags'])

    def post_note(self, text, **kwds):
        params = {"text": text}
        params.update(kwds)
        data = self._session._request("POST",
                                      "/v2/notes.json?access_token=%s" % self.access_token,
                                      body=params)
        return Note(self, self._session, data['notes'][0])

    def get_note(self, id):
        data = self._session._request("GET",
                                      "/v2/notes/%s.json" % id,
                                      body={"access_token": self.access_token})
        return Note(self, self._session, data['notes'][0])

    @property
    def notes(self):
        class NoteIterator:
            def __init__(self, user):
                self._user = user
                self._offset = 0
                self._limit = 100
                self._count = -1
                self._next_batch()

            def __len__(self): return self._count
            def __iter__(self): return self

            def next(self):
                if not self._data:
                    self._next_batch()
                return Note(self, self._user._session, self._data.pop(0))

            def _next_batch(self):
                if self._count == 0 or (self._count >= 0 and self._offset > self._count):
                    raise StopIteration
                limit = min(self._count - self._offset, self._limit) if self._count >= 0 else self._limit
                self._data, self._count = self._user.get_notes(offset=self._offset, limit=limit)
                self._offset += self._limit

        return NoteIterator(self)

    def get_notes(self, offset=0, limit=20):
        data = self._session._request("GET", "/v2/notes.json",
                                      body={"offset": offset, "limit": limit, 'full': 'true',
                                            'access_token': self.access_token})
        return [Note(self, self._session, n) for n in data['notes']], data['count']

class Media(dict):

    def __init__(self, user, session, note, *args, **kwds):
        self._user = user
        self._session = session
        self._note = note
        super(Media, self).__init__(*args, **kwds)

    @property
    def deleted(self):
        return self._deleted

    def delete(self):
        data = self._session._request("DELETE", "/v2/media/%s/%s.json" % (self._note['id'], self['id']),
                                      body={"access_token": self._user.access_token})
        # not quite ready for this...
        # "server_modified_at": self['server_modified_at']})
        if data['status'] == 'ok':
            self._note['media'] = (m for m in self._note['media'] if m is not self)
            self._deleted = True
            return True

class Comment(dict):

    def __init__(self, user, session, note, *args, **kwds):
        self._user = user
        self._session = session
        self._note = note
        super(Comment, self).__init__(*args, **kwds)

    @property
    def deleted(self):
        return self._deleted

    def delete(self):
        data = self._session._request("DELETE", "/v2/comment/%s.json" % self['id'],
                                      body={"access_token": self._user.access_token})
        # not quite ready for this...
        # "server_modified_at": self['server_modified_at']})
        if data['status'] == 'ok':
            self._note['comments'] = (c for c in self._note._comments if c is not self)
            self._deleted = True
            return True

class Note(dict):

    def __init__(self, user, session, *args, **kwds):
        self._user = user
        self._session = session
        self._dirty = False
        super(Note, self).__init__(*args, **kwds)
        self['media'] = (Media(self._user, self._session, self) for m in self['media'])

    @property
    def deleted(self):
        return getattr(self, "_deleted", False)

    def delete(self):
        self._session._request("DELETE", "/v2/notes/%s.json" % self['id'],
                               body={"access_token": self._user.access_token,
                                     "server_modified_at": self['server_modified_at']})
        self._deleted = True

    def add_comment(self, **opts):
        data = self._session._request("POST",
                                      "/v2/comments/{id}.json?access_token={token}".format(
                                          id=self['id'],
                                          token=self._user.access_token),
                                      body=opts)
        return Comment(self._user, self._session, self, data['notes'][0])

    @property
    def comments(self):
        if not hasattr(self, "_comments"):
            data = self._session._request("GET",
                                          "/v2/comments/{id}.json".format(id=self['id']),
                                          body={"access_token": self._user.access_token})
            self._comments = [Comment(self._user, self._session, self, c) for c in data['notes']]
        return self._comments

    def edit(self, **kwds):
        kwds.setdefault('server_modified_at', self['server_modified_at'])
        data = self._session._request(
            "POST",
            "/v2/notes/{id}.json?access_token={token}".format(id=self['id'],
                                                              token=self._user.access_token),
            body=kwds)
        self.update(data['notes'][0])

    def add_media(self, filename, **opts):
        BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'

        def multipart(parts):
            L = []
            for (key, fn, value) in parts:
                L.append('--' + BOUNDARY)
                if fn:
                    L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, fn))
                else:
                    L.append('Content-Disposition: form-data; name="%s"' % key)
                content_type = mimetypes.guess_type(fn)[0] or 'application/octet-stream'
                L.append('Content-Type: %s' % content_type)
                L.append('')
                L.append(value)
            L.append('--' + BOUNDARY + '--')
            L.append('')
            return '\r\n'.join(L)

        with open(filename) as body:
            parts = [('data', filename, body.read())]
            parts.extend([(k, None, v) for k, v in opts.iteritems()])
            body = multipart(parts)

        data = self._session._request(
            "POST",
            "/v2/media/{id}.json?access_token={token}".format(id=self['id'],
                                                              token=self._user.access_token),
            body=body,
            headers={'Content-Type': 'multipart/form-data; boundary=%s' % BOUNDARY})

        m = Media(self._user, self._session, self, data)
        self['media'] = tuple(list(self['media']) + [m])
        return m

class CatchSession(object):
    """
    """

    def __init__(self, host="https://api.catch.com", timeout=10):
        self.host = host
        self._timeout = timeout

    @property
    def host(self):
        return "%s://%s" % ({80: "http", 443: "https"}[self._api_port], self._api_host)

    @host.setter
    def host(self, host):
        host = urlparse.urlsplit(host)
        self._api_host = host.netloc
        self._api_port = {"http": 80, "https": 443}[host.scheme]
        self._conn_class = {"http": httplib.HTTPConnection,
                            "https": httplib.HTTPSConnection}[host.scheme]

    def _request(self, method, url, body=None, headers=None):
        headers = headers or {}
        headers.setdefault('User-Agent', self._user_agent)
        if isinstance(body, dict):
            if method in ("GET", "DELETE"):
                url = "%s%s%s" % (url, "&" if "?" in url else "?", urllib.urlencode(body, doseq=True))
                body = None
            else:
                headers.setdefault('Content-Type', 'application/x-www-form-urlencoded')
                body = urllib.urlencode(body, doseq=True)
        headers.setdefault("Content-Length", len(body or ""))

        conn = self._conn_class(self._api_host, self._api_port)
        conn.request(method, url, body=body, headers=headers)
        response = conn.getresponse()
        data = json.loads(response.read())
        conn.close()
        return data

    def login(self, username, password):
        data = self._request("POST", "/v2/user", headers={
            'Authorization': "Basic %s" % base64.standard_b64encode(":".join((username, password)))
        })
        return User(self, data['user'])

    @property
    def _user_agent(self):
        return ' '.join(("python", "catch.api-%s" % __version__))
