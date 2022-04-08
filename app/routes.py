# -*- coding: utf-8 -*- 
from app.helpers import apology
from flask import render_template, flash, redirect, request
from app import app
import os
from werkzeug.security import generate_password_hash, check_password_hash

#Add work with MySQL
from flask_mysqldb import MySQL
mysql = MySQL(app)

#db.execute("SELECT username FROM users where username=%s", (username,))
#message = db.fetchall()


@app.route('/')
@app.route('/index')
def index(): 
    return render_template("index.html")


@app.route('/register', methods=["GET", "POST"])
def register(): 
    """Register user"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        email = request.form.get("email")
        db = mysql.connection.cursor()
        #Check username and password not empty
        if (len(username) == 0) or (len(password) == 0) or (len(email) == 0):
            return apology("Input username, password, confirmation and EMAIL!")

        #Check passwords correct repeats
        if password != confirmation:
            return apology("Password confirmation missmatch!")

        #Check unic names and email
        unic_name = db.execute("SELECT username FROM users where username=%s", (username,))
        if unic_name != 0:
            return apology("This name already in use!")
        
        unic_name = db.execute("SELECT email FROM users where email=%s", (email,))
        if unic_name != 0:
            return apology("This email already in use!")

        hash = generate_password_hash(password)
        #Add the user's entry into the database after all checks
        
        db.execute("INSERT INTO users(username, password_hash, email) VALUES(%s, %s, %s)",(username, hash, email))
        mysql.connection.commit()
        db.close()
        flash("Учетная запись зарегистрирована")
        return redirect("/") 

    return render_template("register.html")