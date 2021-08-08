#-*- coding: utf-8
import requests
from bs4 import BeautifulSoup
import datetime
import time
import threading
from sqlalchemy import extract
from sqlalchemy.dialects.mysql import INTEGER
from app import db,app
from os import environ, path
import re
from dotenv import load_dotenv
basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, '.env'))
host=environ.get('host')
from flask_login import LoginManager, UserMixin,current_user,login_user,logout_user,login_required
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import markdown

class BenBen(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text)
    username = db.Column(db.String(50))
    uid = db.Column(db.Integer)
    time = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('luogu_user.id'))
    user = db.relationship('LuoguUser', uselist=False, backref='BenBen')
    deleted = db.Column(db.Boolean, default=False)
    deletewant_id = db.Column(db.Integer, db.ForeignKey('delete_want.id'))
    deletewant = db.relationship('DeleteWant', uselist=False, backref='BenBen')
    yulu = db.Column(db.Boolean, default=False)
    lid = db.Column(db.Integer,unique=True)


class LuoguUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50))
    uid = db.Column(db.Integer, index=True)
    benbens = db.relationship('BenBen')
    beipohai = db.Column(db.Integer, default=0)
    allow_paiming = db.Column(db.Boolean, default=True)
    user=db.relationship('User')

class DeleteWant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    benben = db.relationship('BenBen',uselist=False)
    reason = db.Column(db.Text)
    approved = db.Column(db.Integer, default=0)
    # approved为0表示未审核，-1为未通过，1为通过
    approved_message=db.Column(db.Text)
    submit_time=db.Column(db.DateTime,default=datetime.datetime.utcnow)
    approved_time=db.Column(db.DateTime)
    submit_user_id = db.Column(db.Integer)

class User (db.Model,UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    luogu_id = db.Column(db.Integer, db.ForeignKey('luogu_user.id'))
    luogu_user = db.relationship('LuoguUser', uselist=False, backref='User')
    username = db.Column(db.String(120), unique=True)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean)
    super_admin = db.Column(db.Boolean)
    loginrecord = db.relationship('LoginRecord')
    notifications=db.relationship('Notification')
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def validate_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_confirmed(self):
        return bool(self.luogu_id!=None)

    def urdnt(self):
        return Notification.query.filter(Notification.recipient_id==self.id,Notification.readed==False).count()

class LoginRecord (db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id=db.Column(db.Integer, db.ForeignKey('user.id'))
    user= db.relationship('User', uselist=False, backref='LoginRecord')
    ip = db.Column(INTEGER(unsigned=True))
    time=db.Column(db.DateTime,default=datetime.datetime.utcnow)

class Notification (db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id=db.Column(db.Integer,index=True)
    recipient_id=db.Column(db.Integer, db.ForeignKey('user.id'))
    recipient=db.relationship('User', uselist=False, backref='Notification')
    text=db.Column(db.Text)
    time=db.Column(db.DateTime,default=datetime.datetime.utcnow)
    readed=db.Column(db.Boolean, default=False)
    annou=db.Column(db.Integer,index=True)

    def sender (self):
        return User.query.get(self.sender_id)

def jiexi(r):
    html = r.text
    soup = BeautifulSoup(html, 'html.parser')
    benbens = soup.find_all(
        name='li', attrs={'class': "am-comment am-comment-primary feed-li"})
    l = list()
    benbens = benbens[::-1]
    for i in benbens:
        uid = i.find(name='a', attrs={'class': 'center'})['href'].split('/')[2]
        username = i.find(name='span', attrs={
                          'class': 'feed-username'}).a.string
        try:
            text = (i.find(name='span', attrs={'class': 'feed-comment'}).p.prettify(
            ).replace('\t', '').replace('\n', '').replace('\r', ''))[3:-4]
        except AttributeError:
            continue
        stime = i.find(name='div', attrs={
                       'class': 'am-comment-meta'}).text.split(' ')
        stime = stime[1]+' '+stime[2]
        stime = datetime.datetime.strptime(stime, '%Y-%m-%d %H:%M:%S\n')
        if BenBen.query.filter_by(text=text, username=username, uid=int(uid), time=stime).all():
            continue
        abb = BenBen()
        abb.text = text
        abb.username = username
        abb.uid = int(uid)
        abb.time = stime
        user = LuoguUser.query.filter_by(uid=uid).first()
        if user:
            user.benbens.append(abb)
            if user.username != username:
                user.username = username
        else:
            user = LuoguUser(username=username, uid=uid)
            db.session.add(user)
            user.benbens.append(abb)
        db.session.add(abb)
        db.session.commit()


headers = {
    'User-Agent': "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"}


def pa():
    r = requests.get('https://www.luogu.com.cn/feed/all', headers=headers)
    return jiexi(r)

def change (stra):
	model='<iframe scrolling="no" border="0" frameborder="no" framespacing="0" allowfullscreen="true" src="https://player.bilibili.com/player.html?{}&high_quality=1" style="top: 5px;left: 0;width: 100%;height: 520px;"></iframe>'
	r=''
	pos=stra.find('?')
	if pos!=-1:
		num=stra[:pos]
	else:
		num=stra
	if num[0:2]=='BV' :
		r='bvid='+num[2:]
	else:
		if num.isdigit():
			r='aid='+num
		else:
			r='aid='+num[2:]
	if pos!=-1:
		r+=stra[pos:]
		r.replace('?','&')
	return model.format(r)

def jp(st):
    print (st.group(1))
    return change (st.group(1))

def pa_api ():
    benbens=requests.get(host,headers=headers).json()
    benbens = benbens['feeds']['result']
    for i in benbens[::-1]:
        text = markdown.markdown(i['content'])
        r = u'<img alt=".*" src="bilibili:([^"]*)">'
        text=re.sub(r, jp, text)
        username = i['user']['name']
        stime = datetime.datetime.fromtimestamp(i['time'])
        uid=i['user']['uid']
        if BenBen.query.filter_by(uid=uid, time=stime).all():
            continue
        abb = BenBen()
        abb.text = text
        abb.username = username
        abb.uid = uid
        abb.time = stime
        abb.lid = i['id']
        user = LuoguUser.query.filter_by(uid=uid).first()
        if user:
            user.benbens.append(abb)
            if user.username != username:
                user.username = username
        else:
            user = LuoguUser(username=username, uid=uid)
            db.session.add(user)
            user.benbens.append(abb)
        db.session.add(abb)
    db.session.commit()

def doing():
    try:
        pa_api()
    except Exception as e:
        app.logger.exception(e)
    global t
    t = threading.Timer(5.0, doing)
    t.start()
    #except BaseException as reason:
    #    fo = open("foo.txt", "w+")
    #    fo.write(str(reason))
    #    fo.close()

t = threading.Timer(5.0, doing)