from setuptools import setup, find_packages


setup(name="selwsgi",
      version="0.1dev",
      author="Felipe Reyes",
      author_email="freyes@tty.cl",
      description=("A simple library to wrap wsgi apps in an evironment",
                   "suitable to be unit tested with Selenium WebDriver"),
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
