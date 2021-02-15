"""from flask import Flask, request, render_template
import pymongo
import sys
import yaml
import logging
import pickle
from PIL import Image as im 
import io
import base64
app = Flask(__name__)
with open("api_config.yaml") as yaml_file:
   config_dict = yaml.load(yaml_file)["config_dictionary"]
db = pymongo.MongoClient(
            'mongo1:27017',
            username=config_dict['mongo_user'],
            password=config_dict['mongo_password'],
            authSource=config_dict['mongo_database'],
            authMechanism='SCRAM-SHA-256')[config_dict['mongo_database']]
try:
    db.list_collections()
except Exception as e:
    logging.error(f"Problem with connection to MongoDB\n{e.args}")
    sys.exit(2)
collection_photos = db[config_dict['collection_photos']]
collection_labels = db[config_dict['collection_labels']]
@app.route('/')
def hello_world():
    return 'Hello, World!'
@app.route('/find_by_tag', methods=['GET','POST'])
def my_form_post():
    if request.method == "GET":
        return render_template('my_form.html')
    else:
        text = request.form['text']
        labels = [x.strip() for x in text.split(',')]
        found = collection_labels.find_one({'labels':{"$elemMatch":{"$elemMatch":{"$in":labels}}}})
        photo = pickle.loads(collection_photos.find_one({"id":found['id']})['photo'])
        photo = im.fromarray(photo)
        b, g, r = photo.split()
        photo = im.merge("RGB", (r, g, b))
        data = io.BytesIO()
        photo.save(data, "JPEG")
        data64 = base64.b64encode(data.getvalue())
        return render_template("my_response.html", picture=data, tags=str(found))
#db.getCollection('labels_comments').find({'labels':{$elemMatch:{$elemMatch:{$in:['person']}}}})
with open('/etc/hostname','r') as f:
    hostname = f.read().strip()
if __name__=='__main__':
    app.run(host=hostname, port=8880)"""

from flask import (
    Flask,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for
)
from pager import Pager
import os
import pymongo
import sys
import yaml
import logging
import pickle
from PIL import Image as im 
import json
import threading
import time

with open("api_config.yaml") as yaml_file:
   config_dict = yaml.load(yaml_file)["config_dictionary"]

db = pymongo.MongoClient(
            'mongo1:27017',
            username=config_dict['mongo_user'],
            password=config_dict['mongo_password'],
            authSource=config_dict['mongo_database'],
            authMechanism='SCRAM-SHA-256')[config_dict['mongo_database']]
try:
    db.list_collections()
except Exception as e:
    logging.error(f"Problem with connection to MongoDB\n{e.args}")
    sys.exit(2)

collection_photos = db[config_dict['collection_photos']]
collection_labels = db[config_dict['collection_labels']]

user_history = {}

class User:
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

    def __repr__(self):
        return f'<User: {self.username}>'

users = []
users.append(User(id=1, username='Anthony', password='password'))
users.append(User(id=2, username='Becca', password='secret'))
users.append(User(id=3, username='Carlos', password='somethingsimple'))


app = Flask(__name__)
app.secret_key = 'somesecretkeythatonlyishouldknow'

@app.before_request
def before_request():
    g.user = None

    if 'user_id' in session:
        user = [x for x in users if x.id == session['user_id']][0]
        g.user = user
        

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session.pop('user_id', None)

        username = request.form['username']
        password = request.form['password']
        
        user = [x for x in users if x.username == username][0]
        if user and user.password == password:
            session['user_id'] = user.id
            return redirect(url_for('profile'))

        return redirect(url_for('login'))

    return render_template('login.html')



@app.route('/find_by_tag')
def empty_find_by_tag():
    return redirect('/find_by_tag/mooncake')

@app.route('/find_by_tag/<index>')
def profile(index):
    user = g.user
    if not user:
        return redirect(url_for('login'))
    user='test'
    if index == 'mooncake':
        return render_template("my_response.html", data="mooncake", info = [0,0,0,0,0],
        next_pic=f"mooncake",
        previous_pic=f"mooncake",
        user=user)
    index = int(index)
	#name = user_history[user][index]
    photo_date = user_history[user][index]
    return render_template("my_response.html", data=photo_date[0], info=photo_date[1],
        next_pic=f"{(index-1)%len(user_history[user])}",
        previous_pic=f"{(index+1)%len(user_history[user])}",
        user=user)

def get_info(founded, text):
	#TODO wybiera tylko jednen pasujacy element ze zdj

	#catched - wszystkie obiekty na zdj
	catched = founded["labels"]
	info = [-1,-1,-1,-1,"not_found"]
	for i in catched:
		#i[:4] tagi zaczynaja sie od 5 elementu
		if text in i[4:]:
			info = i
	return info
			
def get_photos(text, found, user):
	text_data={}
	for i in found[:20]:
		photo = pickle.loads(collection_photos.find_one({"id":i['id']})['photo'])
		photo = im.fromarray(photo)
		b, g, r = photo.split()
		photo = im.merge("RGB", (r, g, b))
		photo.save(f'static/images/{i["id"]}.png')
		#user_history[user].append(i["id"])
		info = get_info(i, text)
		user_history[user].append([i["id"],info])

@app.route('/goto/<user>', methods=['POST', 'GET'])    
def goto(user):
    if not user:
        return redirect(url_for('login'))
    user_history[user]=[]
    text = request.form['index']
    print(text)
    labels = [x.strip() for x in text.split(',')]
    found = [*collection_labels.find({'labels':{"$elemMatch":{"$elemMatch":{"$in":labels}}}})]
    print(found)
    t = threading.Thread(target=get_photos, args=(text, found, user,))
    t.start()
    time.sleep(3)
    return redirect(f'/find_by_tag/0',)

with open('/etc/hostname','r') as f:
    hostname = f.read().strip()

if __name__=='__main__':
    app.run(host=hostname, port=8880)
