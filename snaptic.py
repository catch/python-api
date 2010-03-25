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

class SnapticError(Exception):
  '''Base class for Snaptic errors'''

  @property
  def message(self):
    '''Returns the first argument used to construct this error.'''
    return self.args[0]

class User(object):
    '''A class representing the User structure used by the Snaptic API.

     The User structure exposes the following properties:
       user.id
       user.user_name
    '''

    def __init__(self, id=None, user_name=None):
        self.id             = id
        self.user_name      = user_name

    def GetUserName(self):
        '''
        Return user_name
        '''
        if self.user_name:
            return self.user_name
        else:
            raise SnapticError("Error user name not set")

    def SetUserName(self, user_name):
        '''
        Set user_name
        '''
        self.user_name = user_name

    def GetId(self):
        '''
        Return users id
        '''
        if self.id:
            return self.id
        else:
            raise SnapticError("Error user id not set")

    def SetId(self, id):
        '''
        Set users id
        '''
        self.id = id

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

    def SetID(self, id):
        '''
        Set ID of image.
        '''
        self.id = id

    def GetID(self):
        '''
        Return ID of image
        '''
        return self.id

    def SetData(self, data):
        '''
        Set image data.
        '''
        self.data = data

    def GetData(self):
        '''
        Return data so that image can be displayed/written to disk as .jpg.
        If data=None, image data has not yet been fetched.
        '''
        if self.data:
            return data

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

    def NoteHasMedia(self):
        if len(self.media) > 0:
            return True
        return False

    def GetCreatedAt(self):
        return self.created_at

    def GetModifiedAt(self):
        return self.modified_at

    def GetReminderAt(self):
        return self.reminder_at

    def GetNoteId(self):
        return self.note_id

    def GetText(self):
        return self.text

    def GetSummary(self):
        return self.summary

    def GetSource(self):
        return self.source

    def GetSourceUrl(self):
        return self.source_url

    def GetUser(self):
        return self.user

    def GetChildren(self):
        return self.children

    def GetMedia(self):
        '''
        Returns list of media associated with note. For now just images.
        '''
        return self.media

    def GetLabels(self):
        return self.labels

    def GetLocation(self):
        return self.location

class Api(object):
    '''A python interface into the Snaptic API

    Example usage:
        To create an instance of the snaptic.Api class with basic authentication:
        >> import snaptic
        >> api = snaptic.Api("username", "password")

        To fetch users notes:
        >> notes = api.GetNotes()
        >> print [n.GetCreatedAt() for n in notes]

        ['2010-03-08T17:49:08.850Z', '2010-03-06T20:02:32.501Z', '2010-03-06T01:35:14.851Z', '2010-03-05T04:13:00.616Z', '2010-03-01T00:09:38.566Z', '2010-02-18T04:09:55.471Z', '2010-02-18T02:26:35.990Z', 
        '2010-02-12T23:28:22.612Z', '2010-02-10T03:06:50.590Z', '2010-02-10T06:02:57.068Z', '2010-02-08T05:14:07.000Z', '2010-02-08T02:28:20.391Z', '2010-02-05T06:57:54.323Z', '2010-02-07T07:26:34.469Z', 
        '2010-01-25T02:11:24.075Z', '2010-01-24T23:37:07.411Z']

        To post a note:
        >> r = api.PostNote("#harry My third note just got uploaded")
        >> print r
        "notes":[
            {
            "created_at": "2010-03-10T05:04:53.357Z",
            "modified_at": "2010-03-10T05:04:53.357Z",
            "reminder_at": "",
            "id": "1422194",
            "text": "#harry My third note just got uploaded",
            "summary": "#harry My third note just got uploaded",
            "source": "3banana",
            "source_url": "https://snaptic.com/",
            "user": {
                "id": "913202",
                "user_name": "ht"
            },
            "children": "0",
            "labels": [
                "harry" ],
            "location": {}
            }   ,
        {"hi":"a little wave"}]}

       To delete the above note:
       >> jsonR  = json.loads(r)
       >> id     = jsonR["notes"][0]['id']
       >> api.DeleteNoteWithId(id)

       To add an image to the above note
       >> jsonR  = json.loads(r)
       >> id     = jsonR["notes"][0]['id']
       >> api.LoadImageAndAddToNoteWithID("myimage.jpg", id)

       To download image data from a note:
       >> m  = note.GetMedia()
       >> id = m[0].GetID()
       >> d = api.GetImageWithId(id)
       >> filename = "%s.jpg" % id
       >> fout = open(filename, "wb")
       >> fout.write(d)
       >> fout.close()

    '''
    API_VERSION = "v1"

    def __init__(self, username, password=None, url='api.snaptic.com', use_ssl=True, port=443, timeout=10):
        self._url       = 'api.snaptic.com'
        self._use_ssl   = use_ssl
        self._port      = port
        self._timeout   = timeout
        self._user      = None
        self.SetCredentials(username, password)

    def SetCredentials(self, username, password):

        '''
        Set username/password

        Args:
            username: snaptic username
            password: snaptic password
        '''
        self._username = username
        self._password = password

    def LoadImageAndAddToNoteWithID(self, filename=None, id=None):
        if filename and id:
            try: 
                fin     = open(filename, 'r')
                data    = fin.read()
                return self.AddImageToNoteWithID(filename, data, id)
            except IOError:
                raise SnapticError("Error reading filename")
        else:
            raise SnapticError("Error problem occured with one of the variables passed to LoadImageAndAddToNoteWithID, filename: %s, id: %s." % (filename, id))

    def AddImageToNoteWithID(self, filename=None, data=None, id=None):
        if data and id and filename:
            page                = "/" + self.API_VERSION + "/images/" + id +".json"
            try:
                return self._PostMultiPart(self._url, page, [("image", filename, data)])
            except IOError, e:
                if hasattr(e, 'code'):
                    raise SnapticError("Error adding image to note, http error code: %s: headers %s" % (e.code, e.headers)) 
        else:
            raise SnapticError("Error problem occured with variables passed to AddImageToNoteWithID filename: %s, id: %s " % (filename, id))

    def _PostMultiPart(self, host, selector, files):
        """
        Post files to an http host as multipart/form-data.
        files is a sequence of (name, filename, value) elements for data to be uploaded as files
        Return the server's response page.
        """
        content_type, body = self._EncodeMultiPartFormData(files)
        try:
            handler = httplib.HTTPConnection(host)
            headers = self._MakeBasicAuthHeaders(self._username, self._password)
            h = {
                'User-Agent': 'INSERT USERAGENTNAME',#Change this to library version? -htormey
                'Content-Type': content_type
                }
            headers.update(h)
            handler.request('POST', selector, body, headers)
            response = handler.getresponse()
            return response.status, response.reason, response.read()
        except IOError, e:
             if hasattr(e, 'code'):
                raise SnapticError("Error posting file to note, http error code: %s: headers %s" % (e.code, e.headers))

    def _EncodeMultiPartFormData(self, files):
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
            L.append('Content-Type: %s' % self._GetContentType(filename))
            L.append('')
            L.append(value)
        L.append('--' + BOUNDARY + '--')
        L.append('')
        body = CRLF.join(L)
        content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
        return content_type, body

    def _GetContentType(self, filename):
        return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

    def DeleteNoteWithId(self, id=None):
        if id:
            try:
                page            = "/" + self.API_VERSION + "/notes/" + id
                handle          = self._BasicAuthRequest(page, method='DELETE')
                response        = handle.getresponse()
                handle.close()
            except IOError, e:
                 if hasattr(e, 'code'):
                    raise SnapticError("Error posting note, http error code: %s: headers %s" % (e.code, e.headers))
        else:
            raise SnapticError("Error deleting note, no id passed")

    def PostNote(self, note=None):
        if note:
            headers     = { 'Content-type' : "application/x-www-form-urlencoded" }
            params      = urlencode(dict(text=note))
            page        = "/" + self.API_VERSION + '/notes.json'
            handle      = self._BasicAuthRequest(page, headers=headers, method='POST', params=params)
            response    = handle.getresponse()
            data        = response.read()
            handle.close()
            if response.status != int(200):
                raise SnapticError("Error posting note, http status: %s, message: %s " % (response.status, data))
            return data
        else:
            raise SnapticError("Error posting note, no note value passed")

    def GetImageWithId(self, id):
        '''
        Get image data using the following id
        '''
        url = "/viewImage.action?viewNodeId=" + id
        return self._FetchUrl(url)

    def GetUserId(self):
        '''
        Get ID of API user.
        '''
        if self._user:
            return self._user.GetId()
        else:
            raise SnapticError("Error user id not set, try calling GetNotes.")

    def GetNotes(self):
        url = "/" + self.API_VERSION + "/notes.json"
        jsonNotes = self._FetchUrl(url)
        return self._ParseNotes(jsonNotes)

    def GetNotesAsJson(self):
        url = "/" + self.API_VERSION + "/notes.json"
        return self._FetchUrl(url)

    def _FetchUrl(self, url):
        if self._username and self._password:
            try:
                handle       = self._BasicAuthRequest(url)
                response     = handle.getresponse()
                data         = response.read()
                handle.close()
                return data
            except IOError, e:
                if hasattr(e, 'code'):
                    raise SnapticError("Error fetching url, http error code: %s: headers %s" % (e.code, e.headers))

    def _MakeBasicAuthHeaders(self, username, password):
        if username and password:
            headers = dict(Authorization="Basic %s"
                    %(base64.b64encode("%s:%s" %(username, password))))
        else:
            raise SnapticError("Error making bacis auth headers with username: %s, password: %s" % (username, password))
        return headers

    def _BasicAuthRequest(self, path, method='GET', headers={}, params={}):
        ''' Make a HTTP request with basic auth header and supplied method.
        Defaults to operating over SSL. '''
        h = self._MakeBasicAuthHeaders(self._username, self._password)
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

    def _ParseNotes( self, source, get_image_data=False):
        notes      = []
        jsonNotes  = json.loads(source)

        for note in jsonNotes['notes']:
            media           = []
            location        = []
            labels          = []
            user            = None

            if 'id' in note:
                if 'user' in note:
                    self._user = User(note['user']['id'], note['user']['user_name'])
                if 'location' in note:
                    pass
                if 'labels' in note:
                    labels = []
                    for label in note['labels']:
                        labels.append(label)
                if 'media' in note:
                    for item in note['media']:
                        if item['type'] == 'image':
                            imageData = None
                            if get_image_data:
                                imageData = self._FetchUrl(item['src'])
                            media.append(Image(item['type'], item['md5'], item['id'], item['revision_id'], item['width'], item['height'], item['src'], imageData))

                notes.append(Note(note['created_at'], note['modified_at'], note['reminder_at'], note['id'], note['text'], note['summary'], note['source'], 
                                note['source_url'], user, note['children'], media, labels, location))
        return notes
