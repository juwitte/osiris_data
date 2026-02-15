from enum import Enum
from typing import Annotated, Literal
from bson.objectid import ObjectId

from pydantic import BaseModel, Field, ValidationError, create_model, UrlConstraints

from pydantic_extra_types.isbn import ISBN

from pymongo.database import Database



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

COUNTRY = Literal[""]
TAGS = Literal[""]
PROJECTS = Literal[""]

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
    "funding_type": {"funding_type": (str | None)},
    "guest-category": {"category": (str | None)},
    "gender": {"gender": (Literal["d", "f", "m", "-"] | None)},
    "nationality": {
        "country": (COUNTRY | None)
    },
    "country": {
        "country": (COUNTRY | None)
    },
    "countries": {
        "countries": (list[COUNTRY] | None)
    },
    "abstract": {"abstract": (str | None)},
    "isbn": {"isbn": (ISBN | None)},  # TODO: check isbn structure
    "issn": {"issn": Annotated[str, Field(pattern=r"^\d{4}-\d{4}$")]},
    "issue": {"issue": (str | None)},
    "iteration": {"iteration": (Literal["once", "annual"] | None)},
    "journal": {"journal": (str | None), "journal_id": (ObjectId | None)},
    "lecture-invited": {"lecture_invited": (bool | None)},
    "lecture-type": {"lecture_type": (Literal["short", "long", "repetition"] | None)},
    "license": {"license": (str | None)},
    "link": {"link": (UrlConstraints | None)},
    "location": {"location": (str | None)},
    "magazine": {"magazine": (str | None)},
    "online-ahead-of-print": {"epub": (bool | None)},
    "openaccess": {"open_access": (bool | None)},
    "openaccess-status": {
        "oa_status": (
            Literal["closed", "open", "diamond", "gold", "green", "hybrid", "bronze"]
            | None
        )
    },
    "pages": {"pages": (str | None)},
    "peer-reviewed": {"peer-reviewed": (bool | None)},
    "person": {
        "name": (str | None),  # TODO: improve person name with pattern check
        "affiliation": (str | None),
        "academic_title": (str | None),
    },
    "person-only": {
        "name": (str | None)
    },  # TODO: improve person name with pattern check
    "person-organization": {"name": (str | None), "organization": (str | None)},
    "projects": {"projects": (list[PROJECTS] | None)},  # TODO: get projects from DB
    "pub-language": {
        "pub_language": (Literal["de", "en", "fr", "es", "it", "other"] | None)
    },
    "publisher": {"publisher": (str | None)},
    "pubmed": {"pubmed": (int | None)},
    "pubtype": {"pubtype": (str | None)},
    "review-type": {"review-type": (str | None)},
    "role": {"role": (str | None)},
    "scientist": {"authors": Annotated[list[Person], Field(min_length=1)]},
    "semester-select": {},
    "scope": {
        "scope": (Literal["local", "regional", "national", "international"] | None)
    },
    "software-link": {"link": (UrlConstraints | None)},
    "software-type": {
        "software_type": (
            Literal["software", "database", "dataset", "webtool", "report"] | None
        )
    },
    "software-venue": {"software_venue": (str | None)},
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
            | None
        )
    },
    "tags": {"tags": (list[TAGS] | None)},  # TODO: DB lookup
    "thesis": {
        "category": (
            Literal["bachelor", "master", "diploma", "doctor", "habilitation"] | None
        )
    },
    "supervisor": {"authors": Annotated[list[Person], Field(min_length=1)]},
    "supervisor-thesis": {"authors": Annotated[list[Person], Field(min_length=1)]},
    "teaching-category": {
        "category": (
            Literal["lecture", "practical-lecture", "seminar", "project", "other"]
            | None
        )
    },
    "teaching-course": {
        "title": (str | None),
        "module": (str | None),
        "module_id": (str | None),
    },
    "title": {"title": str},
    "subtitle": {"subtitle": (str | None)},
    "university": {"publisher": (str | None)},
    "version": {"version": (str | None)},
    "venue": {"venue": (str | None)},
    "volume": {"volume": (str | None)},
    "political_consultation": {
        "political_consultation": (Literal[
            "Gutachten", "Positionspapier", "Studie", "Sonstiges", ""
        ] | None)
    },
    "organization": {"organization": (str | None)},
    "organizations": {"organizations": list[str]},
}


# TODO:
# Change iteration from modules to fields (see AdminTypes in Mongo) to check which fields are defined as required
#
# NOTE:
# Find out if changing default enum values is written to mongo and where
# Find out if fields list has same naming convention as module list (AdminTypes in MongoDB)


def parse_admin_field(field: dict):
    pass


def build_validator(key: str, type_fields: list[dict], admin_fields: list[dict]):
    data_structure = {}

    # Get ids from admin_fields
    admin_fields_ids = [f["id"] for f in admin_fields]
    admin_fields_dict = {x: y for x,y in zip(admin_fields_ids, admin_fields)}

    # Mandatory for OSIRIS functioning:
    date = {
        "type": "field",
        "id": "date"
    }
    if not date in type_fields:
        type_fields.append(date)

    type_field_names = [tf["id"] for tf in type_fields if tf["type"] == "field"]

    # Main loop on modules
    for mod in type_field_names:
        mod = mod.strip("*")
        if (
            mod in admin_fields_dict.keys()
        ):  # first check admin field for new altered definitions and custom fields
            data_structure[mod] = parse_admin_field(admin_fields_dict[mod])
        elif mod in MODULES:  # find field in default list
            for field_name, field_info in MODULES[mod].items():
                data_structure[field_name] = field_info
        else:
            raise KeyError(
                f"OSIRIS configuration fail: Could not find module or field named '{mod}'"
            )  # critical failure
    
    print("DATASTRUCTURE:")
    print(data_structure)
    return create_model(key, **data_structure)


def getValidators(osiris: Database) -> dict:
    """
    Input:
        osiris: Connection to OSIRIS database

    Output:
        dict where keys are [type]-[subtype] of all defined activity types in OSIRIS and value are pydantic classes to validate the input data
    """
    debug = True
    admin_types = osiris["adminTypes"].find()
    admin_fields = osiris["adminFields"].find()

    COUNTRY = Literal[[x["iso"] for x in osiris["countries"].find()]]
    TAGS = Literal[[x for x in [y["value"] for y in osiris["adminGeneral"].find({"key": "tags"}) ]]]
    PROJECTS = Literal[[x["_id"] for x in osiris["projects"].find()]]


    if debug:
        print("Country:")
        print(COUNTRY)
        print("Tags:")
        print(TAGS)
        print("Projects:")
        print(PROJECTS)

    validators = {}
    for t in admin_types:
        key = f"{t['parent']}-{t['id']}"
        validators[key] = build_validator(key, t["fields"], admin_fields)
    return validators
