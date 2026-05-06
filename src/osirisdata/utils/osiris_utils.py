from typing import Annotated, Any, Literal

from pydantic import AnyUrl, BaseModel, Field, create_model

from pydantic_extra_types.isbn import ISBN

from pymongo.cursor import Cursor
from pymongo.database import Database
from datetime import date


class Person(BaseModel):
    last: str
    first: str
    aoi: bool
    position: Literal["first", "middle", "last"]
    user: str | None = None
    approved: bool | None = None
    sws: int | None = None


class SplitDate(BaseModel):
    year: Annotated[int, Field(gt=1800, lt=2100)]
    month: Annotated[int, Field(ge=1, le=12)]
    day: Annotated[int, Field(ge=1, le=31)]


MODULES: dict[str, dict[str, Any]] = {
    "authors": {"authors": Annotated[list[Person], Field(min_length=1)]},
    "author-table": {"authors": Annotated[list[Person], Field(min_length=1)]},
    "book-series": {"series": str},
    "book-title": {"book": str},
    "city": {"city": str},
    "conference": {"conference": str},
    "correction": {"correction": bool},
    "date-range": {"start": SplitDate, "end": SplitDate},
    "date-range-ongoing": {"start": SplitDate},
    "date": {
        f_name: Annotated[
            f_info.asdict()["annotation"],
            *f_info.asdict()["metadata"],
            Field(**f_info.asdict()["attributes"]),
        ]
        for f_name, f_info in SplitDate.model_fields.items()
    },
    "details": {"details": str},
    "doctype": {"doc_type": str},
    "doi": {"doi": Annotated[str, Field(pattern=r"^10\..*")]},
    "edition": {"edition": Annotated[int, Field(ge=1)]},
    "editors": {"editors": list[Person]},
    "editorial": {"editor_type": str},
    "event-select": {
        # Only frontend?
    },
    "funding_type": {"funding_type": str},
    "guest-category": {"category": str},
    "gender": {"gender": Literal["d", "f", "m", "-"]},
    
    "abstract": {"abstract": str},
    "isbn": {"isbn": ISBN},
    "issn": {"issn": Annotated[str, Field(pattern=r"^\d{4}-\d{4}$")]},
    "issue": {"issue": str},
    "iteration": {"iteration": Literal["once", "annual"]},
    "journal": {"journal": str, "journal_id": str},
    "lecture-invited": {"lecture_invited": bool},
    "lecture-type": {"lecture_type": Literal["short", "long", "repetition"]},
    "license": {"license": str},
    "link": {"link": AnyUrl},
    "location": {"location": str},
    "magazine": {"magazine": str},
    "online-ahead-of-print": {"epub": bool},
    "openaccess": {"open_access": bool},
    "openaccess-status": {
        "oa_status": (
            Literal["closed", "open", "diamond", "gold", "green", "hybrid", "bronze"]
        )
    },
    "pages": {"pages": str},
    "peer-reviewed": {"peer-reviewed": bool},
    "person": {
        "name": str,  # TODO: improve person name with pattern check
        "affiliation": str,
        "academic_title": str,
    },
    "person-only": {"name": str},  # TODO: improve person name with pattern check
    "person-organization": {"name": str, "organization": str},
    
    "pub-language": {"pub_language": Literal["de", "en", "fr", "es", "it", "other"]},
    "publisher": {"publisher": str},
    "pubmed": {"pubmed": int},
    "pubtype": {"pubtype": str},
    "review-type": {"review-type": str},
    "role": {"role": str},
    "scientist": {"authors": Annotated[list[Person], Field(min_length=1)]},
    "semester-select": {},
    "scope": {"scope": Literal["local", "regional", "national", "international"]},
    "software-link": {"link": AnyUrl},
    "software-type": {
        "software_type": Literal["software", "database", "dataset", "webtool", "report"]
    },
    "software-venue": {"software_venue": str},
    "status": {"status": Literal["in progress", "completed", "aborted"]},
    "student-category": {
        "category": (
            Literal[
                "bachelor thesis",
                "master thesis",
                "doctoral thesis",
                "internship",
                "other",
            ]
        )
    },
    
    "thesis": {
        "category": (Literal["bachelor", "master", "diploma", "doctor", "habilitation"])
    },
    "supervisor": {"authors": Annotated[list[Person], Field(min_length=1)]},
    "supervisor-thesis": {"authors": Annotated[list[Person], Field(min_length=1)]},
    "teaching-category": {
        "category": (
            Literal["lecture", "practical-lecture", "seminar", "project", "other"]
        )
    },
    "teaching-course": {
        "title": str,
        "module": str,
        "module_id": str,
    },
    "title": {"title": str},
    "subtitle": {"subtitle": str},
    "university": {"publisher": str},
    "version": {"version": str},
    "venue": {"venue": str},
    "volume": {"volume": str},
    "political_consultation": {
        "political_consultation": (
            Literal["Gutachten", "Positionspapier", "Studie", "Sonstiges", ""]
        )
    },
    "organization": {"organization": str},
    "organizations": {"organizations": list[str]},
}

# NO modules fields: history, units,
# Rendering:
# metrics
# quartile
# affiliated
# affiliated_positions
# cooperative
# rendered

# NOTE:
# Find out if changing default enum values is written to mongo and where
# Find out if fields list has same naming convention as module list (AdminTypes in MongoDB)


def mapping_admin_types(field: dict):
    f = field["format"]
    match f:
        case "string" | "text":
            return str
        case "int":
            return int
        case "float":
            return float
        case "bool" | "bool-check":
            return bool
        case "date":
            return date
        case "url":
            return AnyUrl
        case "str-list":
            return list[str]
        case "list":
            values = Literal[[x[0] for x in field["values"]]]
            if field.get("multiple", False):
                return list[values]
            if field.get("others", False):
                return values | str
            return values


def parse_admin_field(admin_fields: Cursor) -> dict[str, dict]:
    # Get ids from admin_fields
    transformed_admin_fields = {}
    for field in admin_fields:
        transformed_admin_fields[field["id"]] = {
            field["id"]: mapping_admin_types(field)
        }
    return transformed_admin_fields


def build_validator(
    key: str, type_fields: list[dict], admin_fields_dict: dict[str, dict[str, type]]
) -> BaseModel:
    data_structure: dict[str, Any] = {}

    # Mandatory for OSIRIS functioning:
    date = {"type": "field", "id": "date", "props": {"required": True}}
    if not date in type_fields:
        type_fields.append(date)

    type_field_names = {
        str(tf["id"]): tf
        for tf in type_fields
        if tf["type"] == "field" or tf["type"] == "custom"
    }

    # Main loop on modules
    for mod, type_info in type_field_names.items():
        found_type = {}

        if mod in admin_fields_dict.keys():
            # first check admin field for new altered definitions and custom fields that override default modules
            found_type = admin_fields_dict[mod]
        elif mod in MODULES:
            # find field in default module list
            found_type = MODULES[mod]
        else:
            raise KeyError(
                f"OSIRIS configuration fail: Could not find module or field named '{mod}'"
            )  # critical failure

        props = type_info.get("props", {})
        if not props:
            props = {}
        for field_name, field_info in found_type.items():
            if props.get("required", False):
                data_structure[field_name] = field_info
            else:
                data_structure[field_name] = field_info | None

    print("DATASTRUCTURE:")
    print(data_structure)
    return create_model(key, **data_structure)


def set_dynamic_literals(osiris: Database):

    osiris_countries = Literal[[x["iso"] for x in osiris["countries"].find()]]
    MODULES.update({"countries": {"countries": list[osiris_countries]}})
    MODULES.update({"country": {"country": osiris_countries}})
    MODULES.update({"nationality": {"country": osiris_countries}})

    osiris_tags = Literal[
        [x for x in [y["value"] for y in osiris["adminGeneral"].find({"key": "tags"})]]
    ]
    MODULES.update({"tags": {"tags": list[osiris_tags]},})

    osiris_projects = Literal[[str(x["_id"]) for x in osiris["projects"].find()]]
    MODULES.update({"projects": {"projects": list[osiris_projects]}})


def getValidators(osiris: Database) -> dict:
    """
    Input:
        osiris: Connection to OSIRIS database

    Output:
        dict where keys are [type]-[subtype] of all defined activity types in OSIRIS and value are pydantic classes to validate the input data
    """
    admin_types = osiris["adminTypes"].find()
    admin_fields = osiris["adminFields"].find()

    set_dynamic_literals(osiris)

    admin_fields_dict = parse_admin_field(admin_fields)

    validators = {}
    for t in admin_types:
        key = f"{t['parent']}-{t['id']}"
        if t.get("fields"):
            validators[key] = build_validator(key, t["fields"], admin_fields_dict)
    return validators
