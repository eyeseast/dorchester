from setuptools import setup
import os

VERSION = "0.2"


requirements = ["click", "click-default-group", "fiona", "geojson", "numpy", "shapely"]


def get_long_description():
    with open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md"),
        encoding="utf8",
    ) as fp:
        return fp.read()


setup(
    name="dorchester",
    description="A toolkit for making dot-density maps in Python",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="Chris Amico",
    url="https://github.com/eyeseast/dorchester",
    project_urls={
        "Issues": "https://github.com/eyeseast/dorchester/issues",
        "CI": "https://github.com/eyeseast/dorchester/actions",
        "Changelog": "https://github.com/eyeseast/dorchester/releases",
    },
    license="Apache License, Version 2.0",
    version=VERSION,
    packages=["dorchester"],
    entry_points="""
        [console_scripts]
        dorchester=dorchester.cli:cli
    """,
    install_requires=requirements,
    extras_require={"test": ["pytest"]},
    tests_require=["dorchester[test]"],
    python_requires=">=3.6",
)
