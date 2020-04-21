import requests
from bs4 import BeautifulSoup
import datetime
import time
from app import db
s = set()
class BenBen(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String,index=True)
    username = db.Column(db.String)
    uid = db.Column(db.Integer)
    time=db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('luogu_user.id'))
class LuoguUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String)
    uid = db.Column(db.Integer,index=True)
    benbens=db.relationship('BenBen')

def jiexi (r):
    html=r.text
    soup = BeautifulSoup(html, 'html.parser')
    benbens=soup.find_all(name='li',attrs={'class':"am-comment am-comment-primary feed-li"})
    l=list()
    benbens=benbens[::-1]
    for i in benbens:
        uid=i.find(name='a',attrs={'class':'center'})['href'].split('/')[2]
        username=i.find(name='span',attrs={'class':'feed-username'}).a.string
        try:
            text=(i.find(name='span',attrs={'class':'feed-comment'}).p.prettify().replace('\t', '').replace('\n', '').replace('\r', ''))[3:-4]
        except AttributeError:
            continue
        stime=i.find(name='div',attrs={'class':'am-comment-meta'}).text.split(' ')
        stime=stime[1]+' '+stime[2]
        stime=datetime.datetime.strptime(stime, '%Y-%m-%d %H:%M:%S\n')
        if BenBen.query.filter_by(text=text,username=username,uid=int(uid),time=stime).all():
            print ('IEE')
            continue
        abb=BenBen()
        abb.text=text
        abb.username=username
        abb.uid=int(uid)
        abb.time=stime
        user=LuoguUser.query.filter_by(uid=uid).first()
        if user:
            user.benbens.append(abb)
            if user.username != username:
                user.username=username
        else:
            user=LuoguUser(username=username,uid=uid)
            db.session.add(user)
            user.benbens.append(abb)
        db.session.add(abb)
        db.session.commit() 

headers={'User-Agent': "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"}

def pa ():
    r=requests.get('https://www.luogu.com.cn/feed/all',headers=headers)
    data = open("luogubenebn.txt", "w")
    data.write( str(s) )
    data.close()
    return jiexi(r)

def doing():
    while True:
        pa()
        time.sleep(5)


    
