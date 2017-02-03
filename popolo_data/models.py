"""
Classes to access items inside Popolo Collections

"""
import json
from six.moves.urllib_parse import urlsplit

from approx_dates.models import ApproxDate

from .base import PopoloObject, CurrentMixin,ObjectDoesNotExist

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

    class DoesNotExist(ObjectDoesNotExist):
        pass

    class MultipleObjectsReturned(MultipleObjectsReturned):
        pass

    @property
    def id(self):
        return self.data.get('id')

    @property
    def email(self):
        return self.data.get('email')

    @property
    def gender(self):
        return self.data.get('gender')

    @property
    def honorific_prefix(self):
        return self.data.get('honorific_prefix')

    @property
    def honorific_suffix(self):
        return self.data.get('honorific_suffix')

    @property
    def image(self):
        return self.data.get('image')

    @property
    def name(self):
        return self.data.get('name')

    @property
    def sort_name(self):
        return self.data.get('sort_name')

    @property
    def national_identity(self):
        return self.data.get('national_identity')

    @property
    def summary(self):
        return self.data.get('summary')

    @property
    def biography(self):
        return self.data.get('biography')

    @property
    def birth_date(self):
        return self.get_date('birth_date', None)

    @property
    def death_date(self):
        return self.get_date('death_date', None)

    @property
    def family_name(self):
        return self.data.get('family_name')

    @property
    def given_name(self):
        return self.data.get('given_name')

    @property
    def wikidata(self):
        return self.identifier_value('wikidata')

    @property
    def twitter(self):
        username_or_url = self.contact_detail_value('twitter') or \
            self.link_value('twitter')
        if username_or_url:
            return extract_twitter_username(username_or_url)
        return None

    @property
    def twitter_all(self):
        # The Twitter screen names in contact_details and links will
        # in most cases be the same, so remove duplicates:
        return unique_preserving_order(
            extract_twitter_username(v) for v in
            self.contact_detail_values('twitter') +
            self.link_values('twitter'))

    @property
    def phone(self):
        return self.contact_detail_value('phone')

    @property
    def phone_all(self):
        return self.contact_detail_values('phone')

    @property
    def facebook(self):
        return self.link_value('facebook')

    @property
    def facebook_all(self):
        return self.link_values('facebook')

    @property
    def fax(self):
        return self.contact_detail_value('fax')

    @property
    def fax_all(self):
        return self.contact_detail_values('fax')

    def __repr__(self):
        return self.repr_helper(self.name)

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

    @property
    def links(self):
        return self.get_related_object_list('links')

    @property
    def contact_details(self):
        return self.get_related_object_list('contact_details')

    @property
    def identifiers(self):
        return self.get_related_object_list('identifiers')

    @property
    def images(self):
        return self.get_related_object_list('images')

    @property
    def other_names(self):
        return self.get_related_object_list('other_names')

    @property
    def sources(self):
        return self.get_related_object_list('sources')

    @property
    def memberships(self):
        from .collections import MembershipCollection
        memberships_list = [
            m.data for m in self.all_popolo.memberships
            if m.person_id == self.id
        ]
        return MembershipCollection(memberships_list, self.all_popolo)

    __hash__ = PopoloObject.__hash__


class Organization(PopoloObject):

    class DoesNotExist(ObjectDoesNotExist):
        pass

    class MultipleObjectsReturned(MultipleObjectsReturned):
        pass

    @property
    def id(self):
        return self.data.get('id')

    @property
    def name(self):
        return self.data.get('name')

    @property
    def wikidata(self):
        return self.identifier_value('wikidata')

    @property
    def classification(self):
        return self.data.get('classification')

    @property
    def image(self):
        return self.data.get('image')

    @property
    def founding_date(self):
        return self.get_date('founding_date', None)

    @property
    def dissolution_date(self):
        return self.get_date('dissolution_date', None)

    @property
    def seats(self):
        return self.data.get('seats')

    @property
    def other_names(self):
        return self.data.get('other_names', [])

    def __repr__(self):
        return self.repr_helper(self.name)

    @property
    def identifiers(self):
        return self.get_related_object_list('identifiers')

    @property
    def links(self):
        return self.get_related_object_list('links')


class Membership(CurrentMixin, PopoloObject):

    class DoesNotExist(ObjectDoesNotExist):
        pass

    class MultipleObjectsReturned(MultipleObjectsReturned):
        pass

    @property
    def role(self):
        return self.data.get('role')

    @property
    def person_id(self):
        return self.data.get('person_id')

    @property
    def person(self):
        return self.all_popolo.persons.lookup_from_key[self.person_id]

    @property
    def organization_id(self):
        return self.data.get('organization_id')

    @property
    def organization(self):
        collection = self.all_popolo.organizations
        return collection.lookup_from_key[self.organization_id]

    @property
    def area_id(self):
        return self.data.get('area_id')

    @property
    def area(self):
        return self.all_popolo.areas.lookup_from_key[self.area_id]

    @property
    def legislative_period_id(self):
        return self.data.get('legislative_period_id')

    @property
    def legislative_period(self):
        collection = self.all_popolo.events
        return collection.lookup_from_key[self.legislative_period_id]

    @property
    def on_behalf_of_id(self):
        return self.data.get('on_behalf_of_id')

    @property
    def on_behalf_of(self):
        collection = self.all_popolo.organizations
        return collection.lookup_from_key[self.on_behalf_of_id]

    @property
    def post_id(self):
        return self.data.get('post_id')

    @property
    def post(self):
        return self.all_popolo.posts.lookup_from_key[self.post_id]

    @property
    def start_date(self):
        return self.get_date('start_date', ApproxDate.PAST)

    @property
    def end_date(self):
        return self.get_date('end_date', ApproxDate.FUTURE)

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

    @property
    def key_for_hash(self):
        return json.dumps(self.data, sort_keys=True)

    def __hash__(self):
        return hash(self.key_for_hash)


class Area(PopoloObject):

    @property
    def id(self):
        return self.data.get('id')

    @property
    def name(self):
        return self.data.get('name')

    @property
    def type(self):
        return self.data.get('type')

    @property
    def identifiers(self):
        return self.get_related_object_list('identifiers')

    @property
    def other_names(self):
        return self.get_related_object_list('other_names')

    @property
    def wikidata(self):
        return self.identifier_value('wikidata')

    def __repr__(self):
        return self.repr_helper(self.name)


class Post(PopoloObject):

    @property
    def id(self):
        return self.data.get('id')

    @property
    def label(self):
        return self.data.get('label')

    @property
    def organization_id(self):
        return self.data.get('organization_id')

    @property
    def organization(self):
        collection = self.all_popolo.organizations
        return collection.lookup_from_key[self.organization_id]

    def __repr__(self):
        return self.repr_helper(self.label)


class Event(CurrentMixin, PopoloObject):

    @property
    def id(self):
        return self.data.get('id')

    @property
    def name(self):
        return self.data.get('name')

    @property
    def classification(self):
        return self.data.get('classification')

    @property
    def start_date(self):
        return self.get_date('start_date', ApproxDate.PAST)

    @property
    def end_date(self):
        return self.get_date('end_date', ApproxDate.FUTURE)

    @property
    def organization_id(self):
        return self.data.get('organization_id')

    @property
    def organization(self):
        collection = self.all_popolo.organizations
        return collection.lookup_from_key[self.organization_id]

    def __repr__(self):
        return self.repr_helper(self.name)

    @property
    def identifiers(self):
        return self.get_related_object_list('identifiers')

    @property
    def memberships(self):
        from .collections import MembershipCollection
        memberships_list = [
            m.data for m in self.all_popolo.memberships
            if m.legislative_period_id == self.id
        ]
        return MembershipCollection(memberships_list, self.all_popolo)