# -*- coding: utf-8 -*-

from datetime import date
from unittest import TestCase

from mock import patch
import six

from .helpers import example_file

from popolo_data.importer import Popolo


EXAMPLE_EVENT_JSON = b'''
{
    "events": [
        {
            "classification": "legislative period",
            "end_date": "2015-03-23",
            "id": "term/12",
            "identifiers": [
                {
                    "identifier": "Q967549",
                    "scheme": "wikidata"
                }
            ],
            "name": "12th Riigikogu",
            "organization_id": "1ba661a9-22ad-4d0f-8a60-fe8e28f2488c",
            "start_date": "2011-03-27"
        }
    ],
    "organizations": [
        {
            "classification": "legislature",
            "id": "1ba661a9-22ad-4d0f-8a60-fe8e28f2488c",
            "identifiers": [
                {
                    "identifier": "Q217799",
                    "scheme": "wikidata"
                }
            ],
            "name": "Riigikogu",
            "seats": 101
         }
    ]
}
'''

EXAMPLE_EVENT_NON_ASCII_JSON = b'''
{
    "events": [
        {
            "classification": "legislative period",
            "end_date": "2015-03-23",
            "id": "2015",
            "name": "2015\xe2\x80\x94",
            "start_date": "2015-03-01"
        }
    ]
}
'''


class TestEvents(TestCase):

    def test_empty_file_gives_no_events(self):
        popolo = Popolo({})
        assert len(popolo.events) == 0

    def test_single_event_with_label(self):
        with example_file(EXAMPLE_EVENT_JSON) as fname:
            popolo = Popolo.from_filename(fname)
            assert len(popolo.events) == 1
            event = popolo.events[0]
            assert event.name == '12th Riigikogu'

    def test_start_and_end_dates(self):
        with example_file(EXAMPLE_EVENT_JSON) as fname:
            popolo = Popolo.from_filename(fname)
            event = popolo.events.first
            assert event.start_date == date(2011, 3, 27)
            assert event.end_date == date(2015, 3, 23)

    def test_event_id(self):
        with example_file(EXAMPLE_EVENT_JSON) as fname:
            popolo = Popolo.from_filename(fname)
            event = popolo.events.first
            assert event.id == 'term/12'

    def test_event_organization_id(self):
        with example_file(EXAMPLE_EVENT_JSON) as fname:
            popolo = Popolo.from_filename(fname)
            event = popolo.events.first
            assert event.organization_id == \
                '1ba661a9-22ad-4d0f-8a60-fe8e28f2488c'

    def test_event_organization(self):
        with example_file(EXAMPLE_EVENT_JSON) as fname:
            popolo = Popolo.from_filename(fname)
            event = popolo.events.first
            org = popolo.organizations.first
            assert event.organization == org

    def test_event_classification(self):
        with example_file(EXAMPLE_EVENT_JSON) as fname:
            popolo = Popolo.from_filename(fname)
            event = popolo.events.first
            assert event.classification == 'legislative period'

    def test_event_identifiers(self):
        with example_file(EXAMPLE_EVENT_JSON) as fname:
            popolo = Popolo.from_filename(fname)
            event = popolo.events.first
            assert event.identifiers == [
                {
                    "identifier": "Q967549",
                    "scheme": "wikidata"
                }
            ]

    def test_event_repr(self):
        with example_file(EXAMPLE_EVENT_JSON) as fname:
            popolo = Popolo.from_filename(fname)
            event = popolo.events.first
            if six.PY2:
                assert repr(event) == b"<Event: 12th Riigikogu>"
            else:
                assert repr(event) == u"<Event: 12th Riigikogu>"

    def test_event_repr_non_ascii(self):
        with example_file(EXAMPLE_EVENT_NON_ASCII_JSON) as fname:
            popolo = Popolo.from_filename(fname)
            event = popolo.events.first
            if six.PY2:
                assert repr(event) == b"<Event: 2015\xe2\x80\x94>"
            else:
                assert repr(event) == u"<Event: 2015—>"

    def test_event_identity_equality_and_inequality(self):
        with example_file(EXAMPLE_EVENT_JSON) as fname:
            popolo_a = Popolo.from_filename(fname)
        event_a = popolo_a.events.first
        with example_file(EXAMPLE_EVENT_JSON) as fname:
            popolo_b = Popolo.from_filename(fname)
        event_b = popolo_b.events.first
        assert event_a == event_b
        assert not (event_a != event_b)

    def test_term_current_at_true(self):
        with example_file(EXAMPLE_EVENT_JSON) as fname:
            popolo = Popolo.from_filename(fname)
            event = popolo.events[0]
            assert event.current_at(date(2013, 1, 1))

    def test_term_current_at_false_before(self):
        with example_file(EXAMPLE_EVENT_JSON) as fname:
            popolo = Popolo.from_filename(fname)
            event = popolo.events[0]
            assert not event.current_at(date(1980, 1, 1))

    def test_term_current_at_false_after(self):
        with example_file(EXAMPLE_EVENT_JSON) as fname:
            popolo = Popolo.from_filename(fname)
            event = popolo.events[0]
            assert not event.current_at(date(2020, 1, 1))

    @patch('popolo_data.base.date')
    def test_term_current_true(self, mock_date):
        mock_date.today.return_value = date(2013, 1, 1)
        mock_date.side_effect = lambda *args, **kw: date(*args, **kw)
        with example_file(EXAMPLE_EVENT_JSON) as fname:
            popolo = Popolo.from_filename(fname)
            event = popolo.events[0]
            assert event.current