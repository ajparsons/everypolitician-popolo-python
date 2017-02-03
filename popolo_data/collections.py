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

    def append(self,new):
        new.all_popolo = self.all_popolo
        self.lookup_from_key[new.key_for_hash] = new
        self.object_list.append(new)
        
    add = append

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

    def merge(self,other,new_collection,unique_on="id"):
        """
        returns a new collection that fuses itself with an 'other' collection
        of same class.
        Where the same unique_on value exists in both - the 'larger' is kept
        
        more complex merges can be added by overriding PopoloObject.absorb
        """
        
        new = new_collection
                
        amend_ids = unique_on != "id" #if not unique on ids, will need to amend backwards
        ids_to_change = []
        
        ours = set([getattr(x,unique_on) for x in self])
        theirs = set([getattr(x,unique_on) for x in other])
        our_lookup = {getattr(x,unique_on):x for x in self}
        their_lookup = {getattr(x,unique_on):x for x in other}
        
        both = ours.union(theirs)
        contested = ours.intersection(theirs)
        uncontested = both.difference(contested)
        
        for c in contested:
            o = our_lookup[c]
            t = their_lookup[c]
            
            if o < t: #if theirs has more information, keep
                keep,lose = t,o
            else:
                keep,lose = o,t
            
            keep.absorb(lose) #runs any model level synchronization
            
            new.add(keep)
            ids_to_change.append((lose.id,keep.id))       
            
        for u in uncontested:
            o = our_lookup.get(u,None)
            t = their_lookup.get(u,None)

            if o and not t:
                new.add(o)
            elif t and not o:
                new.add(t)
        
        if amend_ids == False:
            ids_to_change = []
        
        merge_message = "merging {0} on {1}: {2} + {3} = {4}. {5} ids to change."
            
        print (merge_message.format(self.__class__.object_class.__name__,
                                   unique_on,
                                   len(self),
                                   len(other),
                                   len(new),
                                   len(ids_to_change)))
        
        return ids_to_change



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
