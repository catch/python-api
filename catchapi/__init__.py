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

import mimetypes
import base64
import httplib
import os
import simplejson as json
import sys
from urllib import urlencode
import urlparse

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

class User(object):
    """
    A class representing the User structure used by the Catch API.

     The User class exposes the following properties::
       user.id # read only
       user.user_name # read only
       user.created_at # read only
       user.email # read only
    """

    def __init__(self, id=None, user_name=None, created_at=None, email=None):
        self._id             = id
        self._user_name      = user_name
        self._created_at     = created_at
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
    def email(self):
        return self._email

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

class Note(object):
    """
    A class representing the Note structure used by the Catch API.

    The Note structure exposes the following properties::

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
        note.tags
        note.location
        note.has_media # read only
        note.dictionary # read only
    """

    def __init__(self, created_at, modified_at, reminder_at, note_id, text,
                 summary, source, source_url, user, children, media = [], tags = [], location = []):
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
        self.tags         = tags
        self.location     = location

    @property
    def has_media(self):
        """
        Check to see if Note has any media (images) associated with it.

        Returns:
            True/False
        """
        return len(self.media) > 0

    @property
    def dictionary(self):
        """
        Returns text from the note packaged as a dictionary.

        Returns:
            A dictionary containing selected attributes from the note.
        """
        #Working on adding dates/location/media and other fields to this dictionary. Right now you can just update text. -htormey
        return dict(text=self.text)

class Api(object):
    """
       Example usage:

           To create an instance of the catch.Api class with basic authentication:

               >>> import catchapi
               >>> api = catch.Api("username", "password")

           To fetch all users notes and print an attribute:

               >>> [n.created_at for n in api.notes]
               ['2010-03-08T17:49:08.850Z', '2010-03-06T20:02:32.501Z', ...]

           To fetch a subset of a users notes use a cursor. To get the first 20 notes and print an attribute:

               >>> [n.text for n in api.get_notes_from_cursor(-1)]
               ['Harry says catch is da bomb #food #ice', 'Harry says catch is da bomb #food #ice', ...]

           To get the next 20 notes use cursor 1 (cursor 0 returns all notes in a users account):

               >>> [n.text for n in api.get_notes_from_cursor(1)]
               ['post number 83', 'post number 82', 'post number 81', 'post number 80', ...]

           To post a note:

               >>> api.post_note("Harry says catch is da bomb")
               {
                "notes":[
                    {
                        "summary":"Harry says catch is da bomb",
                        "user": {
                            "user_name":"harry12",
                            "id":1813083},
                            "created_at":"2010-04-22T04:19:16.543Z",
                            "mode":"private",
                            "modified_at":"2010-04-22T04:19:16.543Z",
                            "reminder_at":null,
                            "id":2276722,
                            "text":"Harry says catch is da bomb",
                            "tags":[],
                            "source":"3banana",
                            "location":null,
                            "source_url":"https://catch.com/",
                            "children":0
                    }]}

           To delete a note:

               >>> id        = api.notes[1].note_id
               >>> api.delete_note(id)

           To add an image to the above note

               >>> id        = api.notes[1].note_id
               >>> api.load_image_and_add_to_note_with_id("myimage.jpg", id)

           To edit a note:

               >>> n[0].text='Harry says coolio'
               >>> api.edit_note(n[0])

           To download image data from a note:

              >>> api.notes[1].has_media
              True
              >>> id = api.notes[1].note_id
              >>> d = api.get_image_with_id(id)
              >>> filename = "/Users/harrytormey/%s.jpg" % id
              >>> fout = open(filename, "wb")
              >>> fout.write(d)
              >>> fout.close()

           To get a json object of a users tags

             >>> api.get_tags()
             {
             "tags":[
                {
                    "name":"food",
                    "count":"1",
                },
                {
                    "name":"ice",
                    "count":"1",
                },
             ]}
    """

    def __init__(self, username=None, password=None, url="api.catch.com",
                 use_ssl=True, port=443, timeout=10, cookie_epass=None):
        """
        Args:
            username: The username of the catch account.
            password: The password of the catch account.
            url: The url of the api server which will handle the http(s) API requests.
            use_ssl: Use ssl for basic auth or not.
            port: The port to make http(s) requests on.
            timeout: number of seconds to wait before giving up on a request.
        """
        self._url       = url
        self._use_ssl   = use_ssl
        self._port      = port
        self._timeout   = timeout
        self._user      = None
        self._notes     = None
        self._json      = None
        if cookie_epass:
            self.set_credentials(cookie_epass=cookie_epass)
        else:
            self.set_credentials(username=username, password=password)

    def set_credentials(self, username=None, password=None, cookie_epass=None):
        """
        Set username/password or cookie.

        Args:
            username:
                catch username.
            password:
                catch password.
            cookie_epass:
                catch authentication cookie
        """
        if username and password:
            self._username = username
            self._password = password
        elif cookie_epass:
            self._cookie_epass = cookie_epass
        else:
            raise CatchError("No username/password combination\
                                or cookie authentication provided")

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

    def delete_note(self, id):#Change this to just take a note
        """
        Delete a note.

        Args:
            id: id of note to be deleted.
        Returns:
            The server's response page.
        """
        return self._request("DELETE", id)

    def edit_note(self, note):
        """
        Edit a note.

        Args:
            note: note object to be edited
        Returns:
            The server's response page.
        """
        return self._request("POST", note)

    def post_note(self, note):
        """
        Post a note.

        Args:
            note: text of note to be posted.
        Returns:
            The server's response page.
        """
        return self._request("POST", note) #change this to note_text to be a little clearer -htormey

    def _request(self, http_method, note): #Clean this up a little -htormey
        """
        Perform a http request on a note.

        Args:
            http_metod: what kind of http request is being made (i.e POST/DELETE/GET)
        Returns:
            The server's response page.
        """
        if http_method == "POST":
            headers     = { 'Content-type' : "application/x-www-form-urlencoded" }
            if isinstance(note, Note):
                #Edit an existing note
                params         = urlencode(note.dictionary)
                page = "/v1/notes/%s.json" % str(note.note_id)
            else:
                params = urlencode(dict(text=note))
                page = "/v1/notes.json"
            handle      = self._basic_auth_request(page, headers=headers, method="POST", params=params)
        elif http_method == "DELETE":
            page = "/v1/notes/%s.json" % str(note)
            handle = self._basic_auth_request(page, method="DELETE")

        response    = handle.getresponse()
        data        = response.read()
        handle.close()

        if response.status != 200:
            raise CatchError("Http error posting/editing/deleting note ", response.status, data)
        return data

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

    @property
    def notes(self):
        doc = "A parsed list of note objects"
        def fget(self):
            if self._notes:
                return self._notes
            else:
                return self.get_notes()
        return locals()

    def get_notes(self):
        """
        Get notes and update the Api's internal cache.

        Returns:
            A list of Note objects from the catch users account.
        """
        url = "/v1/notes.json"
        json_notes   = self._fetch_url(url)
        self._notes  = self._parse_notes(json_notes)
        return self._notes

    def get_notes_from_cursor(self, cursor_position):
        """
        Get a batch of upto 20 notes from a given cursor position. See
        description given for json_cursor for further details on how
        cursors work with catch.

        Args:
            cursor_position: cursor position to grab 20 notes from (i.e -1 is most recent 20)
        Returns:
            A list of note objects based on the contents of the users account.
        """
        json_notes   = self.json_cursor(cursor_position)
        notes  = self._parse_notes(json_notes)
        return notes

    def get_cursor_information(self, cursor_position):
        """
        Gets information about cursor at a given position. See json_cursor for further
        details on how cursors work with catch.

        Args:
            cursor_position: cursor position you want to find out about.
        Returns:
            A dictionary containing previous_cursor, next_cursor and note count.
        """
        json_notes   = self.json_cursor(cursor_position)
        return self._parse_cursor_info(json_notes)

    def _parse_cursor_info(self, source):
        """
        Parse cursor information with notes returned from catch.

        Args:
            source: A json object consisting of notes and cursor information
        Returns:
            A dictionary containing previous_cursor, next_cursor and note count.
        """
        cursor_info   = json.loads(source)
        if 'next_cursor' in cursor_info and 'previous_cursor' in cursor_info and 'count' in cursor_info:
            return {"previous_cursor": cursor_info['previous_cursor'], "next_cursor": cursor_info['next_cursor'], "count": cursor_info['count'] }
        else:
            CatchError("Error keys missing from source JSON passed to _parse_cursor_info")

    def get_user(self):
        """
        Get user info.

        Returns:
            A user object.
        """
        url = "/v1/user.json"
        user_info = self._fetch_url(url)
        self._parse_user_info(user_info)
        return self._user

    @property
    def json():
        doc = "Json object of notes stored in account."
        def fget(self):
            if self._json:
                return self._json #should I return json.load(sef._json) ? -htormey
            else:
                return self.get_json()
        return locals()

    def get_json(self):
        """
        Get json object and update the cache.

        Returns:
            A json object representing all notes in a users account.
        """
        url = "/v1/notes.json"
        self._json  = self._fetch_url(url)
        return self._json

    def get_tags(self):
        """
        Fetch json object containing tags from users account.

        Returns:
            A json object containing tags and related information (number of notes per tag, etc).
        """
        url = "/v2/tags.json"
        tags = self._fetch_url(url)
        return tags

    def json_cursor(self, cursor_position):
        """
        Get batches of 20 notes in JSON format from a given cursor position i.e -1, 1,
        etc. For example: -1 returns the most recent 20 notes, 1 returns the previous 20
        before that, etc. One exeption to note is that 0 returns a JSON object for all
        notes in a given account.

        Args:
            cursor_position: cursor position to grab 20 notes from (i.e -1 is most recent 20).
        Returns:
            A json object containing notes from cursor position requested.
        """
        url =  "/v1/notes.json?cursor=%s" % str(cursor_position)
        cursor      = self._fetch_url(url)
        return cursor

    def _fetch_url(self, url):
        """
        Perform a basic auth request on a given catch API endpoint.

        Args:
            url: Catch Api endpoint (i.e /v1/notes.json etc).
        Returns:
            The server's response page.
        """
        handler       = self._basic_auth_request(url)
        response      = handler.getresponse()
        data          = response.read()
        handler.close()
        if response.status != 200:
            raise CatchError("Http error", response.status, data)
        return data

    def _get_auth_headers(self):
        """
        Switch between basic auth and cookie auth depending on which properties
        self has.
        """
        if hasattr(self, "_username") and hasattr(self, "_password"):
            return self._make_basic_auth_headers(self._username, self._password)
        elif hasattr(self, "_cookie_epass"):
            return self._make_cookie_auth_headers(self._cookie_epass)
        else:
            raise CatchError("No username/password combination\
                                or cookie authentication provided")

    def _make_basic_auth_headers(self, username, password):
        """
        Encode headers for basic auth request.

        Args::

            username: catch username to be used.
            password: password to be used.

        Returns:
            Dictionary with encoded basic auth values.
        """
        if username and password:
            headers = dict(Authorization="Basic %s"
                    %(base64.b64encode("%s:%s" %(username, password))))
        else:
            raise CatchError("Error making basic auth headers with username: %s, password: %s" % (username, password))
        return headers

    def _make_cookie_auth_headers(self, cookie_epass):
        """
        Encode headers for cookie auth request.

        Args::

            cookie_epass: cookie auth token to be used.

        Returns:
            Dictionary with encoded basic auth values.
        """
        if cookie_epass:
            return {
                "Cookie": "cookie_epass={0}".format(cookie_epass)
            }
        else:
            raise CatchError("Error making cookie auth headers with\
                               cookie:{0}".format(cookie_epass))

    def _basic_auth_request(self, path, method="GET", headers={}, params={}):
        """
        Make a HTTP request with basic auth header and supplied method.
        Defaults to operating over SSL.

        Args::

            path: Catch API endpoint
            metthod: which http method to use (PUT/DELETE/GET)
            headers: Additional header to use with request.
            params: Other parameters to use

        Returns:
            The server's response page.
        """
        h = self._get_auth_headers()
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
        """
        Parse JSON user returned from catch, instantiate a User object from it.

        Args:
            source: Json object representing a user
        Returns:
            A User object.
        """
        user_info   = json.loads(source)

        if 'user' in user_info:
            self._user = User(user_info['user']['id'], user_info['user']['user_name'], user_info['user']['created_at'], user_info['user']['email'])
        else:
            raise CatchError("Error no user key found in source JSON passed to _parse_user_info")

    def _parse_notes( self, source, get_image_data=False):
        """
        parse JSON notes returned from catch, instantiate a list of note objects from it.

        Args::

            source: A json object representing a list of notes.
            get_images: if images are associated with notes, download them now.
        Returns:
            A list of note objects.
        """

        notes       = []
        json_notes  = json.loads(source)

        for note in json_notes['notes']:
            media           = []
            location        = []
            tags            = []
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
                if 'tags' in note:
                    for tag in note['tags']:
                        tags.append(tag)
                if 'media' in note:
                    for item in note['media']:
                        if item['type'] == 'image':
                            image_data = None
                            if get_image_data:
                                image_data = self._fetch_url(item['src'])
                            media.append(Image(item['type'], None, item['id'], item['revision_id'], item['width'], item['height'], item['src'], image_data))

                notes.append(Note(note['created_at'], note['modified_at'], note['reminder_at'], note['id'], note['text'], note['summary'], note['source'],
                                note['source_url'], user, note['children'], media, tags, location))
        return notes
