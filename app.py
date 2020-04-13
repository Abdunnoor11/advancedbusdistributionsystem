from flask import Flask, render_template, redirect, request, session, flash, url_for
from functools import wraps
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
from models import *

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response

app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

def login_required(f):
    """
    Decorate routes to require login.
    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("student_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def Admin_login_required(f):
    """
    Decorate routes to require login.
    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("id") is None:
            return redirect("/admin_login")
        return f(*args, **kwargs)
    return decorated_function

def booked(student_id):
    today_date = datetime.datetime.now()
    id = Booking_Form.query.filter(
        and_(Booking_Form.student_id == student_id,
             Booking_Form.date > today_date)).first()
    print("Booking_Form ",id)
    if id is None:
        return False
    else:
        booking_date = id.date
        r = today_date < booking_date
        return r

@app.route('/', methods=["GET", "POST"])
@login_required
def index():
    """Log user in"""
    try:
        id = Booking_Form.query.filter_by(student_id=session["student_id"]).first()
        user_route = Schedule.query.filter_by(id=id.route_id).first()
    except:
        user_route=None
        return render_template("Sorry")

    Success = booked(session["student_id"])

    if request.method == "POST":
        From = request.form.get("From")
        Time = request.form.get("Time")
        To = request.form.get("To")

        booking_route = Schedule.query.filter_by(source=From, time=Time, destination=To).first()
        if booking_route is None:
            print("booking_route not avilable")
            return redirect(url_for('index'))
        else:
            a = datetime.datetime.now()
            a = a.replace(day=a.day+1, hour=0, minute=0, second=0, microsecond=0)
            Booking_Form.add_booking(session["student_id"], booking_route.id, a)
            return redirect(url_for('index'))

    sources = Schedule.query.with_entities(Schedule.source).all()
    sources = map(list, sources)
    sources = set([str(i[0]) for i in sources])

    destinations = Schedule.query.with_entities(Schedule.destination).all()
    destinations = map(list, destinations)
    destinations = set([str(i[0]) for i in destinations])

    time = Schedule.query.with_entities(Schedule.time).all()
    time = map(list, time)
    time = set([str(i[0]) for i in time])

    id = Student.query.filter_by(student_id=session["student_id"]).first()

    return render_template('index.html', Success=Success, user_route=user_route, sources=sources, destinations=destinations, time=time, name=id.username)

@app.route('/signup', methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        student_id = request.form.get("student_id")

        if not username:
            return apology("Must provide username")
        elif not email:
            return apology("Must provide email")
        elif not student_id:
            return apology("Must provide student ID")
        elif not request.form.get("password"):
            return apology("Must provide password")

        new_id = Student.query.filter_by(student_id=student_id).first()
        if new_id is None:
            if request.form.get("password") == request.form.get("re_password"):
                password = generate_password_hash(request.form.get("password"))
                Student.add_student(username, email, student_id, password)
                session["student_id"] = student_id
                return redirect(url_for("index"))
            else:
                return apology("password doesn't match")
        else:
            return apology("This ID already exist!")
            # return render_template('signup.html')
    else:
        return render_template('signup.html')

@app.route('/login', methods=["GET", "POST"])
def login():

    session.clear()

    if request.method == "POST":
        if not request.form.get("student_id"):
            return apology("Must provide student id")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("Must provide password")

        student_id = request.form.get("student_id")
        password = request.form.get("password")

        id = Student.query.filter_by(student_id=student_id).first()
        if check_password_hash(id.password, password):
            session["student_id"] = id.student_id
            return redirect(url_for("index"))
        else:
            return apology("invalid username and/or password")
    else:
        return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    # Redirect user to login form
    return redirect(url_for("index"))

@app.route('/full_schedule')
def full_schedule():
    schedules = Schedule.query.all()
    return render_template('full_schedule.html', schedules=schedules)

admin_id = "1298234"
password = "123454321"

@app.route("/admin", methods=["GET", "POST"])
@Admin_login_required
def admin():
    if session["id"] == admin_id:

        if request.method == "POST":
            source = request.form["Source"]
            time = request.form["Time"]
            Destination = request.form["Destination"]

            schedule = Schedule(source=source, time=time, destination=Destination)
            try:
                db.session.add(schedule)
                db.session.commit()
                return redirect('/admin')
            except:
                return 'There was an issue adding your Schedule'

        today_date = datetime.datetime.now()
        journey_date = datetime.datetime.now()
        journey_date = journey_date.replace(day=journey_date.day+1, hour=0, minute=0, second=0, microsecond=0)
        schedules = Schedule.query.all()
        total = {}
        for schedule in schedules:
            t = Booking_Form.query.filter(
                and_(Booking_Form.route_id == schedule.id,
                     Booking_Form.date > today_date)).count()
            total[schedule.id] = t
        return render_template("admin.html", schedules=schedules, journey_date=journey_date.date(), total=total)

@app.route('/delete/<int:id>')
@Admin_login_required
def delete(id):
    if session["id"] == admin_id:
        schedule_to_delete = Schedule.query.get_or_404(id)

        try:
            db.session.delete(schedule_to_delete)
            db.session.commit()
            return redirect('/admin')
        except:
            return 'There was a problem deleting that schedule'

@app.route('/Edit/<int:id>', methods=['GET', 'POST'])
@Admin_login_required
def Edit(id):
    if session["id"] == admin_id:
        schedule_edit = Schedule.query.get_or_404(id)

        if request.method == 'POST':
            schedule_edit.source = request.form["Source"]
            schedule_edit.time = request.form["Time"]
            schedule_edit.Destination = request.form["Destination"]

            try:
                db.session.commit()
                return redirect('/admin')
            except:
                return 'There was an issue updating your task'
        else:
            return render_template('Edit.html', schedule_edit=schedule_edit)

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == "POST":
        if admin_id == request.form.get("id") and password == request.form.get("password"):
            session["id"] = admin_id
            return redirect(url_for("admin"))
    else:
        return render_template("admin_login.html")

@app.route('/admin_logout')
def admin_logout():

    session.clear()
    return redirect(url_for("admin_login"))

def apology(top="", bottom=""):
    """Renders message as an apology to user."""
    def escape(s):
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
            ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=escape(top), bottom=escape(bottom))

if __name__ == '__main__':
    app.run(debug = True)
