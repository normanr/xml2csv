#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


import urllib
from StringIO import StringIO
from xml.etree.ElementTree import ElementTree
from google.appengine.api import urlfetch
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp import util


def renderTree(xml, path, indent):
  if indent > 8: return ''
  r = []
  for e in xml.getchildren():
    r.append('&nbsp;' * indent * 4 + '<a href="%s">%s</a> = %s<br/>\n' % ((path + urllib.quote_plus(e.tag)), e.tag, e.text))
    r.append(renderTree(e, path + e.tag + '/', indent + 1))
  return ''.join(r)

class MainHandler(webapp.RequestHandler):

  def get(self):
    url = self.request.get('url')
    browse = self.request.get('browse')
    xpaths = self.request.get_all('xpath')
    if not url:
      self.response.out.write(template.render('index.html', {'url':'http://'}))
      return
    data = urlfetch.fetch(url).content
    xml = ElementTree()
    xml.parse(StringIO(data))
    texts = []
    for xpath in xpaths:
      subset = xml.findall(xpath)
      texts.extend((x.text for x in subset if x.text))
    output = ','.join(texts)
    if not browse:
      self.response.headers['Content-Type'] = 'text/csv'
      self.response.headers['Content-Disposition'] = 'filename=xml.csv'
      self.response.out.write(output)
      return
    link = 'url=%s%s' % (urllib.quote_plus(url), ''.join(['&amp;xpath=%s' % xpath for xpath in xpaths]))
    path = '?browse=1&amp;%s&amp;xpath=' % link
    self.response.out.write(template.render(
        'index.html', {
            'url':url,
            'output':output,
            'link':link,
            'browse':renderTree(xml.getroot(), path, 0)}))


def main():
  application = webapp.WSGIApplication([('/', MainHandler)],
                                       debug=True)
  util.run_wsgi_app(application)


if __name__ == '__main__':
  main()
