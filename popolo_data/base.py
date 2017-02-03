from datetime import date
import json
import re


from approx_dates.models import ApproxDate

import six

def first(l):
    '''Return the first item of a list, or None if it's empty'''
    return l[0] if l else None


class ObjectDoesNotExist(Exception):
    pass


class MultipleObjectsReturned(Exception):
    pass

class PopoloObject(object):

    def __init__(self, data, all_popolo):
        self.data = data
        self.all_popolo = all_popolo

    def get_date(self, attr, default):
        d = self.data.get(attr)
        if d:
            return ApproxDate.from_iso8601(d)
        return default

    def get_related_object_list(self, popolo_array):
        return self.data.get(popolo_array, [])

    def get_related_values(
            self, popolo_array, info_type_key, info_type, info_value_key):
        '''Get a value from one of the Popolo related objects

        For example, if you have a person with related links, like
        this:

            {
                "name": "Dale Cooper",
                "links": [
                    {
                        "note": "wikipedia",
                        "url": "https://en.wikipedia.org/wiki/Dale_Cooper"
                    }
                ]
            }

        When calling this method to get the Wikipedia URL, you would use:

            popolo_array='links'
            info_type_key='note'
            info_type='wikipedia'
            info_value_key='url'

        ... so the following would work:

            self.get_related_value('links', 'note', 'wikipedia', 'url')
            # => 'https://en.wikipedia.org/wiki/Dale_Cooper'
        '''
        return [
            o[info_value_key]
            for o in self.get_related_object_list(popolo_array)
            if o[info_type_key] == info_type]

    def identifier_values(self, scheme):
        return self.get_related_values(
            'identifiers', 'scheme', scheme, 'identifier')

    def identifier_value(self, scheme):
        return first(self.identifier_values(scheme))

    def link_values(self, note):
        return self.get_related_values('links', 'note', note, 'url')

    def link_value(self, note):
        return first(self.link_values(note))

    def contact_detail_values(self, contact_type):
        return self.get_related_values(
            'contact_details', 'type', contact_type, 'value')

    def contact_detail_value(self, contact_type):
        return first(self.contact_detail_values(contact_type))

    @property
    def key_for_hash(self):
        return self.id

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.id == other.id
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return self.id != other.id
        return NotImplemented

    def __hash__(self):
        return hash(self.key_for_hash)

    def repr_helper(self, enclosed_text):
        fmt = str('<{0}: {1}>')
        class_name = type(self).__name__
        if six.PY2:
            return fmt.format(class_name, enclosed_text.encode('utf-8'))
        return fmt.format(class_name, enclosed_text)


class CurrentMixin(object):

    def current_at(self, when):
        return ApproxDate.possibly_between(
            self.start_date, when, self.end_date)

    @property
    def current(self):
        return self.current_at(date.today())






