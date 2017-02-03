"""
Classes to define the different Popolo collections

"""

from .models import Person, Organization, Membership, Area, Post, Event
from .base import first

class PopoloCollection(object):

    def __init__(self, data_list, object_class, all_popolo):
        self.all_popolo = all_popolo
        self.object_class = object_class
        self.object_list = \
            [self.object_class(data, all_popolo) for data in data_list]
        self.lookup_from_key = {}
        for o in self.object_list:
            self.lookup_from_key[o.key_for_hash] = o

    def __len__(self):
        return len(self.object_list)

    def __getitem__(self, index):
        return self.object_list[index]

    @property
    def first(self):
        return first(self.object_list)

    def filter(self, **kwargs):
        filter_list = [
            o.data for o in self.object_list
            if all(getattr(o, k) == v for k, v in kwargs.items())
        ]
        return self.__class__(filter_list, self.all_popolo)

    def get(self, **kwargs):
        matches = self.filter(**kwargs)
        n = len(matches)
        if n == 0:
            msg = "No {0} found matching {1}"
            raise self.object_class.DoesNotExist(msg.format(
                self.object_class, kwargs))
        elif n > 1:
            msg = "Multiple {0} objects ({1}) found matching {2}"
            raise self.object_class.MultipleObjectsReturned(msg.format(
                self.object_class, n, kwargs))
        return matches[0]


class PersonCollection(PopoloCollection):

    def __init__(self, persons_data, all_popolo):
        super(PersonCollection, self).__init__(
            persons_data, Person, all_popolo)


class OrganizationCollection(PopoloCollection):

    def __init__(self, organizations_data, all_popolo):
        super(OrganizationCollection, self).__init__(
            organizations_data, Organization, all_popolo)


class MembershipCollection(PopoloCollection):

    def __init__(self, memberships_data, all_popolo):
        super(MembershipCollection, self).__init__(
            memberships_data, Membership, all_popolo)


class AreaCollection(PopoloCollection):

    def __init__(self, areas_data, all_popolo):
        super(AreaCollection, self).__init__(
            areas_data, Area, all_popolo)


class PostCollection(PopoloCollection):

    def __init__(self, posts_data, all_popolo):
        super(PostCollection, self).__init__(
            posts_data, Post, all_popolo)


class EventCollection(PopoloCollection):

    def __init__(self, events_data, all_popolo):
        super(EventCollection, self).__init__(
            events_data, Event, all_popolo)

    @property
    def elections(self):
        elections_list = self.filter(classification='general election')
        elections_data = [election.data for election in elections_list]
        return EventCollection(elections_data, self.all_popolo)

    @property
    def legislative_periods(self):
        lps_list = self.filter(classification='legislative period')
        legislative_periods_data = [lp.data for lp in lps_list]
        return EventCollection(legislative_periods_data, self.all_popolo)
