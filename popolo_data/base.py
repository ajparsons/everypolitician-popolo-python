
from datetime import date, datetime
from approx_dates.models import ApproxDate
import calendar
import six
import json
from copy import deepcopy

def approx_date_to_iso(approx_date):
    #duplicated here until approx_date package updated
    
    if approx_date.earliest_date == approx_date.latest_date:
        return approx_date.earliest_date.isoformat()
    else:
        #is it a vague month?
        ed = approx_date.earliest_date
        ld = approx_date.latest_date
        if ed.month == ld.month and ed.year == ld.year:
            days_in_month = calendar.monthrange(ed.year, ed.month)[1]
            if ed.day == 1 and ld.day == days_in_month:
                return ed.strftime("%Y-%m")
        #is it a vague year
        if ed.year == ld.year:
            if ed.month == 1 and ed.day == 1:
                if ld.month == 12 and ld.day == 31:
                    return "{0}".format(ed.year)

    return "{0} to {1}".format(ed.isoformat(),ld.isoformat())

def approx_date_getter(iso8601_date_string):
    #duplicated here until approx_date package updated
        if " to " in iso8601_date_string: #extract double date
            start,end = iso8601_date_string.split(" to ")
            start_date = ApproxDate.from_iso8601(start)
            end_date = ApproxDate.from_iso8601(end)
            combined = ApproxDate(start_date.earliest_date,
                                  end_date.latest_date,
                                  iso8601_date_string)
            return combined
        else:
            return ApproxDate.from_iso8601(iso8601_date_string)  


def first(l):
    '''Return the first item of a list, or None if it's empty'''
    return l[0] if l else None

class Attribute(object):
    '''
    Exposes raw json values for getting and setting.
    
    Works in conjecture with PopoloObject
    
    so:
    
    id = Attribute()
    
    will give a PopoloObject with an id attribute that gets and
    sets the 'id' attr of self.data.
    
    id = Attribute(default="16")
    
    Sets a default extraction value of 16.
    
    id = Attribute(null=True)
    
    will return None rather than an error if the value is absent.
    
    '''
    def __init__(self,attr="",default=None,null=False,allow_multiple=False):
        self.attr = attr
        self._default_value = default
        self.allow_null_default = null
        self.allow_multiple = allow_multiple

    @property
    def default_value(self):
        """
        safe guard against default being shared between instances
        """
        return deepcopy(self._default_value)
    
    def __get__(self, obj, type=None):
        if self.allow_null_default == False and self.default_value == None:
            return obj.data.get(self.attr)
        else:
            try:
                result = obj.data[self.attr]
            except KeyError:
                result = self.default_value
                obj.data[self.attr] = result
            return result

    def __set__(self,obj,value):
        if six.PY2 and isinstance(value,str):
            nv = unicode(value)
        else:
            nv = value
        
        obj.data[self.attr] = nv

class RelatedAttribute(Attribute):
    """
    returns 'related' objects - e.g. if person_id = 5, returns Person 5
    """
    def __init__(self,attr="",default=None,null=False,
                 id_attr=None,collection=None):
        self.attr = attr
        self._default_value = default
        self.allow_null_default = null
        self._collection = collection
            
    @property
    def id_attr(self):
            return self.attr + "_id"
          
    @property  
    def collection(self):
        if self._collection:
            return self._collection
        else:
            return self.attr + "s"   
         
    def __get__(self, obj, type=None):
        collection = getattr(obj.all_popolo,self.collection)
        return collection.lookup_from_key[getattr(obj,self.id_attr)]
    
    def __set__(self,obj,value):
        setattr(obj,self.id_attr,value.id)

class DateAttribute(Attribute):
    """
    Interacts with ApproxDates - sets iso, retrieves ApproxDate
    """
    def __get__(self, obj, type=None):
            return obj.get_date(self.attr,self.default_value)
    
    def __set__(self,obj,value):
        if isinstance(value,ApproxDate):
            obj.data[self.attr] = approx_date_to_iso(value)
        elif isinstance(value,datetime):
            obj.data[self.attr] = value.date().isoformat()
        elif isinstance(value,date):
            obj.data[self.attr] = value.isoformat()
        else:
            obj.data[self.attr] = value


class IdentiferAttribute(Attribute):
    """
    For getting and setting values deeper in linked data.
    """
    getter = "identifier_values"
    
    def __get__(self, obj, type=None):
        getter = getattr(obj,self.__class__.getter)
        v = getter(self.attr)
        if v:
            if self.allow_multiple:
                return v
            else:
                return first(v)
        else:
            return self.default_value
        
    def __set__(self,obj,value):
        setter = getattr(obj,"set_" + self.__class__.getter)
        setter(self.attr,value)
        
class LinkAttribute(IdentiferAttribute):
    getter = "link_values"
    
class ContactAttribute(IdentiferAttribute):
    getter = "contact_detail_values"

class PopoloMeta(type):
    
    def __new__(cls, name, parents, dct):
        
        """
        If attr value not specified for an attribute, gives it the name assigned.
        
        This specifies the key of the popolo dict the property refers to.
        
        so 
        
        name = Attribute()
        
        is equivalent to:
        
        name = Attribute(attr="name")
        """
        
        for k,v in six.iteritems(dct):
            if isinstance(v,Attribute) :
                if v.attr == "":
                    v.attr = k 

        cls = super(PopoloMeta, cls).__new__(cls, name, parents, dct)
        return cls
 

class PopoloObject(six.with_metaclass(PopoloMeta,object)):

    class DoesNotExist(Exception):
        pass

    class MultipleObjectsReturned(Exception):
        pass

    def __init__(self, data=None, all_popolo=None,**kwargs):
        if data == None:
            data = {}
        data.update(kwargs)
        self.data = data
        self.all_popolo = all_popolo

    @property
    def json(self):
        return json.dumps(self.data)

    def get_date(self, attr, default):
        d = self.data.get(attr)
        if d:
            return approx_date_getter(d)
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
            if o[info_type_key] == info_type
            ]

    def del_related_values(self,popolo_array, info_type_key, info_type):
        obj_list = self.get_related_object_list(popolo_array)
        if obj_list:
            for x,o in enumerate(obj_list):
                if o[info_type_key] == info_type:
                    break
            
            if obj_list[x][info_type_key] == info_type:
                del obj_list[x]
            

    def set_related_values(self, popolo_array
                           , info_type_key, info_type, info_value_key,new_value):
        """
        allows related values to be set
        """
        
        obj_list = self.get_related_object_list(popolo_array)
        for o in obj_list:
            if o[info_type_key] == info_type:
                o[info_value_key] = new_value
                return
        new = {info_type_key:info_type,
               info_value_key:new_value}
        obj_list.append(new)
        self.data[popolo_array] = obj_list

    def identifier_values(self, scheme):
        return self.get_related_values(
            'identifiers', 'scheme', scheme, 'identifier')

    def set_identifier_values(self, scheme,value):
        """
        set an identifer value
        """
        self.set_related_values(
            'identifiers', 'scheme', scheme, 'identifier',value)

    def identifier_value(self, scheme):
        return first(self.identifier_values(scheme))

    def link_values(self, note):
        return self.get_related_values('links', 'note', note, 'url')

    def set_link_values(self, note,value):
        """
        set a link value
        """
        self.set_related_values('links', 'note', note, 'url',value)

    def del_link_values(self, note):
        """
        set a link value
        """
        self.del_related_values('links', 'note', note)


    def link_value(self, note):
        return first(self.link_values(note))

    def contact_detail_values(self, contact_type):
        return self.get_related_values(
            'contact_details', 'type', contact_type, 'value')

    def del_contact_detail_values(self, contact_type):
        return self.del_related_values(
            'contact_details', 'type', contact_type)
    
    def set_contact_detail_values(self, contact_type,new_value):
        if not new_value:
            return self.del_contact_detail_values(contact_type)
        else:
            return self.set_related_values(
                'contact_details', 'type', contact_type, 'value',new_value)

    def contact_detail_value(self, contact_type):
        return first(self.contact_detail_values(contact_type))

    def absorb(self,other):
        """
        other is about to be discarded for it's (hopefully) better
        equiv self.
        
        Override if there's anything you want to salvage from other
        and pass into self. 
        """
        pass

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

    def __lt__(self,other):
        """
        is this less "full" than the other?
        Based entirely on how much info is in there - len of dict.
        """
        if self.__class__ == other.__class__:
            ours = len(self.json)
            theirs = len(other.json)
            return ours < theirs
        else:
            return NotImplemented
        
    def __gt__(self,other):
        """
        is this more "full" than the other?
        Based entirely on how much info is in there - len of dict.
        """        
        if self.__class__ == other.__class__:
            ours = len(self.json)
            theirs = len(other.json)
            return ours > theirs
        else:
            return NotImplemented

    def __hash__(self):
        return hash(self.key_for_hash)

    def repr_helper(self, enclosed_text):
        fmt = str('<{0}: {1}>')
        class_name = type(self).__name__
        if six.PY2:
            return fmt.format(class_name, enclosed_text.encode('utf-8'))
        return fmt.format(class_name, enclosed_text)

    def __repr__(self):
        """
        generic __repr__ for different models - will repr with
        whichever value is present in object.
        """
        preferred_order = ["name","label","id"]
        for o in preferred_order:
            if hasattr(self,o):
                return self.repr_helper(getattr(self,o))


class CurrentMixin(object):

    def current_at(self, when):
        return ApproxDate.possibly_between(
            self.start_date, when, self.end_date)

    @property
    def current(self):
        return self.current_at(date.today())

