#login.py
import os

import webapp2
import jinja2

from google.appengine.ext import db

from utils import *

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

class BaseHandler(webapp2.RequestHandler):
   
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)

	def render_str(self, template, **params):
		t = jinja_env.get_template(template)
		return t.render(params)

	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))

	def set_secure_cookie(self,name,val):
		cookie_val = str(make_secure_val(val))
		self.response.headers.add_header(
			'Set-Cookie',
			'%s=%s; Path=/' % (name, cookie_val))

	def read_secure_cookie(self, name):
		cookie_val = self.request.cookies.get(name)
		return cookie_val and check_secure_val(cookie_val)

	def logout(self):
		self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

	def initialize(self, *a, **kw):
		webapp2.RequestHandler.initialize(self, *a, **kw)
		uid = self.read_secure_cookie('user_id')
		self.user = uid and User.by_name(uid)

def users_key(group = 'default'):
	return db.Key.from_path('users', group)

class User(db.Model):
	name = db.StringProperty( required=True)
	pw_hash = db.StringProperty( required=True)
	email = db.StringProperty()

	@classmethod
	def by_id(cls, uid):
		return User.get_by_id(uid, parent = users_key())

	@classmethod
	def by_name(cls, name):
		u = User.all().filter('name =', name).get()
		#u = db.GqlQuery('Select * From User Where name = :name',name = name)
		return u

	@classmethod
	def register(cls, name, pw, email = None):
		pw_hash = make_pw_hash(name, pw)
		return User(parent = users_key(),
					name = name,
					pw_hash = pw_hash,
					email = email)

	@classmethod
	def login(cls, name, pw):
		u = cls.by_name(name)
		if u and valid_pw(name, pw, u.pw_hash):
			return u

class SignUp(BaseHandler):

	def write_form(self,**params):
		self.render("signup.html",**params)

	def get(self):
		self.write_form()

	def post(self):
		have_error = False
		username = self.request.get('username')
		password = self.request.get('password')
		verify = self.request.get('verify')
		email = self.request.get('email')

		params = dict(username = username,
		              email = email)

		if not valid_username(username):
		    params['username_error'] = "That's not a valid username."
		    have_error = True

		if not valid_password(password):
		    params['password_error'] = "That wasn't a valid password."
		    have_error = True
		elif password != verify:
		    params['verify_error'] = "Your passwords didn't match."
		    have_error = True

		if not valid_email(email):
		    params['email_error'] = "That's not a valid email."
		    have_error = True

		if have_error:
		    self.write_form(**params)
		else:
			u = User.by_name(username)
			if u:
				msg = 'That user already exists.'
				self.render('signup.html', username_error = msg)
			else:
				u = User.register(username, password, email)
				u.put()

				self.set_secure_cookie('user_id',username)
				self.redirect('/')

class WelcomePage(BaseHandler):

	def get(self):
		username = self.read_secure_cookie('user_id')
		if username:
			self.write("Welcome %s" % username)
		else:
			self.redirect('/signup')

class LoginPage(BaseHandler):

	def get(self):
		self.render('login.html')

	def post(self):
		username = self.request.get('username')
		password = self.request.get('password')
		u = User.login(username, password)
		if u :
			self.set_secure_cookie('user_id', username)
			self.redirect('/')
		else:
			self.render('login.html',username = username, login_error = "Invalid login")

class LogoutPage(BaseHandler):

	def get(self):
		self.logout()
		self.redirect("/signup")