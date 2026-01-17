import html
from diophila.openalex import OpenAlex
from Levenshtein import ratio
from nameparser import HumanName
from datetime import datetime
from pprint import pprint

from requests.exceptions import HTTPError


from osirisdata.osiris_io import OsirisIO
from osirisdata.utils.openalex_utils import make_abstract_string, TYPES


def get_history(element={}):
    return {
        "type": "imported",
        "user": None,
        "date": datetime.now().date().isoformat(),
        # 'data': element
    }


class OpenAlexParser:
    def __init__(
        self,
        osiris: OsirisIO,
        institute_id: str,
        email: str,
        start_year: int = 1900,
        ignore_duplicates=False,
    ) -> None:

        self.osiris = osiris
        self.inst_id = institute_id
        self.mail = email
        self.start_year = start_year

        # set up OpenAlex
        self.openalex = OpenAlex(self.mail)

        self.possible_duplicates = []
        if not ignore_duplicates:
            osiris_activities = self.osiris.get_activities(self.start_year)
            self.possible_duplicates = [
                (i.get("_id"), i.get("title")) for i in osiris_activities
            ]

    def get_works(self, filters=None):
        # NOPE: use created_date and updated_date to filter
        # Not possible, needs payed version

        if not filters:
            filters = {
                "from_publication_date": str(self.start_year) + "-01-01",
                "institutions.id": self.inst_id,
                "has_doi": "true",
            }

        pages_of_works = self.openalex.get_list_of_works(filters=filters, pages=None)

        works_count = 0
        for page in pages_of_works:
            for work in page["results"]:
                try:
                    element = self.parse_work(work)
                    if element == False:
                        continue
                    works_count += 1
                    yield element
                except Exception as e:
                    print(f'Error with DOI {work["doi"]}')
                    print(e)
                    continue
        print(f"--- Finished. Imported {works_count} documents.")

    def get_work(self, id, id_type="doi", unparsed=False):
        try:
            work = self.openalex.get_single_work(id, id_type)
        except HTTPError:
            print(f"Identifier {id_type}: {id} was not found")
            return False
        if unparsed:
            return work
        return self.parse_work(work)

    def add_work(self, id, id_type="doi", ignore_duplicates=True, test=False):
        if test:
            # delete all entries with the same DOI
            self.osiris.delete_activity(id)
        element = self.get_work(id, id_type)
        if test:
            pprint(element)
        if element != False:
            if ignore_duplicates and element.get("duplicate"):
                print(
                    f'Activity might have a duplicate (DOI {element["doi"]}) and was omitted.'
                )
                return
            self.osiris.add_activity(element)
            print(f"{id_type.upper()} {id} has been added to the database.")

    def get_works_dois(self, filters=None):
        if not filters:
            filters = {
                "from_publication_date": self.start_year + "-01-01",
                "institutions.id": self.inst_id,
                "has_doi": "true",
            }
        pages_of_works = self.openalex.get_list_of_works(filters=filters, pages=None)
        for page in pages_of_works:
            for work in page["results"]:
                yield work["doi"]

    def queue_job(self, ignore_existing=True, ignore_types=[]):
        already_imported = []
        if ignore_existing:
            already_imported = [i.get("openalex") for i in self.osiris.get_activities()]

        for element in self.get_works():
            # print(element)
            if element.get("subtype") in ignore_types:
                continue

            if element.get("openalex") not in already_imported:
                self.osiris.add_queue(element)

    def import_job(self):
        for element in self.get_works():
            if element.get("duplicate"):
                print(
                    f'Activity might have a duplicate (DOI {element["doi"]}) and was omitted.'
                )
                continue
            element["imported"] = datetime.now().date().isoformat()
            element["history"] = [get_history(element)]
            self.osiris.add_activity(element)

    def update_job(self):

        for activity in self.osiris.get_activities():
            if doi := activity.get("doi"):
                element = self.get_work(doi, "doi")
            # elif openalex_id := activity.get('openalex'):
            #     element = self.get_work(openalex_id, 'openalex')
            else:
                # No identifier found, skip entry
                continue
            self.osiris.update_activity(element)

    def get_journal(self, issn) -> dict | None:
        """
        Return journal from DB if exists, else creates the journal
        """
        if not issn:
            return None

        if journal := self.osiris.get_journal(issn):
            return journal

        # if journal does not exist: create one
        try:
            source = self.openalex.get_single_venue(issn[-1], "issn")
        except HTTPError as e:
            print(f"Journal not found {issn} - {e}")
            return

        if not source or source["type"] != "journal":
            return None

        new_journal = {
            "journal": source["display_name"],
            # 'abbr': source['abbreviated_title'],
            "publisher": source["host_organization_name"],
            "issn": source["issn"],
            "oa": source["is_oa"],
            "openalex": source["id"].replace("https://openalex.org/", ""),
        }

        new_journal["_id"] = self.osiris.add_journal(new_journal)
        return new_journal

    def parse_work(self, work) -> dict | bool:
        if work["is_retracted"]:
            print(f'retracted {work["doi"]}')
            return False

        # print(work['doi'])
        if not work["doi"] or "https://doi.org/" not in work["doi"]:
            print(f"doi not found, openalex id: {work['id']}")
            return False

        pubmed = work["ids"].get("pmid")
        if pubmed:
            pubmed = pubmed.replace("https://pubmed.ncbi.nlm.nih.gov/", "")

        doi = work["doi"].replace("https://doi.org/", "")

        # check if element is in the database
        if self.osiris.check_existence(doi, pubmed):
            return False

        typ = TYPES.get(work["type"])
        if not typ:
            print(f'Activity type {work["type"]} is unknown (DOI: {doi}).')
            return False

        authors = []
        for author in work["authorships"]:
            # match via name and ORCID
            
            p_name = author["author"]["display_name"]
            if not p_name:
                p_name = author["raw_author_name"]

            name = HumanName(p_name)

            orcid = author["author"].get("orcid")
            if orcid:
                orcid = orcid.replace("https://orcid.org/", "")

            name_first = name.first
            name_last = name.last
            user = self.osiris.get_user_id(name_last, name_first, orcid)
            pos = author["author_position"]
            if pos == "middle" and author.get("is_corresponding"):
                pos = "corresponding"

            inst = [i.get("id") for i in author["institutions"]]
            authors.append(
                {
                    "last": name.last,
                    "first": name.first + (" " + name.middle if name.middle else ""),
                    "position": pos,
                    "aoi": ("https://openalex.org/" + self.inst_id in inst),
                    "orcid": orcid,
                    "user": user,
                    "approved": False,
                }
            )

        pages = None
        if work["biblio"]["first_page"]:
            pages = work["biblio"]["first_page"]
            if work["biblio"]["last_page"] and work["biblio"]["last_page"] != pages:
                pages += "-" + work["biblio"]["last_page"]

        # journal
        loc = work["primary_location"]["source"]
        # journal = loc['display_name']

        # date
        date = work["publication_date"].split("-")
        month = None
        day = None
        if len(date) >= 2:
            month = int(date[1])
        if len(date) >= 3:
            day = int(date[2])

        abstract = make_abstract_string(work.get("abstract_inverted_index"))
        work["title"] = html.unescape(work["title"])
        element = {
            "doi": doi,
            "type": "publication",
            "subtype": typ,
            "title": work["title"],
            "year": work["publication_year"],
            "abstract": abstract,
            "month": month,
            "day": day,
            "authors": authors,
            "pages": pages,
            "openalex": work["id"].replace("https://openalex.org/", ""),
            "pubmed": pubmed,
            "open_access": work["open_access"]["is_oa"],
            "oa_status": work["open_access"]["oa_status"],
            "correction": False,
            "epub": False,
        }
        if typ == "others":
            element["doc_type"] = work["type"].title()

        journal = None
        if loc and loc.get("type") == "journal":
            element["location"] = loc["display_name"]
            journal = self.get_journal(loc["issn"])
            if journal:
                element.update(
                    {
                        "volume": work["biblio"]["volume"],
                        "issue": work["biblio"]["issue"],
                        "journal": journal["journal"],
                        "issn": journal["issn"],
                        "journal_id": str(journal["_id"]),
                    }
                )
                if (not element["volume"]) and not element["issue"]:
                    element["epub"] = True

        if typ == "article":
            if not loc or not loc["issn"]:
                element["subtype"] = "magazine"
            elif loc.get("type") == "repository":
                element["subtype"] = "preprint"
            elif not journal:
                element["subtype"] = "magazine"

        if typ == "chapter" and loc and loc.get("display_name"):
            element.update(
                {
                    "book": loc["display_name"],
                    "issn": loc["issn"],
                }
            )
        if typ == "preprint":
            element["subtype"] = "preprint"

        if typ == "magazine" or typ == "preprint":
            element["magazine"] = loc.get("display_name") if loc else None

        for id, duplicate in self.possible_duplicates:
            dist = ratio(duplicate, element["title"])
            # print(dist, duplicate)
            if dist > 0.9:
                element["duplicate"] = id
                break
        return element


if __name__ == "__main__":
    parser = OpenAlexParser()
    # parser.queueJob()

    parser.add_work("10.1007/978-3-319-69075-9_13", test=True)
