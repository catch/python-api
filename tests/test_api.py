# backwards compatible with Python < 2.6
try:
    import json
except ImportError:
    import simplejson as json
import sys

from nose.tools import assert_equals, assert_true
from testconfig import config
import snaptic


def test_notes_property():
    """
    Verify that .notes returns a list of notes greater than 0 from test account with notes in it.
    """
    api = snaptic.Api(username=config['api']['email'], password=config['api']['password'])
    n   = api.notes
    assert len(n) > 0
    return n

def test_get_notes():
    """
    Verify that get_notes returns a list of notes greater than 0 from test account with notes in it.
    """
    api = snaptic.Api(username=config['api']['email'], password=config['api']['password'])
    n   = api.get_notes()
    assert len(n) > 0
    return n

def test_post_note():
    """
    Verify posting a note.
    """
    api = snaptic.Api(username=config['api']['email'], password=config['api']['password'])
    data_before_post = test_get_notes()
    r   = api.post_note("Testing 123")
    data_after_post = test_get_notes()
    assert_equals(len(data_before_post) +1, len(data_after_post), "Note count from API indicates note not posted to backend")
    return r

def test_edit_note():
    """
    Verify editing a note.
    """
    api = snaptic.Api(username=config['api']['email'], password=config['api']['password'])
    data_before_post = test_get_notes()
    r   = api.post_note("Testing 123")
    data_after_post = test_get_notes()
    assert_equals(len(data_before_post) +1, len(data_after_post), "Note count from API indicates note not posted to backend")
    #Now try editing note
    test_string = "changed notes rock"
    data_after_post[0].text = test_string
    api.edit_note(data_after_post[0])
    data_after_edit = test_get_notes()
    assert_equals(data_after_edit[0].text, test_string)

def test_delete_note():
    """
    Verify deleting a note.
    """
    api = snaptic.Api(username=config['api']['email'], password=config['api']['password'])
    r   = api.post_note("Testing 123")
    data_after_post     = test_get_notes()
    api.delete_note(data_after_post[0].note_id)
    data_after_delete   = test_get_notes()
    assert_equals(len(data_after_post) -1, len(data_after_delete), "Note count from API indicates a problem deleting note")

def test_get_json_cursor_schema_valid():
    """ 
    Verify that Json returned by the get cursor service contains expected fields.
    """
    api = snaptic.Api(username=config['api']['email'], password=config['api']['password'])
    r                   = api.json_cursor(-1) #Get the first 20 note
    data                = json.loads(r)
    envelope_fields = ('count', 'previous_cursor', 'next_cursor', 'notes')
    for field in envelope_fields:
        assert_true(field in data)
    assert_true(len(data['notes']) > 0)
    note_fields = ('id', 'created_at', 'modified_at', 'reminder_at', 'text',
    'summary', 'source', 'source_url', 'user', 'children', 'tags', 'location')
    for note in data['notes']:
        for field in note_fields:
            assert_true(field in note)

def test_get_json_notes_schema_valid():
    """ 
    Verify that Json returned by the get notes service contains expected fields.
    """
    api = snaptic.Api(username=config['api']['email'], password=config['api']['password'])
    r                   = api.get_json()
    data                = json.loads(r)
    assert_true(len(data['notes']) > 0)
    note_fields = ('id', 'created_at', 'modified_at', 'reminder_at', 'text',
    'summary', 'source', 'source_url', 'user', 'children', 'tags', 'location')
    for note in data['notes']:
        for field in note_fields:
            assert_true(field in note)

def test_post_note_json_schema_valid():
    """ 
    Verify that Json returned by the post notes service contains expected fields.
    """
    r                   = test_post_note()
    data                = json.loads(r)
    assert_true(len(data['notes']) > 0)
    note_fields = ('id', 'created_at', 'modified_at', 'reminder_at', 'text',
    'summary', 'source', 'source_url', 'user', 'children', 'tags', 'location')
    for note in data['notes']:
        for field in note_fields:
            assert_true(field in note)


