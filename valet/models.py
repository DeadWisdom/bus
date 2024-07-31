from .bus import Object, Strings, Functional, References
from .bus.objects import Person

class Place(Object):
    type: Strings = 'Place'
    latitude: Functional[str]
    longitude: Functional[str]
    address: References


class Organization(Object):
    type: Strings = 'Organization'


class Document(Object):
    type: Strings = 'Document'


# Extensions
class License(Object):
    type: Strings = 'License'
    status: Strings


class PostalAddress(Object):
    type: Strings = 'PostalAddress'
    street_address: Strings
    address_locality: Strings
    address_region: Strings
    postal_code: Strings


class Account(Person):
    type: Strings = 'Account'
    email: Strings
    oauth: Strings
