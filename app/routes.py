# -*- coding: utf-8 -*- 
from app.helpers import apology, login_required, avatar
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
        db.close()
        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["password_hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        flash("Welcome " + rows[0]["username"] + "!")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()
    # Redirect user to login form
    return redirect("/")

@app.route("/profile")
@login_required
def profile():
    """Personal profile"""
    db = mysql.connection.cursor()    
    db.execute("SELECT * FROM users WHERE id = '%s'", (session["user_id"],))
    user = db.fetchall()
    db.close()       
    photo = avatar(user[0]["email"],128)
    return render_template("profile.html", photo=photo,user=user[0]["username"])

@app.route("/garage", methods=["GET", "POST"])
@login_required
def garage():
    #For action by buttons
    if request.method == "POST":
        if request.form.get("add_model") == "add_model":
            return redirect("add_model")
        if request.form.get("edit_model") == "edit_model":
            if not request.form.get("select_edit_model"):
                return apology("must select model", 403)
            else:                
                db = mysql.connection.cursor()    
                db.execute("SELECT * FROM models WHERE owner = %s and deleted = %s and name = %s",\
                (session["user_id"], 0, request.form.get("select_edit_model"),))
                model = db.fetchall()
                db.close()
                return render_template("edit_model.html", model=model)
        if request.form.get("delete_model") == "delete_model":
            if not request.form.get("select_delete_model"):
                return apology("must select model", 403)
            else:
                db = mysql.connection.cursor()
                db.execute("UPDATE models SET deleted = %s WHERE owner = %s and name = %s",\
                (1, session["user_id"], request.form.get("select_delete_model"),))
                mysql.connection.commit()               
                db.close()
                flash("Модель удалена!")
                return redirect("/garage")
    #Show models
    db = mysql.connection.cursor()    
    db.execute("SELECT * FROM models WHERE owner = %s and deleted = %s", (session["user_id"], 0))
    models = db.fetchall()
    db.close()
    return render_template("garage.html", models=models)

@app.route("/add_model", methods=["GET", "POST"])
@login_required
def add_model():
        if request.method == "POST":
            if not request.form.get("name"): return apology("Imput name!", 403)
            else: name = request.form.get("name")
            
            db = mysql.connection.cursor()
            unic_name = db.execute("SELECT name FROM models where name=%s", (name,))
            flash(unic_name)
            if unic_name != 0:
                return apology("Name busy!")

            if not request.form.get("model"): return apology("Imput model!", 403)
            else: model = request.form.get("model")
            
            if not request.form.get("vendor"): vendor = None
            else: vendor = request.form.get("vendor")

            owner = session["user_id"]

            if request.form.get("axles") == None: axles = None
            else: axles = request.form.get("axles")

            if not request.form.get("clearance"): clearance = None
            else: clearance = request.form.get("clearance")

            if request.form.get("servo_on") == None: servo_on = None
            else: servo_on = request.form.get("servo_on")

            if not request.form.get("weight"): weight = None
            else: weight = request.form.get("weight")

            if not request.form.get("balance"): balance = None
            else: balance = request.form.get("balance")

            if not request.form.get("combo"): combo = None
            else: combo = request.form.get("combo")
            
            if request.form.get("winch") == None: winch = None
            else: winch = request.form.get("winch")

            if not request.form.get("tires"): tires = None
            else: tires = request.form.get("tires")

            if not request.form.get("base"): base = None
            else: base = request.form.get("base")

            if request.form.get("body") == None: body = None
            else: body = request.form.get("body")
            
            deleted = 0

            
            db.execute("INSERT INTO models(owner, name, model, vendor, axles, clearance, servo_on,\
            weight, balance, combo, winch, tires, base, body, deleted)\
            VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",\
            (owner, name, model, vendor, axles, clearance, servo_on, weight, balance, combo,\
            winch, tires, base, body, deleted,))
            mysql.connection.commit()
            db.close()
            flash("Модель создана")
            return redirect("/garage")     
        return render_template("add_model.html")

@app.route("/edit_model", methods=["GET", "POST"])
@login_required
def edit_model():
    if request.method == "POST":
            if not request.form.get("name"): return apology("Input name!", 403)
            else: name = request.form.get("name")
            db = mysql.connection.cursor()            
            
            id = request.form.get("id")
            unic_name = db.execute("SELECT name FROM models where name=%s and id!=%s", (name, id))
            if unic_name != 0:
                return apology("Name busy!")        

            if not request.form.get("model"): return apology("Imput model!", 403)
            else: model = request.form.get("model")
            
            if not request.form.get("vendor"): vendor = None
            else: vendor = request.form.get("vendor")

            owner = session["user_id"]

            if request.form.get("axles") == None: axles = None
            else: axles = request.form.get("axles")

            if not request.form.get("clearance"): clearance = None
            else: clearance = request.form.get("clearance")

            if request.form.get("servo_on") == None: servo_on = None
            else: servo_on = request.form.get("servo_on")

            if not request.form.get("weight"): weight = None
            else: weight = request.form.get("weight")

            if not request.form.get("balance"): balance = None
            else: balance = request.form.get("balance")

            if not request.form.get("combo"): combo = None
            else: combo = request.form.get("combo")
            
            if request.form.get("winch") == None: winch = None
            else: winch = request.form.get("winch")

            if not request.form.get("tires"): tires = None
            else: tires = request.form.get("tires")

            if not request.form.get("base"): base = None
            else: base = request.form.get("base")

            if request.form.get("body") == None: body = None
            else: body = request.form.get("body")    

            db.execute("UPDATE models SET name=%s, model=%s, vendor=%s, axles=%s, clearance=%s,\
            servo_on=%s, weight=%s, balance=%s, combo=%s, winch=%s, tires=%s, base=%s, body=%s where id=%s",\
            (name, model, vendor, axles, clearance, servo_on, weight, balance, combo,\
            winch, tires, base, body, id,))
            mysql.connection.commit()
            db.close()
            flash("Модель Изменена")
            return redirect("/garage")
    flash("Nothing change")
    return redirect("/garage")

@app.route("/all_models")
@login_required
def all_models():    
    #Show models
    db = mysql.connection.cursor()    
    db.execute("SELECT * FROM models WHERE deleted = %s", (0,))
    models = db.fetchall()
  
    for model in models:          
        db.execute("SELECT username FROM users WHERE id = %s", (model["owner"],))        
        owner = db.fetchall()        
        model["owner_username"] = owner[0]["username"]

    db.close()
    return render_template("all_models.html", models=models)

@app.route("/ontrack")
@login_required
def ontrack():
    db = mysql.connection.cursor()
    db.execute("SELECT * FROM penalty WHERE DELETED = 0")
    penaltys = db.fetchall() 
    db.close()   
    return render_template("ontrack.html", session_id=session["user_id"], penaltys=penaltys)

@app.route("/championat", methods=["POST","GET"])
@login_required
def championat():
    if request.method == "POST":
        if request.form.get("edit_penalty") == "edit_penalty":
            return redirect("edit_penalty")
    return render_template("championat.html", session_id=session["user_id"])

@app.route("/edit_penalty", methods=["POST","GET"])
@login_required
def edit_penalty():
    db = mysql.connection.cursor()
    if request.method == "POST":
        #################ADD PENALTY########################                               
        if request.form.get("add_penalty") == "add_penalty":                
            unic_name = db.execute("SELECT * FROM penalty WHERE name = %s", (request.form.get("penalty_name"),))            
            if unic_name != 0:
                flash(unic_name) 
                return apology("Name busy", 403)
            name = request.form.get("penalty_name")
            price = request.form.get("penalty_price")
            if (len(name) or len(price)) == 0:
                return apology("Input name and price!", 403)

            db.execute("INSERT INTO penalty(name, price, deleted) VALUES(%s,%s,%s)",(name, price, 0,))
            mysql.connection.commit()          
            flash("Штраф добавлен!")
            return redirect("/edit_penalty")
        ##########################REMOVE PENALTY
        if request.form.get("remove_penalty") == "remove_penalty":
            name = request.form.get("remove_penalty_name")
            db.execute("UPDATE penalty SET deleted = %s WHERE name = %s",\
            (1, name,))
            mysql.connection.commit()          
            flash("Штраф удален!")
            return redirect("/edit_penalty")
    
    db.execute("SELECT * FROM penalty WHERE DELETED = 0")
    penaltys = db.fetchall() 
    db.close()   
    return render_template("edit_penalty.html", penaltys=penaltys, session_id=session["user_id"])