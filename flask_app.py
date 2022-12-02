import datetime

from flask import Flask, render_template, request, url_for, redirect, flash, \
session, abort
from flask_sqlalchemy import sqlalchemy, SQLAlchemy, xrange
from sqlalchemy import false
from werkzeug.security import generate_password_hash, check_password_hash
import json

db_name = "users.db"

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{db}'.format(db=db_name)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["TEMPLATES_AUTO_RELOAD"] = True

# SECRET_KEY required for session, flash and Flask Sqlalchemy to work
app.config['SECRET_KEY'] = 'g#x4WTrQg!3A$pL'

db = SQLAlchemy(app)

class User(db.Model):
    username = db.Column(db.String(100), unique=True, primary_key=True, nullable=False)
    pass_hash = db.Column(db.String(100), nullable=False)
    display_completed = True

    def __repr__(self):
        return '' % self.username

def create_db():
    db.create_all()


@app.route("/register/", methods=["GET", "POST"])
def register():
    try:
        if (session.get(session['username'])):
            return redirect(url_for("dashboard", username=session['username']))
    except:
        print("")
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        if not (username and password):
            flash("Username or Password cannot be empty")
            return redirect(url_for('register'))
        else:
            username = username.strip()
            password = password.strip()

        hashed_pwd = generate_password_hash(password, 'sha256')
        new_user = User(username=username, pass_hash=hashed_pwd)
        db.session.add(new_user)

        try:
            db.session.commit()
        except sqlalchemy.exc.IntegrityError:
            flash("Account with username {u} already exists.".format(u=username))
            return redirect(url_for('register'))

        flash("Account successfully created.")
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/", methods=["GET", "POST"])
@app.route("/login/", methods=["GET", "POST"])
def login():
    try:
        if(session.get(session['username'])):
            return redirect(url_for("dashboard", username=session['username']))
    except:
        print("")
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        if not (username and password):
            flash("Neither field may be empty")
            return redirect(url_for('login'))
        else:
            username = username.strip()
            password = password.strip()

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.pass_hash, password):
            session[username] = True
            session['username'] = username
            return redirect(url_for("login_dash", username=username))
        else:
            flash("Username or password invalid.")

    return render_template("login.html")


@app.route("/user/<username>/")
def login_dash(username):
    if not session.get(username):
        abort(401)
    with open('assignments.json') as f:
        data = json.dumps(json.load(f)).__str__()
    return render_template("dashboard.html", username=username, data=data)


@app.route("/logout/<username>")
def logout(username):
    session.pop(username, None)
    flash("Successfully logged out.")
    return redirect(url_for('login'))

@app.route("/dashboard/<username>", methods=["POST", "GET"])
def dashboard(username):
    #if request.method == "GET":
    deletenulls()
    if not session.get(username) and ".css" not in username:
        abort(401)
    with open('assignments.json') as f:
        return render_template("dashboard.html", data=json.dumps(json.load(f)).__str__(), username=username)

def deletenulls():
    obj = json.load(open('/home/adamburich/mysite/assignments.json'))
    actual_out = [];
    for i in xrange(len(obj)):
        if obj[i]["due"] == None:
            obj[i]["DELETE"] = True

    for i in xrange(len(obj)):
        if obj[i]["DELETE"] == False:
            actual_out.append(obj[i])

    with open('/home/adamburich/mysite/assignments.json', "w") as file:
        file_data = actual_out
        file.seek(0)
        json.dump(file_data, file, indent=4)

@app.route("/dashboard/<username>/delete_assignment", methods=["POST", "GET"])
def delete_assignment(username):
    with open('assignments.json') as f:
        data = json.dumps(json.load(f)).__str__()
    return render_template("delete_assignments.html", username=username, data=data)

@app.route("/dashboard/<username>/delete_assignments/success", methods=["POST", "GET"])
def assignments_deleted(username):
    obj = json.load(open("assignments.json"))
    actual_out = [];
    for i in xrange(len(obj)):
        if obj[i]["user"] == username:
            if request.form.get("assignment"+i.__str__()) == "assignment"+i.__str__():
                obj[i]["DELETE"] = True

    for i in xrange(len(obj)):
        if obj[i]["DELETE"] == False:
            actual_out.append(obj[i])

    with open("assignments.json", "w") as file:
        file_data = actual_out
        file.seek(0)
        json.dump(file_data, file, indent=4)
    return render_template("deleted.html", username=username)

@app.route("/dashboard/<username>/complete_assignments", methods=["POST", "GET"])
def complete_assignments(username):
    with open('assignments.json') as f:
        data = json.dumps(json.load(f)).__str__()
    return render_template("complete_assignments.html", username=username, data=data)

@app.route("/dashboard/<username>/complete_assignments/success", methods=["POST", "GET"])
def assignments_completed(username):
    obj = json.load(open("assignments.json"))
    for i in xrange(len(obj)):
        if obj[i]["user"] == username:
            if request.form.get("assignment"+i.__str__()) == "assignment"+i.__str__():
                obj[i]["completed"] = True

    with open("assignments.json", "w") as file:
        file.seek(0)
        json.dump(obj, file, indent=4)
    return render_template("completed.html", username=username)

@app.route("/dashboard/<username>/add_assignment/success", methods=["POST", "GET"])
def assignment_added(username):
    assignment_label = request.form.get("assignment_name")
    assignment_course = request.form.get("course")
    assignment_due = request.form.get("duedate")
    assignment_weight = request.form.get("slider")
    assignment_notes = request.form.get("notes")
    out = {"user": username,
      "assignment_name": assignment_label,
      "course": assignment_course,
      "due": assignment_due,
      "weight": assignment_weight,
      "notes": assignment_notes,
      "completed": False,
      "DELETE": False
           }
    with open("assignments.json", "r+") as file:
        file_data = json.load(file)
        file_data.append(out)
        file.seek(0)
        json.dump(file_data, file, indent=4)
    return render_template("added.html", username=username)

@app.route("/dashboard/<username>/add_assignment")
def add_assignment(username):
    return render_template("add_assignment.html", username=username)

@app.route("/dashboard/<username>/settings")
def settings(username):
    return render_template('settings.html', username=username)

@app.route("/dashboard/<username>/settings/delete")
def delete_account(username):
    target = User.query.filter_by(username=username).first()
    db.session.delete(target)
    db.session.commit()
    flash("Account successfully deleted.")
    return(logout(username))

@app.route("/dashboard/<username>/view_completed")
def view_completed(username):
    with open('assignments.json') as f:
        data = json.dumps(json.load(f)).__str__()
    return render_template('view_completed.html', username=username, data=data)

@app.route("/dashboard/<username>/settings/help")
def help(username):
    return render_template("help.html", username=username)

if __name__ == "__main__":
    app.run(debug=False)
