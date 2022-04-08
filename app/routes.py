# -*- coding: utf-8 -*- 
from flask import render_template
from app import app
import os
import sqlite3

@app.route('/')
@app.route('/index')
def index(): 
    return render_template("index.html")


@app.route('/register')
def register(): 
    return render_template("register.html")