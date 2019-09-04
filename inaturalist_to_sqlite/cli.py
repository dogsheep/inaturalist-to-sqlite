import click
import os
import json
import sqlite_utils
from .utils import save_observation, fetch_all_observations, ensure_views


@click.command()
@click.argument(
    "db_path",
    type=click.Path(file_okay=True, dir_okay=False, allow_dash=False),
    required=True,
)
@click.argument("username", required=False)
@click.option(
    "--load", type=click.File(), help="Load observations from this JSON file on disk"
)
@click.option(
    "--save", type=click.File("w"), help="Save observations to this JSON file on disk"
)
@click.option("-s", "--silent", is_flag=True, help="Don't show progress bar")
def cli(db_path, username, load, save, silent):
    "Save iNaturalist observations to a SQLite database"
    if username and load:
        raise click.ClickException("Provide either username or --load")

    if not username and not load:
        username = click.prompt("Please provide your iNaturalist username")

    if username:
        observations = fetch_all_observations(username, count_first=True)
        observation_count = next(observations)
    else:
        observations = json.load(load)
        observation_count = len(observations)
    db = sqlite_utils.Database(db_path)
    saved = []
    if silent:
        for observation in observations:
            save_observation(observation, db)
            if save:
                saved.append(observation)
    else:
        with click.progressbar(
            length=observation_count,
            label="Importing {} observation{}".format(
                observation_count, "" if observation_count == 1 else "s"
            ),
        ) as bar:
            for observation in observations:
                save_observation(observation, db)
                bar.update(1)
                if save:
                    saved.append(observation)
    ensure_views(db)
    if save:
        json.dump(saved, save, indent=4)
