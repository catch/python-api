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

import simplejson as json
import sys, unittest, catchapi, os
from getpass import getpass

class TestCatchAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._api_host = raw_input("api host [https://api.catch-branch.com]: ") or "https://api.catch-branch.com"
        cls._username = raw_input("username or email [apitest]: ") or "apitest"
        cls._password = getpass("Password for %s: " % cls._username)

    def setUp(self):
        self.api = catchapi.CatchSession(self.__class__._api_host)

    def login(self, username=None, password=None):
        return self.api.login(username or self.__class__._username,
                              password or self.__class__._password)

    def test_tags(self):
        tags = self.login().tags
        self.failUnless(tags)
        self.failUnless(isinstance(tags, tuple))

    def test_notes_property(self):
        # Verify that .notes returns a list of notes greater than 0 from test account with notes in it.
        notes = self.login().notes
        assert len(notes) > 0
        return notes

    def test_get_note(self):
        u = self.login()
        notes = u.notes
        note = notes.next()
        self.failUnless(note['text'])
        self.assertEquals(note['text'], u.get_note(note['id'])['text'])
        return note

    def test_get_notes(self):
        # Verify that get_notes returns a list of notes greater than 0 from test account with notes in it.
        u = self.login()
        notes, count = u.get_notes()
        self.failUnless(len(notes))
        return notes, count

    def test_post_note(self, user=None):
        # Verify posting a note.
        user = user or self.login()
        data_before_post = user.notes
        note = user.post_note("Testing 123")
        self.assertEquals(note['text'], "Testing 123")
        data_after_post = user.notes
        self.assertEquals(len(data_before_post) + 1, len(data_after_post))
        note.delete()

    def test_edit_note(self):
        # Verify editing a note.
        u = self.login()
        note = u.post_note("test edit")
        self.assertEquals(note['text'], 'test edit')
        note.edit(text="edited text")
        self.assertEquals(note['text'], 'edited text')
        self.assertEquals(u.get_note(note['id'])['text'], note['text'])
        note.delete()

    def test_delete_note(self):
        # Verify deleting a note.
        u = self.login()
        n = u.post_note(text="test_delete_note")
        data_before_delete = u.notes
        n.delete()
        self.failUnless(n.deleted)
        self.assertEquals(len(data_before_delete) -1, len(u.notes))

    def test_media(self):
        u = self.login()
        n = u.post_note(text="test_media")
        m = n.add_media(os.path.join(os.path.dirname(__file__), 'catch_logo.png'))
        m.delete()
        n.delete()
        self.failUnless(m.deleted)

    def test_comments(self):
        u = self.login()
        n = u.post_note(text="test_comments")
        c = n.add_comment(text="a comment")
        self.assertEquals(c['text'], 'a comment')
        self.assertEquals(len(n.comments), 1)
        c.delete()
        n.delete()
