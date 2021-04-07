from app import db
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import ForeignKey, Table
from sqlalchemy.orm import relationship
from flask_login import UserMixin

Base = declarative_base()

association_table = Table('association', db.metadata,
                          db.Column('users_id', db.Integer, ForeignKey('users.id')),
                          db.Column('desks_id', db.Integer, ForeignKey('desks.id'))
                          )


class User(UserMixin, db.Model, Base):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False, unique=True)
    name = db.Column(db.String, nullable=False, unique=True)
    desks = relationship('Desk',
                         secondary=association_table,
                         back_populates='users')
    comments = relationship('Comment', back_populates='parent_user')


class Desk(db.Model, Base):
    __tablename__ = "desks"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    mode = db.Column(db.String, nullable=False)
    users = relationship('User',
                         secondary=association_table,
                         back_populates='desks')
    cards = relationship('TaskCard', back_populates='parent_desk')


class TaskCard(db.Model, Base):
    __tablename__ = "cards"
    id = db.Column(db.Integer, primary_key=True)
    header = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=True)
    deadline = db.Column(db.DateTime)
    has_done = db.Column(db.Boolean, nullable=False)
    parent_desk = relationship('Desk', back_populates='cards')
    parent_desk_id = db.Column(db.Integer, ForeignKey('desks.id'))
    comments = relationship('Comment', back_populates='parent_card')


class Comment(db.Model, Base):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String, nullable=False)
    parent_card = relationship('TaskCard', back_populates='comments')
    parent_card_id = db.Column(db.Integer, ForeignKey('cards.id'))
    parent_user = relationship('User', back_populates='comments')
    parent_user_id = db.Column(db.Integer, ForeignKey('users.id'))



db.create_all()