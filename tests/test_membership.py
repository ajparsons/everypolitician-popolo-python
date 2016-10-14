from datetime import date
from unittest import TestCase

import pytest
import six

from .helpers import example_file

from popolo_data.importer import Popolo


EXAMPLE_SINGLE_MEMBERSHIP = b'''
{
    "persons": [
        {
            "id": "SP-937-215",
            "name": "Jean-Luc Picard"
        }
    ],
    "organizations": [
        {
            "id": "starfleet",
            "name": "Starfleet"
        }
    ],
    "memberships": [
        {
            "person_id": "SP-937-215",
            "organization_id": "starfleet",
            "role": "student",
            "start_date": "2327-12-01"
        }
    ]
}
'''

EXAMPLE_MEMBERSHIP_ALL_FIELDS = b'''
{
    "areas": [
        {
            "id": "dunny-on-the-wold",
            "name": "Dunny-on-the-Wold"
        }
    ],
    "events": [
        {
            "classification": "legislative period",
            "id": "pitt",
            "name": "Parliamentary Period",
            "start_date": "1783-12-19",
            "end_date": "1801-01-01"
        }
    ],
    "persons": [
        {
            "id": "1234",
            "name": "Edmund Blackadder"
        }
    ],
    "posts": [
        {
            "id": "dunny-on-the-wold-seat",
            "label": "Member of Parliament for Dunny-on-the-Wold"
        }
    ],
    "organizations": [
        {
            "id": "commons",
            "name": "House of Commons"
        },
        {
            "id": "adder",
            "name": "Adder Party",
            "classification": "party"
        }
    ],
    "memberships": [
        {
            "area_id": "dunny-on-the-wold",
            "end_date": "1784-05-23",
            "legislative_period_id": "pitt",
            "on_behalf_of_id": "adder",
            "organization_id": "commons",
            "person_id": "1234",
            "post_id": "dunny-on-the-wold-seat",
            "role": "candidates",
            "start_date": "1784-03-01"
        }
    ]
}
'''


class TestMemberships(TestCase):

    def test_empty_file_gives_no_memberships(self):
        with example_file(b'{}') as filename:
            popolo = Popolo.from_filename(filename)
            assert len(popolo.memberships) == 0

    def test_membership_should_not_have_name(self):
        with example_file(EXAMPLE_SINGLE_MEMBERSHIP) as fname:
            popolo = Popolo.from_filename(fname)
            assert len(popolo.memberships) == 1
            m = popolo.memberships[0]
            with pytest.raises(AttributeError):
                m.name

    def test_membership_has_person_id_and_organisation_id(self):
        with example_file(EXAMPLE_SINGLE_MEMBERSHIP) as fname:
            popolo = Popolo.from_filename(fname)
            assert len(popolo.memberships) == 1
            m = popolo.memberships[0]
            assert m.person_id == 'SP-937-215'
            assert m.organization_id == 'starfleet'

    def test_membership_has_role(self):
        with example_file(EXAMPLE_SINGLE_MEMBERSHIP) as fname:
            popolo = Popolo.from_filename(fname)
            assert len(popolo.memberships) == 1
            m = popolo.memberships[0]
            assert m.role == 'student'

    def test_membership_foreign_keys(self):
        with example_file(EXAMPLE_MEMBERSHIP_ALL_FIELDS) as fname:
            popolo = Popolo.from_filename(fname)
            assert len(popolo.memberships) == 1
            m = popolo.memberships[0]
            assert m.area_id == 'dunny-on-the-wold'
            assert m.on_behalf_of_id == 'adder'
            assert m.legislative_period_id == 'pitt'
            assert m.post_id == 'dunny-on-the-wold-seat'

    def test_get_organization_from_membership(self):
        with example_file(EXAMPLE_SINGLE_MEMBERSHIP) as fname:
            popolo = Popolo.from_filename(fname)
            assert len(popolo.memberships) == 1
            m = popolo.memberships[0]
            assert m.start_date == date(2327, 12, 1)

    def test_get_sentinel_end_date_from_membership(self):
        with example_file(EXAMPLE_SINGLE_MEMBERSHIP) as fname:
            popolo = Popolo.from_filename(fname)
            m = popolo.memberships[0]
            assert m.end_date >= date(2500, 1, 1)

    def test_organization_repr(self):
        with example_file(EXAMPLE_SINGLE_MEMBERSHIP) as fname:
            popolo = Popolo.from_filename(fname)
            assert len(popolo.memberships) == 1
            m = popolo.memberships[0]
            assert repr(m) == "<Membership: 'SP-937-215' at 'starfleet'>"
