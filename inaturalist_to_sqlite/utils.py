import datetime
import requests
from sqlite_utils.db import AlterError, ForeignKey


def save_observation(observation, db):
    observation = dict(observation)
    location = observation.pop("location", None) or ""
    if location:
        latitude, longitude = location.split(",")
    else:
        latitude, longitude = None, None
    observation["longitude"] = longitude
    observation["latitude"] = latitude
    del observation["observed_on_details"]
    del observation["created_at_details"]
    del observation["observed_on_string"]
    if observation.get("taxon"):
        observation["taxon"] = save_taxon(observation["taxon"], db)
    observation["user"] = (
        db["users"]
        .upsert(observation["user"], pk="id", column_order=("id", "login", "name"))
        .last_pk
    )
    photos = observation.pop("photos", None) or []
    identifications = observation.pop("identifications", None) or []
    observation_id = (
        db["observations"]
        .upsert(observation, pk="id", foreign_keys=("taxon", "user"))
        .last_pk
    )
    for photo in photos:
        photo_id = save_photo(photo, db)
        db["observations_photos"].upsert(
            {"observations_id": observation_id, "photos_id": photo_id},
            pk=("observations_id", "photos_id"),
            foreign_keys=("observations_id", "photos_id"),
        )
    for identification in identifications:
        save_identification(identification, observation_id, db)


def save_identification(identification, observation_id, db):
    identification = dict(identification)
    identification["observation"] = observation_id
    identification["user"] = save_user(identification["user"], db)
    del identification["created_at_details"]
    identification["taxon"] = save_taxon(identification["taxon"], db)
    if "previous_observation_taxon" in identification:
        identification["previous_observation_taxon"] = save_taxon(
            identification["previous_observation_taxon"], db
        )
    identification.pop("previous_observation_taxon_id", None)
    del identification["taxon_id"]
    return (
        db["identifications"]
        .upsert(
            identification,
            pk="id",
            foreign_keys=(
                ("user", "users"),
                ("taxon", "taxons"),
                ("observation", "observations"),
                ("previous_observation_taxon", "taxons"),
            ),
            column_order=(
                "id",
                "user",
                "observation",
                "created_at",
                "taxon",
                "previous_observation_taxon",
            ),
        )
        .last_pk
    )


def save_user(user, db):
    return (
        db["users"].upsert(user, pk="id", column_order=("id", "login", "name")).last_pk
    )


def save_photo(photo, db):
    photo = dict(photo)
    dims = photo.pop("original_dimensions") or {}
    photo["height"] = dims.get("height")
    photo["width"] = dims.get("width")
    return (
        db["photos"]
        .upsert(
            photo,
            pk="id",
            alter=True,
            column_order=("preferred_common_name", "name", "rank"),
        )
        .last_pk
    )


def save_taxon(taxon, db):
    taxon = dict(taxon)
    if taxon.get("default_photo"):
        taxon["default_photo"] = save_photo(taxon["default_photo"], db)
    else:
        taxon["default_photo"] = None
    if taxon.get("conservation_status"):
        taxon["conservation_status"] = (
            db["conservation_status"]
            .upsert(taxon["conservation_status"], pk="status_name")
            .last_pk
        )
    ancestors = taxon.pop("ancestors", None)
    if ancestors:
        for ancestor in ancestors:
            save_taxon(ancestor, db)
    return (
        db["taxons"]
        .upsert(
            taxon,
            pk="id",
            alter=True,
            foreign_keys=(
                ("conservation_status", "conservation_status"),
                ("default_photo", "photos"),
            ),
            column_order=(
                "id",
                "name",
                "preferred_common_name",
                "rank",
                "default_photo",
                "conservation_status",
            ),
        )
        .last_pk
    )


def fetch_all_observations(username, count_first=False):
    # "If you need to retrieve large numbers of records, use the per_page and id_above or id_below parameters instead."
    # If count_first is True it first yields the total checkins count
    params = {"user_login": username, "order": "desc", "order_by": "id", "per_page": 30}
    id_below = None
    first = True
    while True:
        if id_below is not None:
            params["id_below"] = id_below
        url = "https://api.inaturalist.org/v1/observations"
        data = requests.get(url, params).json()
        if first:
            first = False
            if count_first:
                yield data["total_results"]
        if not data.get("results"):
            break
        for item in data["results"]:
            yield item
        id_below = min(r["id"] for r in data["results"])
