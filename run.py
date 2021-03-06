#!/usr/bin/env python
from __future__ import print_function
from flask import jsonify, Flask, render_template, request, flash, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from forms import LoginForm, AnimalForm, UpdateAnimalForm, ContactForm
import smtplib

import datetime
import dateutil.parser
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from werkzeug.utils import secure_filename

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tFXcmRsHfxl3kyaA4b59'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = '/static/animals'

# Uploads
app.config['UPLOADS_DEFAULT_DEST'] = '/static/img/'
app.config['UPLOADS_DEFAULT_URL'] = 'http://localhost:5000/static/img/'

app.config['UPLOADED_IMAGES_DEST'] = '/static/img/'
app.config['UPLOADED_IMAGES_URL'] = 'http://localhost:5000/static/img/'


db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

pw_hash = bcrypt.generate_password_hash('MercedZoo2019')


class Animal(db.Model):
    id_animal = db.Column(db.Integer, primary_key=True)
    names = db.Column(db.String, unique=False, nullable=True)
    name_animal = db.Column(db.String, unique=False, nullable=True)
    dist_animal = db.Column(db.String, unique=False, nullable=True)
    diet_animal = db.Column(db.String, unique=False, nullable=True)
    desc_animal = db.Column(db.String, unique=False, nullable=True)
    breed_animal = db.Column(db.String, unique=False, nullable=True)
    behavior_animal = db.Column(db.String, unique=False, nullable=True)
    status_animal = db.Column(db.String, unique=False, nullable=True)
    fact_animal = db.Column(db.String, unique=False, nullable=True)
    image_filename = db.Column(db.String, default=None, nullable=True)
    image_url = db.Column(db.String, default=None, nullable=True)

    def __repr__(self):
        return "Animal('{}','{}','{}')".format(self.id_animal, self.name_animal, self.status_animal)


# frontend
@app.route("/home")
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if(request.method == 'GET'):
        return render_template("login.html", form=form)
    else:
        url = "/admin/{}".format(form.password.data)
        return redirect(url)


@app.route('/addAnimal/<mypass>', methods=['GET', 'POST'])
def uploadAnimal(mypass):
    if(bcrypt.check_password_hash(pw_hash,mypass)):
        count = len(Animal.query.all())
        animForm = AnimalForm()
        if animForm.validate_on_submit():
            # debug here
            f = animForm.img.data
            img_filename = secure_filename(f.filename)
            f.save(os.path.join(app.root_path, 'static/img', img_filename))
            temp = Animal(name_animal=animForm.name_animal.data,names=animForm.names.data, behavior_animal=animForm.behavior_animal.data, dist_animal=animForm.dist_animal.data, diet_animal=animForm.diet_animal.data, desc_animal=animForm.desc_animal.data,
                          breed_animal=animForm.breed_animal.data, status_animal=animForm.status_animal.data, fact_animal=animForm.fact_animal.data, image_filename=img_filename, image_url="static/img/{}".format(img_filename))
            db.session.add(temp)
            db.session.commit()
            flash('Animal created for {}!'.format(
                animForm.name_animal.data), 'success')
        else:
            flash('Unable to create Animal', 'danger')
        url ="/admin/{}".format(mypass)
        return redirect(url)


@app.route("/animals/<id>/update/<mypass>", methods=['GET', 'POST'])
def update_post(id, mypass):
    if(bcrypt.check_password_hash(pw_hash,mypass)):
        anim = Animal.query.get_or_404(id)
        form = UpdateAnimalForm()
        if form.validate_on_submit():
            anim.name_animal = form.name_animal.data
            anim.names = form.names.data
            anim.dist_animal = form.dist_animal.data
            anim.desc_animal = form.desc_animal.data
            anim.breed_animal = form.breed_animal.data
            anim.diet_animal = form.diet_animal.data
            anim.behavior_animal = form.behavior_animal.data
            anim.status_animal = form.status_animal.data
            anim.fact_animal = form.fact_animal.data

            if form.img.data:
                f = form.img.data
                img_filename = secure_filename(f.filename)
                f.save(os.path.join(app.root_path, 'static/img', img_filename))

            db.session.commit()

            flash('Animal has been successfully updated!', 'success')
            return redirect("/animals/{}".format(id))
        
        form.name_animal.data = anim.name_animal
        form.names.data = anim.names
        form.dist_animal.data = anim.dist_animal
        form.desc_animal.data = anim.desc_animal
        form.breed_animal.data = anim.breed_animal
        form.diet_animal.data = anim.diet_animal
        form.behavior_animal.data = anim.behavior_animal
        form.status_animal.data = anim.status_animal
        form.fact_animal.data = anim.fact_animal
        return render_template('update.html', animForm=form, legend='Update Animal', animid=id, password = mypass)
   


@app.route("/delete/<id>/<mypass>",  methods=['GET', 'POST'])
def delAnim(id, mypass):
    if(bcrypt.check_password_hash(pw_hash, mypass)):
        anim = Animal.query.get_or_404(id)
        db.session.delete(anim)
        db.session.commit()
        flash('Animal succesfully deleted', 'success')
    url = "/admin/{}".format(mypass)
    return redirect(url)


@app.route("/admin/<mypass>",  methods=['GET', 'POST'])
def admin(mypass):
    if(bcrypt.check_password_hash(pw_hash, mypass)):
        allAnim = Animal.query.all()
        animForm = AnimalForm()
        return render_template("admin.html", password=mypass, allAnim=allAnim, animForm=animForm)
    flash('Incorrect Password', 'warning')
    return redirect("/login")


@app.route("/animals")
def animals():
    allAnim = Animal.query.all()
    for animal in allAnim:
        print(animal.image_url)
    return render_template("animals.html", allAnim=allAnim)


@app.route("/animals/<id>")
def animal(id):
    anim = Animal.query.get(id)
    print(anim.image_url)
    return render_template("animal.html", animal=anim)


@app.route("/contact", methods=['GET', 'POST'])
def contact():
    contactForm = ContactForm()
    if request.method == 'POST':
        gmail_user = 'applegateparkzoomerced@gmail.com'
        gmail_password = 'MercedZoo'

        sent_from = gmail_user
        to = [gmail_user]
        body = 'Contact Form Data from Applegate Park Zoo Website\nName: %s\nEmail: %s\nMessage Body:%s' % (
            contactForm.name.data, contactForm.email.data, contactForm.message.data)

        email_text = """\
        From: %s
        To: %s
        Subject: %s

        %s
        """ % (sent_from, ", ".join(to), subject, body)

        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(gmail_user, gmail_password)
        server.sendmail(sent_from, to, email_text)
        server.close()

        flash('Contact Form submitted by {}! We will get back to you as soon as we can!'.format(
            contactForm.name.data), 'success')
        return redirect("/")
    else:  # request.method == 'GET':
        return render_template('contact.html', contForm=contactForm)


@app.route("/events")
def events():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)

    # Call the Calendar API
    now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    # print('Getting the upcoming 10 events')
    events_result = service.events().list(calendarId='primary', timeMin=now,
                                          maxResults=10, singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])

    eventsArr = []

    pictures = ['bear.jpg', 'A bear', 'deer.jpg', 'A deer', 'pck.jpg',
                'A peacock', 'what.jpg', 'A male peacock', 'who.jpg', 'A koala']

    counter = 0
    for event in events:
        eventArr = []
        start = event['start'].get('dateTime', event['start'].get('date'))
        d = dateutil.parser.parse(start)
        startDate = d.strftime('%A, %B %-d at %-I:%M %p')
        eventArr.append(startDate)
        eventArr.append(event['summary'])
        eventArr.append(pictures[counter])
        eventArr.append(pictures[counter+1])
        counter += 2
        if(counter > len(pictures)):
            counter = 0
        eventsArr.append(eventArr)

    return render_template("events.html", events=eventsArr)


@app.route("/map")
def map():
    return render_template("map.html")


if __name__ == '__main__':
    app.run(debug=True, host="localhost", port=5000, threaded=True)
