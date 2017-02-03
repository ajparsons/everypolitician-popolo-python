"""
Classes to define the different Popolo collections

"""
import json

from .models import Person, Organization, Membership, Area, Post, Event
from .base import first

class PopoloCollection(object):

    object_class = None

    def __init__(self, data_list , all_popolo):
        self.all_popolo = all_popolo
        self.object_class = self.__class__.object_class
        self.object_list = \
            [self.object_class(data, all_popolo) for data in data_list]
        self.lookup_from_key = {}
        for o in self.object_list:
            self.lookup_from_key[o.key_for_hash] = o

    def __len__(self):
        return len(self.object_list)

    def json(self):
        return json.dumps(self.raw_data())

    def raw_data(self):
        return [x.data for x in self.object_list]

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
    object_class = Person

class OrganizationCollection(PopoloCollection):
    object_class = Organization

class MembershipCollection(PopoloCollection):
    object_class = Membership

class AreaCollection(PopoloCollection):
    object_class = Area

class PostCollection(PopoloCollection):
    object_class = Post

class EventCollection(PopoloCollection):
    object_class = Event
    
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
