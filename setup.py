#!/usr/bin/env python

from distutils.core import setup

setup(name="minishift-python",
      version="0.1.3",
      description="Python interface for the minishift",
      author="Nick Johnson",
      author_email="nick@arachnidlabs.com",
      url="https://github.com/arachnidlabs/minishift-python/",
      packages=["minishift"],
      install_requires=["mcp2210", "python-daemon"])
