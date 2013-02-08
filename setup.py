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
      packages=find_packages(),
      classifiers=[
          "Classifier: Intended Audience :: Developers"
          "Classifier: License :: OSI Approved :: MIT License"
          "Classifier: Topic :: Internet :: WWW/HTTP :: WSGI"
          "Classifier: Topic :: Internet :: WWW/HTTP :: WSGI :: Server"
          "Classifier: Programming Language :: Python :: 2.5"
          "Classifier: Programming Language :: Python :: 2.6"
          "Classifier: Programming Language :: Python :: 2.7"
      ])
