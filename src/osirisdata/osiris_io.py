from pymongo import MongoClient

from osirisdata.utils import osiris_utils


class OsirisIO:

    def __init__(self, connection: str, database: str):
        client = MongoClient(connection)
        self.osiris = client[database]

        self.fields = self.osiris["adminFields"].find()
        self.types = self.osiris["adminTypes"].find()

        self.validators = osiris_utils.getValidators(self.types, self.fields)


    def _check_activity(self, element: dict):
        activity_type = element.get("type")
        if not activity_type:
            raise KeyError("Activity needs 'type' key")
        activity_subtype = element.get("subtype")
        if not activity_subtype:
            raise KeyError("Activity needs 'subtype' key")
        osiris_type = self.osiris["adminTypes"].find_one({"id": activity_subtype})
        if not osiris_type:
            raise KeyError(f"Activity type {activity_type} not found in OSIRIS")
        # validate(element)


    def get_user_id(self, name_last: str, name_first: str = "", orcid: str=None):
        if orcid:
            user = self.osiris["persons"].find_one({"orcid": orcid})
            if user:
                return user["username"]
        user = self.osiris["persons"].find_one(
            {
                "$or": [
                    {"last": name_last, "first": {"$regex": f"^{name_first}.*"}},
                    {"names": f"{name_last}, {name_first}"},
                ]
            }
        )
        if user:
            return user["username"]
        return None

    def get_journal(self, issn: list[str] | str) -> dict:
        if isinstance(issn, list):
            return self.osiris["journals"].find_one({"issn": {"$in": issn}})
        else:
            return self.osiris["journals"].find_one({"issn": {"$in": [issn]}})

    def add_journal(self, new_journal: dict) -> int:
        new_doc = self.osiris["journals"].insert_one(new_journal)
        return new_doc.inserted_id

    def check_existence(self, doi: str, pubmed: str):
        if doi and self.osiris["activities"].count_documents({"doi": doi}) > 0:
            print(f"DOI {doi} exists in activities and was omitted.")
            return True
        if pubmed and self.osiris["activities"].count_documents({"pubmed": pubmed}) > 0:
            print(f"Pubmed {pubmed} exists in activities and was omitted.")
            return True
        if self.osiris["queue"].count_documents({"doi": doi}) > 0:
            print(f"DOI {doi} exists in queue and was omitted.")
            return True

    def get_activities(self, start_year: int = 0):
        return self.osiris["activities"].find(
            {
                "type": "publication",
                "year": {"$gte": int(start_year)},
            },
            {"title": 1},
        )

    def add_activity(self, element: dict):
        self._check_activity(element)
        self.osiris["activities"].insert_one(element)

    def get_activity_by_id(self, id, id_type="_id"):
        return self.osiris["activities"].find_one({id_type: id})

    def delete_activity(self, doi: str):
        # delete all entries with the same DOI
        self.osiris["activities"].delete_many({"doi": doi})

    def add_queue(self, element: dict):
        self.osiris["queue"].insert_one(element)

    def get_type(self, element: dict):
        return self.osiris["adminTypes"].find_one(element)

    def update_activity(self, element: dict):
        # TODO improve original object search
        original = self.get_activity_by_id(element.get("doi"), id_type="doi")
        if not original:
            return
        update = {}
        for key, value in element.items():
            if key not in original.keys():
                update[key] = value
            # TODO add more to update

        return self.osiris["activities"].update_one(
            {"_id": original.get("_id")}, {"$set": update}
        )

    def delete_collection(self, collection: str) -> None:
        """Delete a whole collection"""
        self.osiris[collection].delete_many({})
