#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import requests

from .collections import (
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
        if json_data == None:
            json_data = {}
        self.json_data = json_data
        json_get = self.json_data.get
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
    def latest_term(self):
        return self.latest_legislative_period
