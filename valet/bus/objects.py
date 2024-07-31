from typing import Annotated, Any, TypeVar, Union
from collections.abc import Iterable, Mapping, Iterator
from datetime import datetime
from pydantic import (
    BaseModel,
    ConfigDict,
    SerializationInfo,
    Field,
    model_serializer,
    model_validator,
)
from pydantic.alias_generators import to_camel
from pydantic.functional_validators import BeforeValidator
from pydantic.functional_serializers import PlainSerializer


### Helper Functions
def fix_camels(data):
    match data:
        case dict():
            return {to_camel(k): fix_camels(v) for k, v in data.items()}
        case [*items]:
            return [fix_camels(i) for i in items]
        case _:
            return data


def make_a_list(value) -> list:
    """
    Used to convert a value into a list if it isn't already.
    """
    match value:
        case None:
            return []
        case [*items]:
            return list(items)
        case _:
            return [value]


def make_not_a_list(value):
    """
    Used to convert a list to a singular value if it is a list.
    """
    match value:
        case [first, *rest] if not rest:
            return first
        case _:
            return value


def make_a_node(value):
    """
    Used to convert a value into a node if it isn't already.
    """
    match value:
        case str():
            return {"id": value}
    return value


def default_strings(*values: tuple[str], **kwargs):
    """
    Makes a field with a default value of a list of given values.
    """
    return Field(default_factory=lambda: list(values), **kwargs)

def TypeField(name: str, **kwargs):
    return default_strings(name, **kwargs)

def chain(*values: tuple[Any]):
    for value in values:
        match value:
            case None:
                return
            case [*items]:
                yield from items
            case str() | Mapping() | BaseModel():
                yield value
            case Iterable():
                yield from value
            case item:
                yield item


def first(*values: tuple[Any]):
    return next(chain(*values))


def gather(*values: tuple[Any]):
    return list(chain(*values))


def get_id(obj: Any) -> str | None:
    match obj:
        case str():
            return obj
        case LDObject(id=id):
            return id
        case None:
            return None
        case _:
            raise RuntimeError(f"Cannot get id from object: {obj!r}")


def first_id(*values: tuple[Any]) -> str | None:
    return get_id(first(*values))


def chain_ids(*values: tuple[Any]) -> Iterator[str]:
    for obj in chain(*values):
        if id := get_id(obj):
            yield id


def gather_ids(*values: tuple[Any]) -> list[str]:
    return list(chain_ids(*values))


### Types
T = TypeVar("T")
Functional = Annotated[T | None, Field(default=None)]
Values = Annotated[
    list[T],
    Field(default_factory=list, validate_default=True),
    BeforeValidator(make_a_list),
    PlainSerializer(make_not_a_list, when_used="json"),
]
Strings = Values[str]
Node = Annotated[Union[str, 'LDObject'], PlainSerializer(make_a_node, when_used="always")]
References = Values[Node]
Links = Values[Union[str, 'Link']]
JSONPrimitives = str | int | float | bool | datetime
JSONable = Union[JSONPrimitives, dict[str, JSONPrimitives], list[JSONPrimitives]]


class LDObject(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="allow", coerce_numbers_to_str=True)

    id: Functional[str]
    type: Strings

    def __repr_args__(self):
        """
        Tells pydantic to not show properties that are None or empty lists
        """
        for k, v in super().__repr_args__():
            match v:
                case None:
                    continue
                case []:
                    continue
            yield k, v

    @model_validator(mode="after")
    def remove_exta_underscores(self) -> "LDObject":
        """
        Removes any key in our model_extra that startswith an underscore which happens in some
        places like when we get _collection back in our elastic results.
        """
        remove = [k for k in self.model_extra.keys() if k.startswith("_")]
        for k in remove:
            del self.model_extra[k]
        return self

    @model_serializer(mode="wrap", return_type=dict)
    def serialize_model(self, handler, info: SerializationInfo) -> dict:
        """
        Tells pydantic to not serialize properties that are None or empty lists or start with '_'

        Also steals the context and puts in the top level object
        """
        context = {}
        if info.context:
            context.update(info.context)
            info.context.clear()
        value = handler(self)
        for k in tuple(value.keys()):
            if k.startswith("_"):
                del value[k]
            else:
                v = value[k]
                if v in ([], None):
                    del value[k]
        if info.mode_is_json():
            for k, v in value.items():
                match v:
                    case {'id': id, **rest} if not rest:  # Convert {'id': 'http://example.com'} to 'http://example.com'
                        value[k] = id
        value.update(context)
        return value



### Basic Models
class Link(LDObject):
    href: Functional[str]
    rel: Strings
    media_type: Functional[str]
    name: Strings
    href_lang: Functional[str]
    height: Functional[int]
    width: Functional[int]
    preview: References


class Object(LDObject):
    name: Strings
    summary: Strings
    content: Values[JSONable]
    image: References
    icon: References
    location: References
    attributed_to: References
    audience: References
    context: References
    generator: References
    duration: Functional[float]
    published: Functional[datetime]
    updated: Functional[datetime]
    start_time: Functional[datetime]
    end_time: Functional[datetime]
    in_reply_to: References
    replies: References
    tag: References
    url: Links
    to: References
    bto: References
    cc: References
    bcc: References
    media_type: Functional[str]


class Tombstone(Object):
    type: Strings = TypeField("Tombstone")
    former_type: Strings
    deleted: Functional[datetime]

    @classmethod
    def from_object(cls, obj: Object):
        data = obj.model_dump()
        data["type"] = "Tombstone"
        data["former_type"] = obj.type
        data["deleted"] = datetime.now()
        return cls.model_validate(data)


### Collections
class Collection(Object):
    total_items: Functional[int]
    items: list[Node] | None = None
    current: Functional["CollectionPage | str"]
    first: Functional["CollectionPage | str"]
    last: Functional["CollectionPage | str"]


class CollectionPage(Collection):
    part_of: Functional[Collection | str]
    items: list[Node] | None = None
    next: Functional["CollectionPage | str"]
    prev: Functional["CollectionPage | str"]


class OrderedCollection(Object):
    total_items: Functional[int]
    items: list[Node] | None = None
    ordered_items: list[Node] | None = None
    first: Functional["OrderedCollectionPage | str"]
    last: Functional["OrderedCollectionPage | str"]


class OrderedCollectionPage(OrderedCollection):
    part_of: Functional[OrderedCollection | str]
    ordered_items: list[Node] | None = None
    next: Functional["OrderedCollectionPage | str"]
    prev: Functional["OrderedCollectionPage | str"]


### Content Models
class Document(Object):
    type: Strings = "Document"


class Article(Object):
    type: Strings = "Article"


class Page(Object):
    type: Strings = "Page"


class Profile(Object):
    type: Strings = "Profile"


### People ###
class Actor(Object):
    type: Strings = "Actor"


class Person(Actor):
    type: Strings = "Person"


### Activity
class Activity(Object):
    actor: References
    object: References
    target: References
    result: References
    origin: References
    instrument: References


class IntransitiveActivity(Object):
    actor: References
    target: References
    result: References
    origin: References
    instrument: References

class Error(Object):
    type: Strings = "Error"



### Storage ###
class ObjectQuery(LDObject):
    """
    Used for querying the database.

    All parts are assumed to be inclusive (OR), which is to say if you specify two different types
    you will get ALL objects that match any of the types.
    """

    type: Strings
    term: str = None
    context: References
    collection: References
    since: datetime = None
    page: int = 0
    size: int = 50


### Rebuild

Link.model_rebuild()
Object.model_rebuild()