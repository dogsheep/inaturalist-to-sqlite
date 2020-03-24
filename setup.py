from setuptools import setup
import os

VERSION = "0.1a"


def get_long_description():
    with open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md"),
        encoding="utf8",
    ) as fp:
        return fp.read()


setup(
    name="inaturalist-to-sqlite",
    description="Create a SQLite database containing your observation history from iNaturalist",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="Simon Willison",
    url="https://github.com/dogsheep/inaturalist-to-sqlite",
    license="Apache License, Version 2.0",
    version=VERSION,
    packages=["inaturalist_to_sqlite"],
    entry_points="""
        [console_scripts]
        inaturalist-to-sqlite=inaturalist_to_sqlite.cli:cli
    """,
    install_requires=["sqlite-utils~=2.0", "click", "requests"],
    extras_require={"test": ["pytest"]},
    tests_require=["inaturalist-to-sqlite[test]"],
)
