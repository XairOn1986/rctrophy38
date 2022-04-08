# -*- coding: utf-8 -*- 
from app.helpers import apology, login_required
from flask import render_template, flash, redirect, request, session
from flask_session import Session
from tempfile import mkdtemp
from app import app
import os
from werkzeug.security import generate_password_hash, check_password_hash

#Add work with MySQL
from flask_mysqldb import MySQL
mysql = MySQL(app)

Session(app)
sess = Session()
sess.init_app(app)


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
            return apology("Input name, password, confirmation and email!")

        #Check passwords correct repeats
        if password != confirmation:
            return apology("Repeat password correct!")

        #Check unic names and email
        unic_name = db.execute("SELECT username FROM users where username=%s", (username,))
        if unic_name != 0:
            return apology("Username busy!")
        
        unic_name = db.execute("SELECT email FROM users where email=%s", (email,))
        if unic_name != 0:
            return apology("Email busy!")

        hash = generate_password_hash(password)
        #Add the user's entry into the database after all checks
        
        db.execute("INSERT INTO users(username, password_hash, email) VALUES(%s, %s, %s)",(username, hash, email))
        mysql.connection.commit()
        db.close()
        flash("Учетная запись зарегистрирована")
        return redirect("/") 

    return render_template("register.html")



@app.route('/login', methods=["GET", "POST"])
def login(): 
    """Log user in"""    
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        db = mysql.connection.cursor()
        db.execute("SELECT * FROM users WHERE username = %s", (request.form.get("username"),))
        rows = db.fetchall()
        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["password_hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        flash('Welcome!')
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")