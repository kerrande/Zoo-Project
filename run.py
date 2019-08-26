#!/usr/bin/env python
from __future__ import print_function
from flask import Flask, render_template, request, flash, redirect
from flask_sqlalchemy import SQLAlchemy
from forms import AnimalForm, ContactForm
import smtplib

import datetime
import dateutil.parser
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

app = Flask(__name__)
app.config['SECRET_KEY']='tFXcmRsHfxl3kyaA4b59'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = '/static/animals'

db = SQLAlchemy(app)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

class Animal(db.Model):
    id_animal = db.Column(db.Integer, primary_key=True)
    name_animal = db.Column(db.String(20), unique=False, nullable = False)
    #image is located at the static/animals/ directory
    dist_animal = db.Column(db.String(2000), unique=False, nullable = False)
    diet_animal = db.Column(db.String(2000), unique=False, nullable = False)
    desc_animal = db.Column(db.String(2000), unique=False, nullable = False)
    breed_animal = db.Column(db.String(2000), unique=False, nullable = False)
    status_animal = db.Column(db.String(20), unique=False, nullable=False)
    fact_animal = db.Column(db.String(2000), unique=False, nullable = True)

    def __repr__(self):
        return "Animal('{}','{}','{}')".format(self.id_animal,self.name_animal,self.status_animal)

#frontend
@app.route("/home")
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/admin/config", methods=['GET', 'POST'])
def animconfig():
    return 0

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def savePic(picture_data):
    currid = len(Animal.query.all()) + 1
    f_name, f_ext = os.path.splitext(picture_data)
    picture_fn = str(currid) + f_ext
    pic_path= os.path.join('static/img', picture_fn)
    picture_data.save(pic_path)

    return picture_fn

@app.route('/addAnimal', methods = ['GET', 'POST'])
def uploadAnimal():
    count = len(Animal.query.all())
    animForm = AnimalForm()
    if animForm.validate_on_submit():
        if animForm.img.data:
            picture_file = savePic(animForm.img.data)

        temp = Animal(name_animal=animForm.name_animal.data,dist_animal=animForm.dist_animal.data,diet_animal=animForm.diet_animal.data,desc_animal=animForm.desc_animal.data,breed_animal=animForm.breed_animal.data,status_animal=animForm.status_animal.data,fact_animal=animForm.fact_animal.data)
        db.session.add(temp)
        #try to add image here
        db.session.commit()
        flash('Animal created for {}!'.format(animForm.name_animal.data),'success')   
    return redirect("/admin")  

@app.route("/admin")
def admin():
    allAnim=Animal.query.all()
    animForm = AnimalForm()
    return render_template("admin.html", animForm=animForm, allAnim=allAnim)

@app.route("/animals")
def animals():
    allAnim=Animal.query.all()
    return render_template("animals.html", allAnim=allAnim)

@app.route("/animals/<id>")
def animal(id):
    anim = Animal.query.get(1)
    return render_template("animal.html", animal=anim)


@app.route("/contact", methods =['GET','POST'])
def contact():
    contactForm = ContactForm()
    if request.method == 'POST':
        gmail_user = 'Email Address'
        gmail_password = 'Password'

        sent_from = gmail_user
        to = [gmail_user]
        body = 'Contact Form Data from Applegate Park Zoo Website\nName: %s\nEmail: %s\nMessage Body:%s' % (contactForm.name.data,contactForm.email.data,contactForm.message.data)

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
        
        flash('Contact Form submitted by {}! We will get back to you as soon as we can!'.format(contactForm.name.data),'success')
        return redirect("/")
    else: # request.method == 'GET':
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
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    # print('Getting the upcoming 10 events')
    events_result = service.events().list(calendarId='primary', timeMin=now,
                                        maxResults=10, singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])

    eventsArr = []

    pictures = ['bear.jpg', 'A bear', 'deer.jpg', 'A deer', 'pck.jpg', 'A peacock', 'what.jpg', 'A male peacock', 'who.jpg', 'A koala']

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
            counter = 0;
        eventsArr.append(eventArr)

    return render_template("events.html", events=eventsArr)

@app.route("/map")
def map():
    return render_template("map.html")

@app.route("/trueAdmin")
def trueAdmin():
    return render_template("")


if __name__ == '__main__':
    app.run(debug=True, host="localhost", port=5000, threaded=True)
