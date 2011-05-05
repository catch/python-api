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

class CatchError(Exception):
    """
    Base class for Catch errors.

    The SnaptiError class exposes the following properties::

        catch_error.message # read only
        catch_error.status # read only
        catch_error.response # read only
    """

    @property
    def message(self):
        """Returns the first argument used to construct this error."""
        return self.args[0]

    @property
    def status(self):
        """Returns the HTTP status code used to construct this error."""
        return self.args[1]

    @property
    def response(self):
        """Returns HTTP response body used to construct this error."""
        return self.args[2]

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

#Perhaps I should refactor this into a class hierarchy and subclass for image/sound/etc? -htormey
class Image(object):
    """
    A class representing the Image structure which is an attribute of a note retruned via the Catch API.

     The Image structure exposes the following properties::

        image.type
        image.md5
        image.id
        image.width
        image.height
        image.src
        image.data
    """

    def __init__(self, type="image", md5=None, id=None, revision_id=None, width=0, height=0, src=None, data=None):
        self.type           = type
        self.md5            = md5
        self.id             = id
        self.revision_id    = revision_id
        self.width          = width
        self.height         = height
        self.src            = src
        self.data           = data

class Note(dict):
    """
    """

    def __init__(self, user, session, *args, **kwds):
        self._user = user
        self._session = session
        self._dirty = False
        super(Note, self).__init__(*args, **kwds)

    @property
    def deleted(self):
        return getattr(self, "_deleted", False)

    def delete(self):
        self._session._request("DELETE", "/v2/notes/%s.json" % self['id'],
                               body={"access_token": self._user.access_token,
                                     "server_modified_at": self['server_modified_at']})
        self._deleted = True

    def edit(self, **kwds):
        kwds.setdefault('server_modified_at', self['server_modified_at'])
        data = self._session._request(
            "POST",
            "/v2/notes/{id}.json?access_token={token}".format(id=self['id'],
                                                              token=self._user.access_token),
            body=kwds)
        self.update(data['notes'][0])

    @property
    def has_media(self):
        """
        Check to see if Note has any media (images) associated with it.

        Returns:
            True/False
        """
        return len(self.media) > 0

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

    def load_image_and_add_to_note_with_id(self, filename, id):
        """
        Load image from filename and append to note.

        Args::

            filename: filename of image to load data from.
            id: id of note to which image will be appended.
        """
        try:
            fin     = open(filename, 'r')
            data    = fin.read()
            self.add_image_to_note_with_id(filename, data, id)
        except IOError:
            raise CatchError("Error reading filename")

    def add_image_to_note_with_id(self, filename, data, id):
        """
        Add image data to note.

        Args::

            filename: filename of image.
            data: loaded image data to be appended to note.
            id: id of note to which image data will be appended.

        Returns:
            The server's response page.
        """
        page = "/v1/images/%s.json" % str(id)
        return self._post_multi_part(self._url, page, [("image", filename, data)])

    @property
    def _user_agent(self):
        return ' '.join(("python", "catch.api-%s" % __version__))

    def _post_multi_part(self, host, selector, files):
        """
        Post files to an http host as multipart/form-data.

        Args::

            host: server to send request to
            selector: API endpoint to send to the server
            files: sequence of (name, filename, value) elements for data to be uploaded as files

        Returns:
            Return the server's response page.
        """
        content_type, body = self._encode_multi_part_form_data(files)
        handler = httplib.HTTPConnection(host)
        headers = self._get_auth_headers()
        h = {'User-Agent': self._user_agent, 'Content-Type': content_type}
        headers.update(h)
        handler.request("POST", selector, body, headers)
        response = handler.getresponse()
        data     = response.read()
        handler.close()
        if response.status != 200:
            raise CatchError("Error posting files ", response.status, data)

    def _encode_multi_part_form_data(self, files):
        """
        Encode multi part form data to be posted to server.

        Args:
            Files is a sequence of (name, filename, value) elements for data to be uploaded as files
        Return:
            sequence of (content_type, body) ready for httplib.HTTPConnection instance
        """
        BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'
        CRLF = '\r\n'
        L = []
        for (key, filename, value) in files:
            L.append('--' + BOUNDARY)
            L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
            L.append('Content-Type: %s' % self._get_content_type(filename))
            L.append('')
            L.append(value)
        L.append('--' + BOUNDARY + '--')
        L.append('')
        body = CRLF.join(L)
        content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
        return content_type, body

    def _get_content_type(self, filename):
        """
        Attempt to guess mimetype of file.

        Args:
            filename: filename to be guessed.
        Returns:
            File type or default value.
        """
        return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

    def get_image_with_id(self, id):
        """
        Get image data associated with a given id.

        Args:
            id: id of image to be fetched.
        Returns:
            Data associated with image id.
        """
        url = "/viewImage.action?viewNodeId=%s" % str(id)
        return self._fetch_url(url)

    def get_user_id(self):
        """
        Get ID of API user.

        Returns:
            Id of catch user associated with API instance.
        """
        if self._user:
            return self._user.id
        else:
            raise CatchError("Error user id not set, try calling GetNotes.")
