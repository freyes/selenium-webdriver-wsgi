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
from webtest.http import get_free_port
import webob

log = logging.getLogger("selwsgi")


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
        ip, port = get_free_port()
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
            self.driver.find_element(by=how, value=what)
        except NoSuchElementException:
            return False
        return True

    def wait_element_by(self, xpath=None, id=None, name=None, link_text=None,
                        css=None, timeout=20):
        driver = self.driver
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
                self.driver.find_element_by_xpath(xpath)
            except Exception:
                return
            time.sleep(poll)
        raise AttributeError("Element %s never dissappeared" % xpath)

    def take_screenshot(self, directory, name=None):
        path = None
        try:
            path = os.path.join(directory, "shot_%s.png" %
                                (name or self.__class__.__name__))
            self.driver.save_screenshot(path)
            self.log.debug("Shot saved: %s" % path)
        except Exception, ex:
            self.log.warn("I couldn't take the screenshot on tearDown %s" % ex)
            path = None
        return path

    def fill_form(self, form_name, values):
        form = self.driver.find_element_by_id(form_name)
        assert form is not None, "form %s not found" % form_name
        time.sleep(1)
        for key, value in values.items():
            XPATH = 'id("%s")//input[@name="%s"]' % (form_name, key)
            item = self.driver.find_element_by_xpath(XPATH)
            item.clear()
            item.send_keys(value)
            item = self.driver.find_element_by_xpath(XPATH)
            assert item.get_attribute("value") == value

        return self.driver.find_element_by_id(form_name)


#######################################################################
# Code took from webtest 1.4.3 webtest.sel
# https://raw.github.com/Pylons/webtest/1.4.3/webtest/sel.py
# it was removed from webtest, that's why I'm putting it here

###############
# Servers
###############


class WSGIApplication(object):
    """A WSGI middleware to handle special calls used to run a test app"""

    def __init__(self, app, bind):
        self.app = app
        self.serve_forever = True
        self.bind = bind
        self.url = 'http://%s:%s/' % bind
        self.thread = None

    def __call__(self, environ, start_response):
        if '__kill_application__' in environ['PATH_INFO']:
            self.serve_forever = False
            resp = webob.Response()
            return resp(environ, start_response)
        elif '__file__' in environ['PATH_INFO']:
            req = webob.Request(environ)
            resp = webob.Response()
            resp.content_type = 'text/html; charset=UTF-8'
            filename = req.params.get('__file__')
            body = open(filename).read()
            body.replace('http://localhost/',
                         'http://%s/' % req.host)
            resp.body = body
            return resp(environ, start_response)
        elif '__application__' in environ['PATH_INFO']:
            resp = webob.Response()
            return resp(environ, start_response)
        return self.app(environ, start_response)

    def __repr__(self):
        return '<WSGIApplication %r at %s>' % (self.app, self.url)


class WSGIRequestHandler(simple_server.WSGIRequestHandler):
    """A WSGIRequestHandler who log to a logger"""

    def log_message(self, format, *args):
        log.debug("%s - - [%s] %s" %
                  (self.address_string(),
                  self.log_date_time_string(),
                  format % args))


class WSGIServer(simple_server.WSGIServer):
    """A WSGIServer"""

    def serve_forever(self):
        while self.application.serve_forever:
            self.handle_request()
