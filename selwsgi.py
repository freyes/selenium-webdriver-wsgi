import time
import socket
import logging
from multiprocessing import Process
from wsgiref import simple_server
from selenium import webdriver
from webtest import app as testapp
from webtest.compat import HTTPConnection
from webtest.compat import CannotSendRequest
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
