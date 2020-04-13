import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_
import datetime
import time

db = SQLAlchemy()

class Schedule(db.Model):
    __tablename__ = "schedule"
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String, nullable=False)
    time = db.Column(db.String, nullable=False)
    destination = db.Column(db.String, nullable=False)

class Student(db.Model):
    __tablename__ = "students"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    student_id = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)

    def add_student(username, email, student_id, password):
        s = Student(username=username, email=email, student_id=student_id, password=password)
        db.session.add(s)
        db.session.commit()

class Booking_Form(db.Model):
    __tablename__ = "booking_form"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String, nullable=False)
    route_id = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime(), nullable=False)

    def add_booking(student_id, route_id, date):
        b = Booking_Form(student_id=student_id, route_id=route_id, date=date)
        db.session.add(b)
        db.session.commit()
