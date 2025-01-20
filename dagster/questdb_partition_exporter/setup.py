from setuptools import find_packages, setup

setup(
    name="questdb_partition_exporter",
    packages=find_packages(exclude=["questdb_partition_exporter_tests"]),
    install_requires=[
        "dagster",
        "dagster-cloud"
    ],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
