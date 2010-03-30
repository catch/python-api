# Copyright (c) 2010 Harry Tormey <harry@p2presearch.com>
#
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.


'''A library that provides a python interface to the Snaptic API'''

__author__ = 'harry@p2presearch.com'
__version__ = '0.3-devel'

import mimetypes
import base64
import httplib
import os
import simplejson as json
import sys
from urllib import urlencode
import urlparse

def Property(func):
    return property(**func())

class SnapticError(Exception):
  '''Base class for Snaptic errors'''

  @property
  def message(self):
    '''Returns the first argument used to construct this error.'''
    return self.args[0]

  @property
  def status(self):
    '''Returns the HTTP status code used to construct this error.'''
    return self.args[1]

  @property
  def response(self):
    '''Returns HTTP response body used to construct this error.'''
    return self.args[2]

class User(object):
    '''A class representing the User structure used by the Snaptic API.

     The User structure exposes the following properties:
       user.id
       user.user_name
    '''

    def __init__(self, id=None, user_name=None, created_at=None, auth_token=None, email=None):
        self._id             = id
        self._user_name      = user_name
        self._created_at     = created_at
        self._auth_token     = auth_token
        self._email          = email

    @property
    def id(self):
        return self._id

    @property
    def user_name(self):
        return self._user_name

    @property
    def created_at(self):
        return self._created_at

    @property
    def auth_token(self):
        return self._auth_token

    @property
    def email(self):
        return self._email

#Perhaps I should refactor this into a class hierarchy and subclass for image/sound/etc? -htormey
class Image(object):
    '''A class representing the Image structure which is an attribute of a note retruned via the Snaptic API.

     The Image structure exposes the following properties:
       image.type
       image.md5
       image.id
       image.width
       image.height
       image.src
       image.data
    '''

    def __init__(self, type="image", md5=None, id=None, revision_id=None, width=0, height=0, src=None, data=None):
        self.type           = type
        self.md5            = md5
        self.id             = id
        self.revision_id    = revision_id
        self.width          = width
        self.height         = height
        self.src            = src
        self.data           = data

class Note(object):
    '''A class representing the Note structure used by the Snaptic API.

     The Note structure exposes the following properties:
       note.created_at
       note.modified_at
       note.reminder_at
       note.note_id
       note.text
       note.summary
       note.source
       note.source_url
       note.user
       note.children
       note.media
       note.labels
       note.location
       note.has_media
    '''

    def __init__(self, created_at, modified_at, reminder_at, note_id, text,
                 summary, source, source_url, user, children, media = [], labels = [], location = []):
        self.created_at   = created_at
        self.modified_at  = modified_at
        self.reminder_at  = reminder_at
        self.note_id      = note_id
        self.text         = text
        self.summary      = summary
        self.source       = source
        self.source_url   = source_url
        self.user         = user
        self.children     = children
        self.media        = media
        self.labels       = labels
        self.location     = location

    @property
    def has_media(self):
        return len(self.media) > 0

    @property
    def dictionary(self):
        '''
        return a dictionary version of the note
        '''
        #Working on adding dates/location/media and other fields to this dictionary. Right now you can just update text. -htormey
        return dict(text=self.text)

class Api(object):
    '''A python interface into the Snaptic API

    Example usage:
        To create an instance of the snaptic.Api class with basic authentication:
        >> import snaptic
        >> api = snaptic.Api("username", "password")

        To fetch users notes and print an attribute:
        >> print [n.created_at for n in api.notes]

        ['2010-03-08T17:49:08.850Z', '2010-03-06T20:02:32.501Z', '2010-03-06T01:35:14.851Z', '2010-03-05T04:13:00.616Z', '2010-03-01T00:09:38.566Z', '2010-02-18T04:09:55.471Z', '2010-02-18T02:26:35.990Z', 
        '2010-02-12T23:28:22.612Z', '2010-02-10T03:06:50.590Z', '2010-02-10T06:02:57.068Z', '2010-02-08T05:14:07.000Z', '2010-02-08T02:28:20.391Z', '2010-02-05T06:57:54.323Z', '2010-02-07T07:26:34.469Z', 
        '2010-01-25T02:11:24.075Z', '2010-01-24T23:37:07.411Z']

        To post a note:
        >> r = api.post_note("Harry says snaptic is da bomb")
        >> print r
        {
        "notes":[
            {
            "created_at": "2010-03-30T05:12:15.395Z",
            "modified_at": "2010-03-30T05:12:19.260Z",
            "reminder_at": "",
            "id": "1760036",
            "text": "Harry says snaptic is da bomb",
            "summary": "Harry says snaptic is da bomb",
            "source": "3banana",
            "source_url": "https://snaptic.com/",
            "user": {
                "id": "913202",
                "user_name": "ht"
            },
            "children": "0",
            "labels": {},
            "tags": {},
            "location": {}
            }
        ]}

       To delete a note:
       >> id        = api.notes[1].note_id
       >> api.delete_note(id)

       To add an image to the above note
       >> id        = api.notes[1].note_id
       >> api.load_image_and_add_to_note_with_id("myimage.jpg", id)

       To edit a note:
       >> n[0].text='Harry says coolio'
       >> api.edit_note(n[0])

       To download image data from a note:
       >> api.notes[1].has_media
       True
       >> id = api.notes[1].note_id
       >> d = api.get_image_with_id(id)
       >> filename = "/Users/harrytormey/%s.jpg" % id
       >> fout = open(filename, "wb")
       >> fout.write(d)
       >> fout.close()
    '''

    API_SERVER                  = "api.snaptic.com"
    API_VERSION                 = "v1"
    HTTP_GET                    = "GET"
    HTTP_POST                   = "POST"
    HTTP_DELETE                 = "DELETE"
    API_ENDPOINT_NOTES_JSON     = "/notes.json"
    API_ENDPOINT_NOTES          = "/notes/"
    API_ENDPOINT_IMAGES         = "/images/"
    API_ENDPOINT_IMAGES_VIEW    = "/viewImage.action?viewNodeId="
    API_ENDPOINT_USER_JSON      = "/user.json"

    def __init__(self, username, password=None, url=API_SERVER, use_ssl=True, port=443, timeout=10):
        self._url       = url
        self._use_ssl   = use_ssl
        self._port      = port
        self._timeout   = timeout
        self._user      = None
        self._notes     = None
        self._json      = None
        self.set_credentials(username, password)

    def set_credentials(self, username, password):

        '''
        Set username/password

        Args:
            username: snaptic username
            password: snaptic password
        '''
        self._username = username
        self._password = password

    def load_image_and_add_to_note_with_id(self, filename, id):
        if filename and id:
            try: 
                fin     = open(filename, 'r')
                data    = fin.read()
                self.add_image_to_note_with_id(filename, data, id)
            except IOError:
                raise SnapticError("Error reading filename")
        else:
            raise SnapticError("Error problem occured with one of the variables passed to LoadImageAndAddToNoteWithID, filename: %s, id: %s." % (filename, id))

    def add_image_to_note_with_id(self, filename=None, data=None, id=None):
        if data and id and filename:
            page                = "/" + self.API_VERSION + self.API_ENDPOINT_IMAGES + id +".json"
            return self._post_multi_part(self._url, page, [("image", filename, data)])
        else:
            raise SnapticError("Error problem occured with variables passed to AddImageToNoteWithID filename: %s, id: %s " % (filename, id))

    def _post_multi_part(self, host, selector, files):
        """
        Post files to an http host as multipart/form-data.
        files is a sequence of (name, filename, value) elements for data to be uploaded as files
        Return the server's response page.
        """
        content_type, body = self._encode_multi_part_form_data(files)
        handler = httplib.HTTPConnection(host)
        headers = self._make_basic_auth_headers(self._username, self._password)
        h = {
            'User-Agent': 'INSERT USERAGENTNAME',#Change this to library version? -htormey
            'Content-Type': content_type
            }
        headers.update(h)
        handler.request(self.HTTP_POST, selector, body, headers)
        response = handler.getresponse()
        data     = response.read()
        handler.close()
        if response.status != 200:
            raise SnapticError("Error posting files ", response.status, data)

    def _encode_multi_part_form_data(self, files):
        """
        files is a sequence of (name, filename, value) elements for data to be uploaded as files
        Return (content_type, body) ready for httplib.HTTPConnection instance
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
        return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

    def delete_note(self, id):
        page            = "/" + self.API_VERSION + self.API_ENDPOINT_NOTES + id
        handler         = self._basic_auth_request(page, method=self.HTTP_DELETE)
        response        = handler.getresponse()
        handler.close()
        if response.status != 200:
            data        = response.read()
            raise SnapticError("Http error deleting note", response.status, data)

    def edit_note(self, note=None):
        '''
        edit text/other in the note object then pass it back in to post
        '''
        if note: #Maybe check for attributes like id or is of type note? -htormey
            headers        = { 'Content-type' : "application/x-www-form-urlencoded" }
            params         = urlencode(note.dictionary)
            page           = "/" + self.API_VERSION + self.API_ENDPOINT_NOTES + note.note_id + '.json'
            handle         = self._basic_auth_request(page, headers=headers, method=self.HTTP_POST, params=params)
            response       = handle.getresponse()
            data           = response.read()
            handle.close()
            if response.status != 200:
                raise SnapticError("Http error editing note ", response.status, data)
            return data
        else:
            raise SnapticError("Error editing note, no note value passed")

    def post_note(self, note=None):
        if note: #Update this to use and actual note -htormey
            headers     = { 'Content-type' : "application/x-www-form-urlencoded" }
            params      = urlencode(dict(text=note))
            page        = "/" + self.API_VERSION + self.API_ENDPOINT_NOTES_JSON
            handle      = self._basic_auth_request(page, headers=headers, method=self.HTTP_POST, params=params)
            response    = handle.getresponse()
            data        = response.read()
            handle.close()
            if response.status != 200:
                raise SnapticError("Http error posting note ", response.status, data)
            return data
        else:
            raise SnapticError("Error posting note, no note value passed")

    def get_image_with_id(self, id):
        '''
        Get image data using the following id
        '''
        if id:
            url = self.API_ENDPOINT_IMAGES_VIEW  + id
            return self._fetch_url(url)
        else:
            raise SnapticError("Error user id not set, try calling GetNotes.")

    def get_user_id(self):
        '''
        Get ID of API user.
        '''
        if self._user:
            return self._user.id
        else:
            raise SnapticError("Error user id not set, try calling GetNotes.")

    @Property
    def notes():
        doc = "A parsed list of note objects"
        def fget(self):
            if self._notes:
                return self._notes
            else:
                return self.get_notes()
        return locals()

    def get_notes(self):
        '''
        Get notes and update the cache
        '''
        url          = "/" + self.API_VERSION + self.API_ENDPOINT_NOTES_JSON
        json_notes   = self._fetch_url(url)
        self._notes  = self._parse_notes(json_notes)
        return self._notes

    def get_user(self):
        '''
        Get user info
        '''
        url          = "/" + self.API_VERSION + self.API_ENDPOINT_USER_JSON
        user_info    = self._fetch_url(url)
        self._parse_user_info(user_info)
        return self._user

    @Property
    def json():
        doc = "Json object of notes stored in account"
        def fget(self):
            if self._json:
                return self._json #should I return json.load(sef._json) ? -htormey
            else:
                return self.get_json()
        return locals()

    def get_json(self):
        '''
        Get json object and update the cache
        '''
        url         = "/" + self.API_VERSION + self.API_ENDPOINT_NOTES_JSON
        self._json  = self._fetch_url(url)
        return self._json

    def _fetch_url(self, url):
        handler       = self._basic_auth_request(url)
        response      = handler.getresponse()
        data          = response.read()
        handler.close()
        if response.status != 200:
            raise SnapticError("Http error", response.status, data)
        return data

    def _make_basic_auth_headers(self, username, password):
        if username and password:
            headers = dict(Authorization="Basic %s"
                    %(base64.b64encode("%s:%s" %(username, password))))
        else:
            raise SnapticError("Error making basic auth headers with username: %s, password: %s" % (username, password))
        return headers

    def _basic_auth_request(self, path, method=HTTP_GET, headers={}, params={}):
        ''' Make a HTTP request with basic auth header and supplied method.
        Defaults to operating over SSL. '''
        h           = self._make_basic_auth_headers(self._username, self._password)
        h.update(headers)
        if self._use_ssl:
            handler = httplib.HTTPSConnection
        else:
            handler = httplib.HTTPConnection

        # 'timeout' parameter is only available in Python 2.6+
        if sys.version_info[:2] < (2, 6):
            conn = handler(self._url, self._port)
        else:
            conn = handler(self._url, self._port, timeout=self._timeout)
        conn.request(method, path, params, headers=h)
        return conn

    def _parse_user_info(self, source):
        '''
        parse JSON user returned from snaptic, instantiate a User object from it.
        '''
        user_info   = json.loads(source)

        if 'user' in user_info:
            self._user = User(user_info['user']['id'], user_info['user']['user_name'], user_info['user']['created_at'], user_info['user']['auth_token'], user_info['user']['email'])
        else:
            SnapticError("Error no user key found in source JSON passed to _parse_user_info")

    def _parse_notes( self, source, get_image_data=False):
        '''
        parse JSON notes returned from snaptic, instantiate a list of note objects from it.
        '''
        notes       = []
        json_notes  = json.loads(source)

        for note in json_notes['notes']:
            media           = []
            location        = []
            labels          = []
            user            = None
            source          = None

            if 'id' in note:
                if 'user' in note:
                    if self._user == None:
                        self. get_user()
                        user = self._user.id
                    user = self._user.id
                if 'location' in note:
                    pass 
                if 'labels' in note:
                    labels = []
                    for label in note['labels']:
                        labels.append(label)
                if 'media' in note:
                    for item in note['media']:
                        if item['type'] == 'image':
                            image_data = None
                            if get_image_data:
                                image_data = self._fetch_url(item['src'])
                            media.append(Image(item['type'], item['md5'], item['id'], item['revision_id'], item['width'], item['height'], item['src'], image_data))

                notes.append(Note(note['created_at'], note['modified_at'], note['reminder_at'], note['id'], note['text'], note['summary'], note['source'], 
                                note['source_url'], user, note['children'], media, labels, location))
        return notes
