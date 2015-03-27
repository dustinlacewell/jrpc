#!/usr/bin/env python

from setuptools import setup

requirements = []
with open('requirements.txt') as fobj:
    for requirement in fobj:
        requirements.append(requirement)

setup(
    name = "jrpc",
    version = "0.1.0",
    packages = ['jrpc'],
    scripts = ['bin/jrpc'],

    install_requires = requirements,

    # metadata for upload to PyPI
    author = "Dustin Lacewell",
    author_email = "dlacewell@gmail.com",
    description = "JSON RPC for Autobahn/Twisted",
    keywords = "twisted autobahn rpc json",
    url = "http://github.com/dustinlacewell/jrpc",
)

