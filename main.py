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


import cgi
import urllib
from StringIO import StringIO
import webapp2
from xml.etree.ElementTree import ElementTree

from django.template.loader import render_to_string
from google.appengine.api import urlfetch


def renderGroup(xpaths, xml):
  texts = []
  for xpath in xpaths:
    subset = xml.findall(xpath)
    subset = [x.text for x in subset if x.text]
    text = ','.join(subset)
    if len(subset) > 1:
      texts.append('"%s"' % text)
    else:
      texts.append(text)
  return ','.join(texts)

def renderHeader(groups, xpaths):
  if not groups:
    return ','.join([x[x.rfind('/')+1:] for x in xpaths])
  headers = []
  for group in groups:
    headers.extend((x[x.rfind('/')+1:] for x in xpaths if x.startswith(group + '/')))
  return ','.join(headers)

def matrixJoin(list):
  o = [[]]
  while len(list) > 0:
    new = []
    for x in o:
      for y in list[0]:
        new.append(x + [y])
    o = new
    list = list[1:]
  return o

def renderOutput(groups, xpaths, xml):
  if not groups:
    return renderGroup(xpaths, xml)
  lines = []
  for group in groups:
    items = xml.findall(group)
    texts = []
    for item in items:
      subpaths = [p[len(group)+1:] for p in xpaths if p.startswith(group + '/')]
      texts.append(renderGroup(subpaths, item))
    lines.append(texts)
  return '\n'.join([','.join(x) for x in matrixJoin(lines)])

def renderTree(nodes, path, indent):
  if indent > 8: return ''
  r = []
  for e in nodes:
    children = e.getchildren()
    filter = 'group' if children else 'xpath'
    link = path % filter + urllib.quote_plus(e.tag)
    r.append('&nbsp;' * indent * 4 + '<a href="%s">%s</a> = %s<br>\n' % (
        cgi.escape(link, True), cgi.escape(e.tag, True), cgi.escape(unicode(e.text))))
    r.append(renderTree(children, path + urllib.quote_plus(e.tag + '/').replace('%', '%%'), indent + 1))
  return ''.join(r)

class MainHandler(webapp2.RequestHandler):

  def get(self):
    url = self.request.get('url')
    browse = self.request.get('browse')
    header = self.request.get('header')
    groups = self.request.get_all('group')
    xpaths = self.request.get_all('xpath')
    if not url:
      self.response.out.write(render_to_string('index.html', None))
      return
    if url.startswith('http%3A%2F%2F') or url.startswith('https%3A%2F%2F'):
      url = urllib.unquote(url)
    if url.startswith('='):
      url = url[1:]
    if '://' not in url:
      url = 'http://' + url
    data = urlfetch.fetch(url).content
    data = data.replace('&nbsp;', u'\xa0'.encode('utf-8'))
    data = data.replace('&copy;', u'\xa9'.encode('utf-8'))
    xml = ElementTree()
    xml.parse(StringIO(data))
    headeroutput = renderHeader(groups, xpaths)
    output = renderOutput(groups, xpaths, xml)
    if not browse:
      self.response.headers['Content-Type'] = 'text/csv'
      self.response.headers['Content-Disposition'] = 'filename=xml.csv'
      if header:
        self.response.out.write(headeroutput + '\n')
      self.response.out.write(output + '\n')
      return
    link = 'url=%s%s%s' % (
        urllib.quote_plus(url),
        ''.join(['&group=%s' % urllib.quote_plus(group) for group in groups]),
        ''.join(['&xpath=%s' % urllib.quote_plus(xpath) for xpath in xpaths]))
    path = '?browse=1&' + link.replace('%', '%%') + '&%s='
    self.response.out.write(render_to_string(
        'index.html', {
            'url':url,
            'header':headeroutput,
            'output':output,
            'link':link,
            'browse':renderTree(xml.getroot().getchildren(), path, 0)}))


application = webapp2.WSGIApplication([('/.*', MainHandler)],
                                     debug=True)
