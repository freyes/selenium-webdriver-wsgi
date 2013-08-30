#!/usr/bin/env python
import os
from setuptools import setup, find_packages


# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(name="selwsgi",
      version="0.1",
      author="Felipe Reyes",
      author_email="freyes@tty.cl",
      description="A simple library to wrap wsgi apps in an evironment suitable to be unit tested with Selenium WebDriver",
      long_description=read('README.rst'),
      license="MIT",
      keywords="selenium wsgi webtest unittest",
      url="https://github.com/freyes/selenium-webdriver-wsgi",
      py_modules=["selwsgi", ],
      install_requires=["WebTest", "WebOb"],
      classifiers=[
          "Intended Audience :: Developers",
          "License :: OSI Approved :: MIT License",
          "Topic :: Internet :: WWW/HTTP :: WSGI",
          "Topic :: Internet :: WWW/HTTP :: WSGI :: Server",
          "Programming Language :: Python :: 2.5",
          "Programming Language :: Python :: 2.6",
          "Programming Language :: Python :: 2.7"
      ])
