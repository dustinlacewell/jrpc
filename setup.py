#!/usr/bin/env python

from setuptools import setup

setup(name="jrpc",
      version="0.1.2",
      packages=['jrpc'],
      scripts=['bin/jrpc'],
      install_requires=[
          "Twisted",
          "autobahn",
      ],

      # metadata for upload to PyPI
      author="Dustin Lacewell",
      author_email="dlacewell@gmail.com",
      description="JSON RPC for Autobahn/Twisted",
      keywords="twisted autobahn rpc json",
      url="http://github.com/dustinlacewell/jrpc", )
