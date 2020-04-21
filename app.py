from flask_sqlalchemy import SQLAlchemy
from flask import Flask,render_template
import threading
app = Flask(__name__)
app.secret_key = '11451419260817avdgsjrhsjaj4'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+app.root_path+'/data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
from luogu_spider import doing,BenBen,LuoguUser
thread = threading.Thread(target=doing)
thread.setDaemon(True)
thread.start()
db.create_all()
@app.route("/")
def main ():
    return render_template('main.html',benbens=BenBen.query.all()[::-1])
@app.route("/user/<int:uid>")
def user (uid):
    u=LuoguUser.query.filter_by(uid=uid).first().benbens
    return render_template('main.html',benbens=u[::-1])
