# -*- coding: utf-8 -*- 
from app.helpers import apology, login_required, avatar
from flask import render_template, flash, redirect, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from app import app
import os
from werkzeug.security import generate_password_hash, check_password_hash
import operator


#Add work with MySQL
from flask_mysqldb import MySQL
mysql = MySQL(app)

Session(app)
sess = Session()
sess.init_app(app)


@app.route('/')
@app.route('/index')
def index():
    db = mysql.connection.cursor()
    db.execute("select id from championats where deleted=0 order by id limit 1")
    temp = db.fetchall()
    championat_id = temp[0]["id"]

    db.execute("select * from events where deleted=0 and status=1 and championat_id=%s", (championat_id,))
    events = db.fetchall()

    if request.args.get("select_etap") != None:
        db.execute("select * from events where deleted=0 and status=1 and id=%s", (request.args.get("select_etap"),))
    else:
        db.execute("select * from events where deleted=0 and status=1 order by date desc limit 1")
    temp = db.fetchall()



    etap_id = temp[0]["id"]
    etap_name = temp[0]["event_name"]
    etap_date = temp[0]["date"]
    etap_link = temp[0]["link"]
    db.execute("select * from results where event_id = %s and deleted = 0 order by place",(etap_id,))
    results = db.fetchall()
    for result in results:
        db.execute("select username from users where id = %s",(result["user_id"],))
        temp = db.fetchall()
        result["user_name"] = temp[0]["username"]
        db.execute("select * from models where id = %s",(result["model_id"],))
        temp = db.fetchall()
        result["model_name"] = temp[0]["name"]
        result["model_model"] = temp[0]["model"] 
    
    return render_template("index.html", results=results, etap_name=etap_name, 
        etap_date=etap_date, etap_link=etap_link, etap_id=etap_id, events=events)


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


@app.route("/edit_penalty", methods=["POST","GET"])
@login_required
def edit_penalty():
    db = mysql.connection.cursor()
    if request.method == "POST":
        #################ADD PENALTY########################                               
        if request.form.get("add_penalty") == "add_penalty":                
            unic_name = db.execute("SELECT * FROM penalty WHERE name = %s", (request.form.get("penalty_name"),))            
            if unic_name != 0:                 
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

@app.route("/admin", methods=["POST","GET"])
@login_required
def admin():
    db = mysql.connection.cursor()
    if request.method == "POST":
    ##############Add and Championat########################################    
        if request.form.get("create_championat") == "create_championat":
            if len(request.form.get("year_create_championat")) == 0:
                flash ("Введи год!")
                return redirect("/admin")
            year_champ = int(request.form.get("year_create_championat"))            
            unic_name_champ = db.execute("SELECT * FROM championats WHERE year = %s and deleted = 0", (year_champ,))            
            if unic_name_champ != 0:
                flash("Такой год уже есть!")            
                return redirect("/admin")
            else:
                db.execute("INSERT INTO championats(year, deleted) VALUES(%s,%s)",\
                (year_champ, 0,))
                mysql.connection.commit()       
                flash("Чемпионат добавлен!")
                return redirect("/admin")
    ############Delete championat##########################
        if request.form.get("delete_championat") == "delete_championat":
            if request.form.get("select_delete_championat") == None:
                flash ("Выбери год!")
                return redirect("/admin")
            year_champ = int(request.form.get("select_delete_championat"))
            db.execute("UPDATE championats SET deleted = %s WHERE year = %s",\
            (1, year_champ,))
            mysql.connection.commit()       
            flash("Чемпионат удален!")
            return redirect("/admin")
    
    ##################CREATE EVENT#############################################
        if request.form.get("create_event") == "create_event":
            if request.form.get("select_championat_create_event") == None:
                flash ("Выбери чемпионат!")
                return redirect("/admin")
            db.execute ("select id from championats where year = %s and deleted = 0",\
                (request.form.get("select_championat_create_event"),))                
            query_id = db.fetchall()
            championat_id = int(query_id[0]["id"])            
            
            if len(request.form.get("name_create_event")) == 0:
                flash ("Введи имя этапа!")
                return redirect("/admin")
            event_name = request.form.get("name_create_event")

            if len(request.form.get("date_create_event")) == 0:
                flash ("Введи дату этапа!")
                return redirect("/admin")            
            date = request.form.get("date_create_event")

            if request.form.get("select_status_create_event") == None:
                flash ("Выбери статус!")
                return redirect("/admin")
            status = request.form.get("select_status_create_event")
            
            if len(request.form.get("link_create_event")) == 0:
                link = "Пока нету("                
            else:
                link = request.form.get("link_create_event")

            db.execute("INSERT INTO events(championat_id, event_name, date, status, link, deleted)\
            VALUES (%s,%s,%s,%s,%s,%s)",(championat_id, event_name, date, status, link, 0,))
            mysql.connection.commit()       
            flash("Этап добавлен!")

    ##################DELETE EVENT#############################################
        if request.form.get("delete_event") == "delete_event":
            if request.form.get("select_delete_event") == None:
                flash ("Выбери Этап!")
                return redirect("/admin")
            event_id = int(request.form.get("select_delete_event"))
            db.execute("UPDATE events SET deleted = %s WHERE id = %s",\
            (1, event_id,))
            mysql.connection.commit()

    ###################EDIT PENALTY###########################################
        if request.form.get("edit_penalty") == "edit_penalty":
            return redirect("/edit_penalty")
    
    ###################ADD RESULTS!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        if request.form.get("add_result_event") == "add_result_event":
            if request.form.get("select_result_event") == None:
                flash ("Выбери Год!")
            else:
                query_id = int(request.form.get("select_result_event"))
                db.execute("select id from championats where year = %s", (query_id,))
                query_id = db.fetchall()
                champ_id = query_id[0]["id"]                              
                return redirect(url_for('add_results', champ_id=champ_id))
    ###################generate page###########################
    db.execute("SELECT * FROM events WHERE deleted = 0")
    events = db.fetchall()
    db.execute("SELECT * FROM statuses")
    statuses = db.fetchall()
    db.execute("SELECT * FROM championats WHERE deleted = 0")
    championats = db.fetchall()
    db.close()
    return render_template("admin.html", session_id=session["user_id"],\
    championats=championats, statuses=statuses, events=events)



@app.route("/add_results", methods=["POST","GET"])
@login_required
def add_results():    
    db = mysql.connection.cursor()
    if request.method == "POST":
        flash("кнопочку нажали")
    if request.args.get("champ_id"):
        champ_id = int(request.args.get("champ_id"))
    else:
        champ_id = 0
    
    if request.args.get("select_etap"):
        etap_id = int(request.args.get("select_etap"))
    else:
        etap_id = 0

    if request.args.get("select_user"):
        user_id = int(request.args.get("select_user"))
    else:
        user_id = 0  
   
    if request.args.get("select_model"):
        model_id = int(request.args.get("select_model"))
    else:
        model_id = 0
    
    if request.args.get("result_min_sec"):
        result_time = float(request.args.get("result_min_sec"))
    else:
        result_time = 0
    
    
    ######################Get result from page and add to base
    if request.args.get("add_result") == "add_result":
        #test before record
        if champ_id == 0: 
            flash ("Выбери чемпионат")
            return redirect("/admin")

        if (etap_id == 0) or (user_id == 0) or (model_id == 0) or (result_time == 0):
            flash ("Заполни все поля!")           
        else:
            #################add result to base
            db.execute("INSERT INTO results(event_id, user_id, model_id, result, place, score, deleted)\
            VALUES (%s,%s,%s,%s,%s,%s,%s)",(etap_id, user_id, model_id, result_time, 0, 0, 0,))
            mysql.connection.commit()       
            flash("Результат добавлен!")

            ###################Range by result_time
            db.execute("select * from results where event_id = %s and deleted = 0",(etap_id,))
            results = db.fetchall()
            db.execute("select * from scores")
            scores = db.fetchall()
            for result_i in results:
                result_i["place"] = 1
                for result_j in results:
                    if result_j["result"] < result_i["result"]:
                        result_i["place"] = result_i["place"] + 1
            
            
            for result in results:
                champ_score = 1
                for score in scores:
                    if result["place"] == score["place"]:
                        champ_score = score["score"]
                        continue
                    
                db.execute("UPDATE results SET place=%s, score=%s WHERE id = %s",\
                (result["place"], champ_score, result["id"],))
                mysql.connection.commit()
    
    ######################Delete result by button####################################
    if request.args.get("delete_result"):
        result_id_for_delete = int(request.args.get("delete_result"))        
        db.execute("UPDATE results SET deleted=1 WHERE id=%s", (result_id_for_delete,))
        mysql.connection.commit()

        db.execute("select * from results where event_id = %s and deleted = 0",(etap_id,))
        results = db.fetchall()
        db.execute("select * from scores")
        scores = db.fetchall()
        for result_i in results:
            result_i["place"] = 1
            for result_j in results:
                if result_j["result"] < result_i["result"]:
                    result_i["place"] = result_i["place"] + 1
            
            
        for result in results:
            champ_score = 1
            for score in scores:
                if result["place"] == score["place"]:
                    champ_score = score["score"]
                    continue
                    
            db.execute("UPDATE results SET place=%s, score=%s WHERE id = %s",\
            (result["place"], champ_score, result["id"],))
            mysql.connection.commit()

    ######################PAGE LOADING
    db.execute("select * from results where event_id = %s and deleted = 0 order by place",(etap_id,))
    results = db.fetchall()
    for result in results:
        db.execute("select username from users where id = %s",(result["user_id"],))
        temp = db.fetchall()
        result["user_name"] = temp[0]["username"]
        db.execute("select * from models where id = %s",(result["model_id"],))
        temp = db.fetchall()
        result["model_name"] = temp[0]["name"]
        result["model_model"] = temp[0]["model"]

    db.execute("select * from models where owner = %s", (user_id,))
    models = db.fetchall()
    db.execute("SELECT * FROM users")
    users = db.fetchall()
    db.execute("SELECT * FROM events WHERE deleted = 0")
    events = db.fetchall()
    db.execute("SELECT * FROM statuses")
    statuses = db.fetchall()
    db.execute("SELECT * FROM championats WHERE deleted = 0")
    championats = db.fetchall()
    db.close()
    return render_template("/add_results.html", session_id=session["user_id"],\
    championats=championats, statuses=statuses, events=events, champ_id=champ_id,
    etap_id=etap_id, users=users, user_id=user_id, models=models, results=results)


@app.route("/championat", methods=["POST","GET"])
@login_required
def championat():
    db = mysql.connection.cursor()
    db.execute("select * from championats where deleted=0 order by id limit 1")
    temp = db.fetchall()
    championat_year = temp[0]["year"]
    championt_id = temp[0]["id"]

    db.execute("select * from users")
    users = db.fetchall()

    db.execute("select id from events where championat_id=%s and deleted=0", (championt_id,))
    temps = db.fetchall()

    events_id = []

    for temp in temps:
        events_id.append(temp["id"])

    for user in users:
        user["avatar"] = avatar(user["email"],128)

        db.execute("select * from results where user_id=%s and deleted=0",(user["id"],))
        results = db.fetchall()
        sum_score = 0

        for result in results:
            if result["event_id"] in events_id:
                sum_score = sum_score + result["score"]
        
        user["score"] = sum_score

    rows = sorted(users, key=lambda d: d['score'], reverse=True)

    i = 1
    for row in rows:        
        row["place"] = i
        i = i + 1

    return render_template("championat.html", championat_year=championat_year, rows=rows)