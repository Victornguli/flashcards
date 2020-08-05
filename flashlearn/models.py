import logging
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from flask_bcrypt import Bcrypt
from werkzeug.http import http_date
from flashlearn import db

logger = logging.getLogger('flashlearn')


class TimestampedModel(db.Base):
	"""Base model class for all timestamped models"""
	__abstract__ = True

	id = Column(Integer, primary_key = True)
	date_created = Column(DateTime(timezone = True), server_default = func.now())
	date_updated = Column(DateTime(timezone = True), server_default = func.now(), onupdate = func.now())
	state = Column(String, default = 'Active')

	def save(self):
		"""Save a user to a database. This includes creating a new user and editing too"""
		db.session.add(self)
		db.session.commit()

	def update(self, **kwargs):
		for k, v in kwargs.items():
			setattr(self, k, v)
		db.session.commit()

	def delete(self):
		db.session.delete(self.query.filter_by(id = self.id).first())
		db.session.commit()

	@classmethod
	def all(cls):
		return cls.query.filter(cls.state == 'Active')

	@classmethod
	def get_by_id(cls, _id):
		return cls.query.filter(cls.id == _id).first()


class User(TimestampedModel):
	"""User model class"""
	__tablename__ = 'users'

	username = Column(String(50), nullable = False)
	password = Column(String(256), nullable = False)
	email = Column(String(256))

	def __init__(self, username, password = None, email = None):
		"""Initialize new user model"""
		self.username = username
		if password:
			self.password = Bcrypt().generate_password_hash(password).decode()
		self.email = email

	def password_is_valid(self, password):
		"""Checks a submitted password against its stored hash"""
		return Bcrypt().check_password_hash(self.password, password)

	def set_password(self, password):
		"""Set password"""
		self.password = Bcrypt().generate_password_hash(password).decode()

	@property
	def to_json(self):
		return dict(
			id = self.id, username = self.username, email = self.email,
			date_created = http_date(self.date_created), date_modified = http_date(self.date_updated),
			decks = [d.to_json for d in self.decks],
			study_plans = [p.to_json for p in self.study_plans],
			is_active = True if self.state == 'Active' else False)

	# @property
	# def decks(self):
	# 	return Deck.query.filter(Deck.user_id == self.id)
	#
	# @property
	# def plans(self):
	# 	return StudyPlan.query.filter(StudyPlan.user_id == self.id)

	def __repr__(self):
		return f'<User: {self.username} - {self.state}>'


class Deck(TimestampedModel):
	"""Deck model class"""
	__tablename__ = 'decks'

	name = Column(String(100), nullable = False, unique = True)
	description = Column(String)
	user_id = Column(Integer, ForeignKey('users.id'))
	parent_id = Column(Integer, ForeignKey('decks.id'))

	user = relationship('User', backref = 'decks')
	children = relationship('Deck')

	def __init__(self, name, description, user_id = None, user = None, parent_id = None):
		"""Initialize a Deck"""
		self.name = name
		self.description = description
		if user_id:
			self.user_id = user_id
		elif user:
			self.user = user
		self.parent_id = parent_id

	@property
	def to_json(self):
		return dict(
			id = self.id, name = self.name, description = self.description,
			user = self.user_id, parent = self.parent_id)

	def __repr__(self):
		return f'<Deck: {self.name}>'


class Card(TimestampedModel):
	"""Card model class"""
	__tablename__ = 'cards'

	name = Column(String(100), nullable = False, unique = True)
	description = Column(String)
	front = Column(Text(), nullable = False)
	back = Column(Text(), nullable = False)
	user_id = Column(Integer, ForeignKey('users.id'), nullable = False)
	deck_id = Column(Integer, ForeignKey('decks.id'), nullable = False)

	user = relationship('User', backref = 'cards')
	deck = relationship('Deck', backref = 'cards')

	def __init__(self, **kwargs):
		"""Initialize a card"""
		super(Card, self).__init__(**kwargs)

	def __repr__(self):
		return f'<Card: {self.name} - {self.user.username} - {self.group.name}>'

	@property
	def to_json(self):
		return dict(
			id = self.id, name = self.name, description = self.description,
			front = self.front, back = self.back, user = self.user.to_json)


class StudyPlan(TimestampedModel):
	"""Study plan model class"""
	__tablename__ = 'study_plans'

	name = Column(String(100), nullable = False, unique = True)
	description = Column(String)
	ordering = Column(String(10))
	see_solved = Column(Boolean(), default = False)
	user_id = Column(Integer, ForeignKey('users.id'))

	user = relationship('User', backref = 'study_plans')

	def __init__(self, name, ordering = False, user_id = None, user = None):
		"""Initialize a study plan"""
		self.name = name
		self.ordering = ordering
		if user_id:
			self.user_id = user_id
		elif user:
			self.user = user

	def __repr__(self):
		return f'<StudyPlan: {self.name} - {self.state}>'

	@property
	def to_json(self):
		d = {
			'id': self.id,
			'name': self.name,
			'description': self.description,
			'see_solved': self.see_solved,
			'user_id': self.user_id
		}
		return d

# if __name__ == '__main__':
# 	t = Card
# 	print(getattr(t, 'name', 0))
# 	print(t.__table__.columns)
