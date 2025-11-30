from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field, ValidationError, create_model


class Position(str, Enum):
    FIRST = "first"
    MIDDLE = "middle"
    LAST = "last"

class Gender(str, Enum):
    DIVERSE = "d"
    FEMALE = "f"
    MALE = "m"
    NOINFO = "-"

class Person(BaseModel):
    last: str
    first: str
    aoi: bool
    position: Position
    user: str | None = None
    approved: bool | None = None
    sws: int | None = None


class SplitDate(BaseModel):
    year: Annotated[int, Field(gt=1800, lt=2100)]
    month: Annotated[int, Field(ge=1, le=12)]
    day: Annotated[int, Field(ge=1, le=31)]


MODULES = {
    "authors": {"authors": Annotated[list[Person], Field(min_length=1)]},
    "author-table": {"authors": Annotated[list[Person], Field(min_length=1)]},
    "book-series": {"series": (str | None)},
    "book-title": {"book": (str | None)},
    "city": {"city": (str | None)},
    "conference": {"conference": (str | None)},
    "correction": {"correction": (bool | None)},
    "date-range": {"start": SplitDate, "end": SplitDate},
    "date-range-ongoing": {"start": SplitDate, "end": None},
    "date": {
        f_name: Annotated[
            f_info.asdict()["annotation"] | None,
            *f_info.asdict()["metadata"],
            Field(**f_info.asdict()["attributes"]),
        ]
        for f_name, f_info in SplitDate.model_fields.items()
    },
    "details": {"details": (str | None)},
    "doctype": {"doc_type": (str | None)},
    "doi": {"str": Annotated[str, Field(pattern="^10\..*")]},
    "edition": {"edition": Annotated[int, Field(ge=1)]},
    "editors": {"editors": list[Person]},
    "editorial": {"editor_type": (str | None)},
    "event-select": {
            # Only frontend?
        },
    "funding_type": {
        "funding_type": (str | None)
    },
    "guest-category": { "category": (str | None)},
    "gender": (Gender | None),
    "nationality": {"country": Annotated[str, Field()]}
    # TODO: continue
}


# TODO:
# Change iteration from modules to fields (see AdminTypes in Mongo) to check which fields are defined as required
#
# NOTE:
# Find out if changing default enum values is written to mongo and where
# Find out if fields list has same naming convention as module list (AdminTypes in MongoDB)

def parse_admin_field(field : dict):
    pass

def build_validator(key, type_fields: list[str], admin_fields: list[dict]):
    data_structure = {}

    # Get ids from admin_fields
    admin_fields_ids = [f["id"] for f in admin_fields]
    admin_fields_dict = zip(admin_fields_ids, admin_fields)

    # Mandatory for OSIRIS functioning:
    if not "date" in type_fields:
        type_fields.append("date")

    type_field_names = [tf["id"] for tf in type_fields if tf["type"] == "field"]

    # Main loop on modules
    for mod in type_field_names:
        mod = mod.strip("*")
        if mod in admin_fields_dict.keys(): # first check admin field for new altered definitions and custom fields
            data_structure[mod] = parse_admin_field(admin_fields_dict[mod])
        elif mod in MODULES: # find field in default list
            for field_name, field_info in MODULES[mod].items():
                data_structure[field_name] = field_info
        else:
            raise KeyError(f"OSIRIS configuration fail: Could not find module or field named '{mod}'") # critical failure
    return create_model(key, **data_structure)


def getValidators(admin_types: list[dict], admin_fields: list[dict]) -> dict:
    '''
    
    Input:
        types: List of all types from collection 'AdminTypes'
        fields: List of all fields from collection 'AdminFields'

    Output:
        dict where keys are [type]-[subtype] of all defined activity types in OSIRIS and value are pydantic classes to validate the 
    '''
    validators = {}
    for t in admin_types:
        key = f"{t['type']}-{t['subtype']}"
        validators[key] = build_validator(key, t["fields"], admin_fields)
    return validators
