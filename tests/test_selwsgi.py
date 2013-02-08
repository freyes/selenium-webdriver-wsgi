from __future__ import absolute_import
from nose.tools import assert_equal
from selwsgi import WebDriverApp


def hello_world(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/html')])
    return ["<h1>Hello World!</h1>"]


class TestWebDriverApp(object):
    def setUp(self):
        self.app = WebDriverApp(hello_world)

    def tearDown(self):
        self.app.close()

    def test_hello_world(self):
        self.app.driver.get(self.app.url)
        title = self.app.driver.find_element_by_xpath("//h1")
        assert_equal("Hello World!", title.text)
