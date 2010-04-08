# backwards compatible with Python < 2.6
try:
    import json
except ImportError:
    import simplejson as json
import sys

from nose.tools import assert_equals, assert_true
from testconfig import config
import snaptic


def test_get_notes():
    """
    Verify that notes returns a list of notes greater than 0 from test account with notes in it.
    """
    api = snaptic.Api(username=config['api']['email'], password=config['api']['password'])
    n   = api.notes
    assert len(n) > 0
    return n

def test_post_note():
    """
    Verify that you get back the approrpiate Json object when you post a note.
    """
    api = snaptic.Api(username=config['api']['email'], password=config['api']['password'])
    data_before_post = test_get_notes()
    r   = api.post_note("Testing 123")
    data_after_post = test_get_notes()
    assert_equals(len(data_before_post) +1, len(data_after_post), "Note count from API indicates note not written to backend")
    return r

def test_post_note_json_schema_valid():
    """ 
    Verify that Json returned by post notes service contains expected fields
    """
    r                   = test_post_note()
    data                = json.loads(r)
    assert_true(len(data['notes']) > 0)
    note_fields = ('id', 'created_at', 'modified_at', 'reminder_at', 'text',
    'summary', 'source', 'source_url', 'user', 'children', 'tags', 'location')
    for note in data['notes']:
        for field in note_fields:
            assert_true(field in note)


