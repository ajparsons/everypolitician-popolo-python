#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import requests
import io
import six
from copy import deepcopy

from .collections import (PopoloCollection,
    AreaCollection, EventCollection, MembershipCollection, PersonCollection,
    OrganizationCollection, PostCollection)

class NotAValidType(TypeError):
    pass

class Popolo(object):

    @classmethod
    def from_filename(cls, filename):
        with open(filename) as f:
            return cls(json.load(f))

    @classmethod
    def from_url(cls, url):
        r = requests.get(url)
        return cls(r.json())

    @classmethod
    def new(cls):
        return cls({})

    def __init__(self, json_data=None):
        if json_data == None: #insulate from other instances
            json_data = {}
        json_data = deepcopy(json_data)
        json_get = json_data.get
        self.persons = PersonCollection(json_get('persons', []), self)
        self.organizations = OrganizationCollection(json_get('organizations', []), self)
        self.memberships =  MembershipCollection(json_get('memberships', []), self)
        self.areas = AreaCollection(json_get('areas', []), self)
        self.posts = PostCollection(json_get('posts', []), self)
        self.events = EventCollection(json_get('events', []), self)
   
    @property
    def elections(self):
        return self.events.elections

    @property
    def legislative_periods(self):
        return self.events.legislative_periods

    @property
    def terms(self):
        return self.legislative_periods

    @property
    def latest_legislative_period(self):
        lps = self.legislative_periods
        return max(lps, key=lambda lp: lp.start_date.midpoint_date)

    @property
    def collections(self):
        return [[k,v] for k,v in six.iteritems(self.__dict__)\
                if isinstance(v,PopoloCollection)]

    @property
    def latest_term(self):
        return self.latest_legislative_period

    def add(self,new):
        """
        find the correct collection for the object and add it
        """
        if isinstance(new,list):
            ll = new
        else:
            ll = [new]
        
        to_return = []
        for l in ll:
            for k,collection in self.collections:
                if isinstance(l,collection.object_class):
                    to_return.append(collection.add(l))
                    break
        
        if len(to_return) != len(ll):
            raise NotAValidType("This type can't be used with Popolo.")

    def to_filename(self,filename):
        di = {k:v.raw_data() for k,v in self.collections}
        content = json.dumps(di,indent=4, sort_keys=True, ensure_ascii=False)
        with io.open(filename, 'w', encoding='utf8') as json_file:
            json_file.write(content)

    @property
    def json_data(self):
        return {k:v.raw_data() for k,v in self.collections}

    def to_json(self):
        return json.dumps(self.json_data,
                          indent=4,
                          sort_keys=True
                          ,
                          ensure_ascii=False)      

    def amend_ids(self,id_list):
        """
        expects a list of id replacements
        [[a,1],[b,2]].
        Will replace the 'old' id across all objects.
        When two popolos are being merged, one set of ids needs to take
        priority. 
        """
        for k,v in self.collections:
            for old,new in id_list:
                if old != new:
                    for o in v.object_list:
                        for prop in six.iterkeys(o.__class__.__dict__):
                            if "_id" in prop:
                                if getattr(o,prop) == old:
                                    setattr(o,prop,new)
                                    
    def merge(self,other):
        """
        combine with another popolo, preserving specified id field
        """
        #we need to make copies
        
        safe_ours = self.__class__(self.json_data)
        safe_other = self.__class__(other.json_data)
        new = self.__class__({})
        
        process_order = [
                        ("organizations","name"),#unique on name
                        ("events","id"), #unique on id
                        ("persons","name"),
                        ("areas","name"),
                        ("posts","id"),
                        ("memberships","id"),
                        ]
    
        for p,merge_value in process_order:

            our_col = getattr(safe_ours,p)
            their_col = getattr(safe_other,p)
            new_col = getattr(new,p)
            
            ids_to_change = our_col.merge(their_col,new_col,merge_value)
            safe_ours.amend_ids(ids_to_change)
            safe_other.amend_ids(ids_to_change)
            
        return new
