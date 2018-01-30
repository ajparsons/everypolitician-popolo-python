from unittest import TestCase

import six
import os
from datetime import datetime
import json
from approx_dates.models import ApproxDate
from popolo_data.importer import Popolo, NotAValidType
from popolo_data.models import (Person, Organization, Membership,
                                Area, Post, Event)
from popolo_data.base import approx_date_to_iso
from tempfile import mktemp

class TestSaving(TestCase):
    """
    test assignments to attributes and to files
    """
    def test_date_save_load(self):
        
        p = Person()
        p.birth_date = ApproxDate.from_iso8601("2015")
        assert approx_date_to_iso(p.birth_date) == "2015"
        p.birth_date = ApproxDate.from_iso8601("2015-06")
        assert approx_date_to_iso(p.birth_date) == "2015-06"
        p.birth_date = "2015-06-23 to 2015-07-12"
        assert approx_date_to_iso(p.birth_date) == "2015-06-23 to 2015-07-12"
        p.birth_date = datetime(2015,6,23)
        assert approx_date_to_iso(p.birth_date) == "2015-06-23"        
        
    
    def test_invalidtype(self):
        
        p = Popolo()
        t = "hello this is a string, an invalid type!"
        try:
            p.add(t)
        except NotAValidType:
            pass

    def test_twitter(self):
        """
        does adding delete values
        """
        p = Person()
        p.twitter = "testuser"
        p.twitter = "http://www.twitter.com/testuser"
        p.twitter = "testuser"
        assert p.twitter == "testuser"
        
        p.twitter = None
        
    
    def test_merge(self):
        
        """
        "test if merging preserves correct details
        """
        full_attributes = {"id": "person1",
                             "email": "test@madeup.com",
                             "honorific_prefix": "Dr",
                             "honorific_suffix": "MBe",
                             "image": "blahblah.jpg",
                             "name": "Indiana Jones",
                             "sort_name": "jones, indiana",
                             "national_identity": "american",
                             "biography": "steals things",
                             "birth_date": datetime(1899, 7, 1).date(),
                             "death_date": ApproxDate.FUTURE,
                             "family_name": "Jones",
                             "given_name": "Indiana",
                             "summary": "archaeologist",
                             "wikidata": "Q174284",
                             "phone": "9906753",
                             "fax": "5559906753",
                             "property": "123 fake street",
                             "facebook": "https://www.facebook.com/indianajones/",
                             "sources": ["TV", "Movies"],
                             }

        reduced_attributes = {"id": "4435435",
                             "gender": "male",
                             "name": "Indiana Jones",
                             "other_names": [{"name":"Indiana Walton Jones"}],
                             }

        p1 = Person()
        p2 = Person()

        for k, v in six.iteritems(full_attributes):
            setattr(p1, k, v)

        for k, v in six.iteritems(reduced_attributes):
            setattr(p2, k, v)       

        assert "Q174284" == p1.identifier_value("wikidata")
        #also test a model without a custom absorb class
        o1 = Organization(id="org1",
                          name="org1")
        o2 = Organization(id="org1",
                          name="org1")
        
        membership = Membership()
        membership.person = p2

        pop1 = Popolo.new()
        pop2 = Popolo.new()
        pop1.add(p1)
        pop1.add(o1)
        pop2.add(p2)
        pop2.add(o2)
        pop2.add(membership)
        one_way = pop1.merge(pop2)
        other_way = pop2.merge(pop1)
        
        new_person = one_way.persons[0]        
        other_person = other_way.persons[0]

        original = pop1.persons[0]
        assert new_person.id == "person1"
        assert other_person.id == "person1"
        assert new_person.property == "123 fake street"
        assert other_person.property == "123 fake street"
        assert new_person.gender == "male"
        assert other_person.gender == "male"
        assert "Indiana Walton Jones"  in [x["name"] for x in new_person.other_names]
        assert "Indiana Walton Jones" not in [x["name"] for x in original.other_names]
        
        #test collection json export
        pop1.persons.json()
      
    def test_populate_from_scratch(self):
        """
        test person
        """
        pop = Popolo()
        
        """
        test person
        """
        person_attributes = {"id": "person1",
                             "email": "test@madeup.com",
                             "gender": "male",
                             "honorific_prefix": "Dr",
                             "honorific_suffix": "MBe",
                             "image": "blahblah.jpg",
                             "name": "Indiana Jones",
                             "sort_name": "jones, indiana",
                             "national_identity": "american",
                             "biography": "steals things",
                             "birth_date": datetime(1899, 7, 1).date(),
                             "death_date": datetime(1999, 7, 1).date(),
                             "family_name": "Jones",
                             "given_name": "Indiana",
                             "summary": "archaeologist",
                             "wikidata": "Q174284",
                             "phone": "9906753",
                             "fax": "5559906753",
                             "property": "123 fake street",
                             "facebook": "https://www.facebook.com/indianajones/",
                             "other_names": [{"name":"Indiana Walton Jones"}],
                             "sources": ["TV", "Movies"],
                             "twitter":"indianajones",
                             }

        p = Person()

        for k, v in six.iteritems(person_attributes):
            setattr(p, k, v)
            assert getattr(p, k) == v

        pop.add([p])
        """
        test organisation
        """
        org_attributes = {"id": "org1",
                          "name": "made up organisation",
                          "wikidata": "Q20136634",
                          "classification": "Parliament",
                          "image": "parliament.jpg",
                          "founding_date": datetime(1894, 7, 1).date(),
                          "dissolution_date": datetime(1923, 7, 1).date(),
                          "seat": 50,
                          "other_names": ["banana republic"]
                          }

        o = Organization()

        for k, v in six.iteritems(org_attributes):
            setattr(o, k, v)
            assert getattr(o, k) == v

        pop.add(o)
        """
        test area
        """
        area_attributes = {"id": "area1",
                           "name": "Brighton",
                           "type": "City",
                           "wikidata": "Q131491"
                           }

        a = Area()

        for k, v in six.iteritems(area_attributes):
            setattr(a, k, v)
            assert getattr(a, k) == v

        pop.add(a)
        """
        test post
        """
        post_attribute = {"id": "post1",
                          "label": "Leader",
                          "organization_id": "org1",
                          }

        p = Post()

        for k, v in six.iteritems(post_attribute):
            setattr(p, k, v)
            assert getattr(p, k) == v

        pop.add(p)
        
        """
        test event
        """
        event_attributes = {"id": "event1",
                          "classification": "legislative-term",
                          "start_date": datetime(1900, 1, 1).date(),
                          "end_date": datetime(1905, 1, 1).date(),
                          "organization_id":"org1",
                          }        
        e = Event()
        for k, v in six.iteritems(event_attributes):
            setattr(e, k, v)
            assert getattr(e, k) == v
        pop.add(e)
            
        membership_attributes = {"role":"MP",
                                 "person_id":"person1",
                                 "organisation_id":"org1",
                                 "area_id":"area1",
                                 "post_id":"post1",
                                 "legislative_period_id":"event1",
                                 "start_date": datetime(1900, 5, 1).date(),
                                 "end_date":datetime(1903, 1, 1).date(),
                                 }
            
        m = Membership()
        for k, v in six.iteritems(membership_attributes):
            setattr(m, k, v)
            assert getattr(m, k) == v
        pop.add(m)        

        
        """
        can we save and reload this intact?
        """

        j = pop.to_json()
        pop2 = Popolo(json.loads(j))
        assert pop2.to_json() == pop.to_json()
        
        assert pop.memberships[0].id == pop2.memberships[0].id
        
        """
        save to temp file
        """
        filename = mktemp()
        pop.to_filename(filename)
        os.remove(filename)
        
        