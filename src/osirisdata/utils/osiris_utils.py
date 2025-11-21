from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field, ValidationError, create_model


class AuthorPosition(str, Enum):
    FIRST = 'first'
    MIDDLE = 'middle'
    LAST = 'last'

class Author(BaseModel):
    last : str
    first : str
    aoi : bool
    position : AuthorPosition
    user : str | None = None
    approved : bool | None = None
    sws : int | None = None

class SplitDate(BaseModel):
    year: Annotated[int, Field(gt=1800, lt=2100)]
    month: Annotated[int, Field(ge=1, le=12)]
    day: Annotated[int, Field(ge=1, le=31)]



MODULES = {
    "authors": {
        "authors": Annotated[list[Author], Field(min_length=1)]
    },
    "author-table": {
        "authors": Annotated[list[Author], Field(min_length=1)]
    },
    "book-series" : {
        "series": (str | None)
    },
    "book-title" : {
        "book": (str | None)
    },
    "city": {
        "city": (str | None)
    },
    "conference": {
        "conference": (str | None)
    },
    "correction": {
        "correction": (bool | None)
    },
    "date-range": {
        "start": SplitDate,
        "end": SplitDate
    },
    "date-range-ongoing":{
        "start": SplitDate,
        "end": None
    },
    "date": {
        f_name: Annotated[f_info.asdict()['annotation'] | None, *f_info.asdict()['metadata'], Field(**f_info.asdict()['attributes'])]
        for f_name, f_info in SplitDate.model_fields.items()
    },
    "details":{
        "details": (str | None)
    },
    "doctype": {
        "doc_type": (str | None)
    },
    "doi":{
        "str": Annotated[str, Field()]
    }
}

def build_validator(key, modules: list[str], field_dict):
    data_structure = {}
    for mod in modules:
        mod = mod.strip("*")
        if mod in field_dict:
            data_structure[mod] = field_dict[mod]
        elif mod in MODULES:
            for field_name, field_info in MODULES[mod].items():
                data_structure[field_name] = field_info
        else:
            raise KeyError(f"Could not find module or field named: {mod}")
    return create_model(key, **data_structure)



def getValidators(types: list[dict], fields:list[dict]) -> dict:
    validators = {}
    field_dict = {field["id"]: field["format"] for field in fields}
    for t in types:
        key = f"{t['type']}-{t['subtype']}"
        validators[key] = build_validator(key, t["modules"], field_dict)
    return validators