from setuptools import setup, find_packages
from os import path

this_directory = path.abspath(path.dirname(__file__))

with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

requires = [
    "aiohttp",
    "async-property",
    "cached-property",
    "chardet",
    "maya",
    "CaseInsensitiveDict"
]

setup(
    name="roblox.py",
    version="0.1",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="roblox robloxapi robloxpy",
    url="https://github.com/jpatrickdill/roblox.py",
    author="Patrick Dill",
    author_email="jamespatrickdill@gmail.com",
    license="MIT",
    packages=["roblox"],
    install_requires=requires,
    include_package_data=True
)
