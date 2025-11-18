from enum import Enum

from pydantic import BaseModel, ValidationError, create_model


class AuthorPosition(str, Enum):
    FIRST = 'first'
    MIDDLE = 'middle'
    LAST = 'last'

class Author(BaseModel):
    last : str
    first : str
    aoi : bool
    position : AuthorPosition
    user : str
    approved : bool
    sws : int

MODULES = {
    "authors": 
}

def build_validator(key, modules: list[str], field_dict):
    data_structure = {}
    for mod in modules:
        mod = mod.strip("*")
        if mod in field_dict:
            data_structure[mod] = field_dict[mod]
        elif mod in MODULES:
            data_structure[mod] = MODULES[mod]
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