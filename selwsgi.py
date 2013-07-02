import os
import time
import socket
import logging
from multiprocessing import Process
from wsgiref import simple_server
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from webtest import app as testapp
from httplib import HTTPConnection, CannotSendRequest
from webtest.sel import (_free_port, WSGIApplication, WSGIServer,
                         WSGIRequestHandler)


class WebDriverApp(testapp.TestApp):
    apps = []

    def __init__(self, app=None, url=None, timeout=30000,
                 extra_environ=None, relative_to=None, **kwargs):
        self.app = None
        if app:
            super(WebDriverApp, self).__init__(app,
                                               relative_to=relative_to)
            self._run_server(self.app)
            url = self.app.url

        self._driver = webdriver.Firefox()
        self._driver.get(url)
        self.extra_environ = extra_environ or {}
        self.timeout = timeout
        self.test_app = self
        self.log = logging.getLogger(self.__class__.__name__)

    @property
    def driver(self):
        """
        The current :class:`selenium.webdriver.remote.webdriver.WebDriver`
        """
        return self._driver

    @property
    def url(self):
        return self.app.url

    def _run_server(self, app):
        """Run a wsgi server in a separate thread"""
        ip, port = _free_port()
        self.app = app = WSGIApplication(app, (ip, port))

        def run():
            logger = logging.getLogger("SeleniumWebDriverApp")

            def log_message(self, format, *args):
                logger.info("%s - - [%s] %s\n" %
                            (self.address_string(),
                             self.log_date_time_string(),
                             format % args))

            # monkey patch to redirect request handler logs
            WSGIRequestHandler.log_message = log_message

            httpd = simple_server.make_server(ip, port, app,
                                              server_class=WSGIServer,
                                              handler_class=WSGIRequestHandler)

            httpd.serve_forever()

        app.thread = Process(target=run)
        app.thread.start()
        conn = HTTPConnection(ip, port)
        time.sleep(.5)
        for i in range(100):
            try:
                conn.request('GET', '/__application__')
                conn.getresponse()
            except (socket.error, CannotSendRequest):
                time.sleep(.3)
            else:
                break

    def close(self):
        """
        Close selenium and the WSGI server if needed
        """
        self.driver.close()
        if self.app:
            conn = HTTPConnection(*self.app.bind)
            for i in range(100):
                try:
                    conn.request('GET', '/__kill_application__')
                    conn.getresponse()
                except socket.error:
                    conn.close()
                    # let's be nice with the forked process
                    self.app.thread.terminate()
                    self.app.thread.join(5)  # timeout of 5 seconds
                    break
                else:
                    time.sleep(.3)

    def is_element_present(self, how, what):
        try:
            self.browser.find_element(by=how, value=what)
        except NoSuchElementException:
            return False
        return True

    def wait_element_by(self, xpath=None, id=None, name=None, link_text=None,
                        css=None, timeout=20):
        driver = self.browser
        if xpath:
            method = driver.find_element_by_xpath
            arg = xpath
        elif id:
            method = driver.find_element_by_id
            arg = id
        elif name:
            method = driver.find_element_by_name
            arg = name
        elif link_text:
            method = driver.find_element_by_link_text
            arg = link_text
        elif css:
            method = driver.find_element_by_css_selector
            arg = css
        else:
            raise ValueError("please provide a type (xpath, id or name)")

        try:
            fn = lambda driver: method(arg)
            WebDriverWait(driver, timeout, 1.0).until(fn)
        except TimeoutException, ex:
            self.log.error("%s" % ex)
            self.take_screenshot("/tmp")
            assert False, "timeout, element '%s' wasn't found" % arg

    def wait_until_dissapears(self, xpath, timeout=20, poll=0.5):
        start = time.time()
        while (time.time() - start) <= timeout:
            try:
                self.browser.find_element_by_xpath(xpath)
            except Exception:
                return
            time.sleep(poll)
        raise AttributeError("Element %s never dissappeared" % xpath)

    def take_screenshot(self, directory, name=None):
        path = None
        try:
            path = os.path.join(directory, "shot_%s.png" %
                                (name or self.__class__.__name__))
            self.browser.save_screenshot(path)
            self.log.debug("Shot saved: %s" % path)
        except Exception, ex:
            self.log.warn("I couldn't take the screenshot on tearDown %s" % ex)
            path = None
        return path

    def fill_form(self, form_name, values):
        form = self.app.browser.find_element_by_id(form_name)
        assert form is not None, "form %s not found" % form_name
        time.sleep(1)
        for key, value in values.items():
            XPATH = 'id("%s")//input[@name="%s"]' % (form_name, key)
            item = self.browser.find_element_by_xpath(XPATH)
            item.clear()
            item.send_keys(value)
            item = self.browser.find_element_by_xpath(XPATH)
            assert item.get_attribute("value") == value

        return self.app.browser.find_element_by_id(form_name)
