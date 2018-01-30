"""
Classes to access items inside Popolo Collections

"""

import json
import re
import hashlib
import unidecode
from six.moves.urllib_parse import urlsplit
import six

from approx_dates.models import ApproxDate

from .base import PopoloObject, CurrentMixin
from .base import Attribute, IdentiferAttribute, DateAttribute, \
                LinkAttribute, ContactAttribute, RelatedAttribute

safe_property = property #we define an attribute of person as 'property'


def _is_name_current_at(name_object, date_string):
    start_range = name_object.get('start_date') or '0001-01-01'
    end_range = name_object.get('end_date') or '9999-12-31'
    return date_string >= start_range and date_string <= end_range

def extract_twitter_username(username_or_url):
    split_url = urlsplit(username_or_url)
    if split_url.netloc == 'twitter.com':
        return re.sub(r'^/([^/]+).*', r'\1', split_url.path)
    return username_or_url.strip().lstrip('@')

def unique_preserving_order(sequence):
    '''Return a list with only the unique elements, preserving order

    This is from http://stackoverflow.com/a/480227/223092'''
    seen = set()
    seen_add = seen.add
    return [x for x in sequence if not (x in seen or seen_add(x))]


class Person(PopoloObject):
    id = Attribute()
    email = Attribute()
    gender = Attribute()
    honorific_prefix = Attribute()
    honorific_suffix = Attribute()
    image = Attribute()
    name = Attribute()
    sort_name = Attribute()
    national_identity = Attribute()
    biography = Attribute()
    birth_date = DateAttribute(default=ApproxDate.PAST)
    death_date = DateAttribute(default=ApproxDate.FUTURE)
    family_name = Attribute()
    given_name = Attribute()
    summary = Attribute()
    wikidata = IdentiferAttribute()
    phone = ContactAttribute()
    fax = ContactAttribute()
    property = ContactAttribute()
    facebook = LinkAttribute()
    links = Attribute(default=[])
    contact_details = Attribute(default=[])
    identifiers = Attribute(default=[])
    images = Attribute(default=[])
    other_names = Attribute(default=[])
    sources = Attribute(default=[])
    phone_all = ContactAttribute(attr="phone",allow_multiple=True)
    facebook_all = LinkAttribute(attr="facebook",allow_multiple=True)
    fax_all = ContactAttribute(attr="fax",allow_multiple=True)

    def get_identifier(self,scheme):
        rel = [x for x in self.identifiers if x["scheme"] == scheme]
        if len(rel) == 0:
            return None
        else:
            return rel[0]["identifier"]

    @safe_property
    def twitter(self):
        username_or_url = self.contact_detail_value('twitter') or \
            self.link_value('twitter')
        if username_or_url:
            return extract_twitter_username(username_or_url)
        return None
    
    @twitter.setter
    def twitter(self,value):
        """
        set new twitter - clears other possible method out
        """
        if value and "twitter.com" in value:
            username = extract_twitter_username(value)
            self.set_link_values("twitter",value)
            self.set_contact_detail_values("twitter", username)
        else:
            self.del_link_values("twitter")
            self.set_contact_detail_values("twitter", value)
            
    @safe_property
    def twitter_all(self):
        # The Twitter screen names in contact_details and links will
        # in most cases be the same, so remove duplicates:
        return unique_preserving_order(
            extract_twitter_username(v) for v in
            self.contact_detail_values('twitter') +
            self.link_values('twitter'))

    @safe_property
    def memberships(self):
        
        from .collections import MembershipCollection
        
        membership_lists = [
            m.data for m in self.all_popolo.memberships
            if m.person_id == self.id
        ]
        return MembershipCollection(membership_lists,self.all_popolo)

    def name_at(self, particular_date):
        historic_names = [n for n in self.other_names if n.get('end_date')]
        if not historic_names:
            return self.name
        names_at_date = [
            n for n in historic_names
            if _is_name_current_at(n, str(particular_date))
        ]
        if not names_at_date:
            return self.name
        if len(names_at_date) > 1:
            msg = "Multiple names for {0} found at date {1}"
            raise Exception(msg.format(self, particular_date))
        return names_at_date[0]['name']
    
    def absorb(self,other):
        """
        makes sure the final version has picked up any alternate spellings
        """
        our_names = [x["name"] for x in self.other_names]
    
        for n in other.other_names:
            if n["name"] not in our_names:
                self.other_names.append(n)

class Organization(PopoloObject):
    
    id = Attribute()
    name = Attribute()
    wikidata = IdentiferAttribute()
    classification = Attribute()
    image = Attribute()
    founding_date = DateAttribute(default=ApproxDate.PAST)
    dissolution_date = DateAttribute(default=ApproxDate.FUTURE)
    seats = Attribute()
    other_names = Attribute(default=[])
    identifiers = Attribute(default=[])
    links = Attribute(default=[])

class Membership(CurrentMixin, PopoloObject):
    
    role = Attribute()
    person_id = Attribute()
    organization_id = Attribute()
    area_id = Attribute()
    post_id = Attribute()
    legislative_period_id = Attribute()
    on_behalf_of_id = Attribute()
    
    person = RelatedAttribute()
    organization = RelatedAttribute()
    area = RelatedAttribute()
    post = RelatedAttribute()
    legislative_period = RelatedAttribute(collection="events")
    on_behalf_of = RelatedAttribute(collection="organizations")
    
    start_date = DateAttribute(default=ApproxDate.PAST)
    end_date = DateAttribute(default=ApproxDate.FUTURE)

    @safe_property
    def id(self):
        """
        returns a comparable id
        """

        m = hashlib.sha256()
        
        combo = [self.person_id,
                 self.organization_id,
                 self.area_id,
                 self.post_id,
                 self.legislative_period_id,
                 self.on_behalf_of_id]
        
        combo = [unidecode.unidecode(x).encode("utf-8") for x in combo if x]
        combo = b"".join(combo)
        m.update(combo)
        return m.hexdigest()


    @safe_property
    def old_id(self):

        combo = str([self.person_id,
                         self.organization_id,
                         self.area_id,
                         self.post_id,
                         self.legislative_period_id,
                         self.on_behalf_of_id])
        return hash(combo)
    
    def __repr__(self):
        enclosed = u"'{0}' at '{1}'".format(
            self.person_id, self.organization_id)
        return self.repr_helper(enclosed)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.data == other.data
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return self.data != other.data
        return NotImplemented

    @safe_property
    def effective_start_date(self):
        """
        If membership contains no special start information, 
        return start of legislative period
        """
        if self.start_date == ApproxDate.PAST:
            return self.legislative_period.start_date
        return self.start_date
    
    @safe_property
    def effective_end_date(self):
        """
        If membership contains no special start information, 
        return start of legislative period
        """
        if self.end_date == ApproxDate.FUTURE:
            return self.legislative_period.end_date
        return self.end_date

    @safe_property
    def key_for_hash(self):
        return json.dumps(self.data, sort_keys=True)
    
    def __hash__(self):
        return hash(self.key_for_hash)


class Area(PopoloObject):
    
    id = Attribute()
    name = Attribute()
    type = Attribute()
    identifiers = Attribute(default=[])
    other_names = Attribute(default=[])
    wikidata = IdentiferAttribute()

    def get_identifier(self,scheme):
        rel = [x for x in self.identifiers if x["scheme"] == scheme]
        if len(rel) == 0:
            return None
        else:
            return rel[0]["identifier"]

class Post(PopoloObject):
    
    id = Attribute()
    label = Attribute()
    organization_id = Attribute()
    organization = RelatedAttribute()


class Event(CurrentMixin, PopoloObject):
    id = Attribute()
    name = Attribute()
    classification = Attribute()
    start_date = DateAttribute(default=ApproxDate.PAST)
    end_date = DateAttribute(default=ApproxDate.FUTURE)
    organization_id = Attribute()
    organization = RelatedAttribute()
    identifiers = Attribute(default=[])

    @property
    def memberships(self):
        from .collections import MembershipCollection
        
        memberships_list = [
            m.data for m in self.all_popolo.memberships
            if m.legislative_period_id == self.id
        ]
        return MembershipCollection(memberships_list, self.all_popolo)
