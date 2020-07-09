import codecs
import sys
import codecs
from os.path import join, dirname, abspath
from setuptools import setup, find_packages


project_root = dirname(abspath(__file__))
version = {}


with open(join(project_root, "protoc_base_plugin/version.py")) as read_file:
    exec(read_file.read(), version)

with open(join(project_root, "requirements.txt")) as read_file:
    REQUIRED = read_file.read().splitlines()

with codecs.open(join(project_root, "README.md"), "r", "utf-8") as f:
    long_description = "".join(f.readlines())


setup(
    name="protoc-base-plugin",
    version=version["__version__"],
    description="A framework for easier creation of protoc plugins",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Alexander Neumann",
    author_email="aleneum@gmail.com",
    url="https://gitlab.ub.uni-bielefeld.de/avikom/protoc-base-plugin.git",
    packages=find_packages(exclude=["tests", "test_*"]),
    install_requires=REQUIRED,
    license="MIT",
    entry_points={
        "console_scripts": [
            "protoc-gen-null = protoc_base_plugin.generators.null_parser:main"
        ],
    },
)
