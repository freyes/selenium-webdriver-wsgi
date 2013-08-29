Selenium WebDriver WSGI
=======================

A simple library to wrap wsgi apps in an evironment suitable to be unit tested with Selenium WebDriver.


Installation
------------

The easiest way to install the code is to use `pip`_.

Install the newest version from `PyPI`_.::

    pip install selwsgi

Install the latest development version::

    pip install git+https://github.com/freyes/selenium-webdriver-wsgi.git#egg=selwsgi

The other option is to download and uncompress the code manually and execute the
included `setup.py` script for installation::

    ./setup.py install


Example Usage
-------------

Example of a simple unittest::

    from selwsgi import WebDriverApp
    from nose.tools import assert_true
    from myapp import application
    
    class BaseTestSelenium(object):
        def setUp(self):
            self.app = WebDriverApp(application())
    
        def tearDown(self):
            self.app.close()

        def test_index(self):
            res = self.app.get("/")
            assert_true(res.headers["Location"].endswith("/account/login?next=%2F"),
                        "Location ({}) doesn't end with /account/login?next=%2F".format(res.headers["Location"]))


Dependencies
------------

* `WebTest`_
* `WebOb`_

.. _PyPI: http://pypi.python.org/pypi/rabbitmq-munin
.. _pip: http://www.pip-installer.org/
.. _WebTest: https://pypi.python.org/pypi/WebTest
.. _WebOb: https://pypi.python.org/pypi/WebOb
