import os
import logging

import time

import webapp2
import jinja2

from google.appengine.ext import db

import user

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

class WikiHandler(webapp2.RequestHandler):
   
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)

	def render_str(self, template, **params):
		t = jinja_env.get_template(template)
		return t.render(params)

	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))

class Page(db.Model):
	name = db.StringProperty(required = True)
	content = db.TextProperty()
	created = db.DateTimeProperty( auto_now_add = True )

class WikiPage(WikiHandler):

	def get(self,pName):
		#logging.error("pName is %s" % pName)
		#page = db.GqlQuery('SELECT * FROM Page WHERE name = :1', pName)
		page = Page.all().filter('name =', pName).order('-created').get()  #This query returns only one result or None
		#logging.error("page is %s" % page)
		if page:
			self.render('main.html',page=page)
		else:
			self.redirect('/_edit%s' % pName)

class EditPage(WikiHandler):

	def get(self,pName):
		page = Page.all().filter('name =', pName).order('-created').get()
		if page:
			self.render('edit.html',pName=pName,content=page.content)
		else:
			self.render('edit.html',pName=pName)

	def post(self,pName):
		content = self.request.get('content')
		if content:
			p = Page(name=pName,content=content)
			p.put()
			time.sleep(1)
			#logging.error("pName is %s" % pName)
			self.redirect('%s' % pName)
		else:
			self.redirect('/_edit%s' % pName)

class HistoryPage(WikiHandler):

	def get(self,pName):
		history = Page.all().filter('name =', pName).order('-created').run()
		self.render('history.html',history=history,pName=pName)

PAGE_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)'

application = webapp2.WSGIApplication([
				('/login', user.LoginPage),('/logout', user.LogoutPage),('/signup', user.SignUp),
				('/_edit' + PAGE_RE, EditPage),('/_history' + PAGE_RE, HistoryPage),(PAGE_RE, WikiPage)
			],debug=True)