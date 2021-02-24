from flask_sqlalchemy import SQLAlchemy
from flask import Flask,render_template,redirect, url_for,flash,request,jsonify,abort,session
from flask_login import LoginManager, UserMixin,current_user,login_user,logout_user,login_required
from flask_moment import Moment
import threading
from sqlalchemy import extract,func,desc
import datetime
import random
import markdown
import re
import time
import requests
import flask_bootstrap
import gunicorn
import gevent
from os import environ, path
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, '.env'))
app = Flask(__name__)
app.secret_key = environ.get('sk')
DIALECT = 'mysql'
DRIVER = 'pymysql'
USERNAME = 'root'
PASSWORD = environ.get('mysqlpassword')
HOST = '114.116.248.90'
PORT = '3306'
DATABASE = 'benben'
#app.config['SQLALCHEMY_DATABASE_URI'] = "{}+{}://{}:{}@{}:{}/{}?charset=utf8".format(DIALECT, DRIVER, USERNAME, PASSWORD, HOST, PORT,DATABASE)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+app.root_path+'/data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
from luogu_spider import doing,BenBen,LuoguUser,User,DeleteWant
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField,DateTimeField, TextAreaField,PasswordField,BooleanField
from wtforms.validators import DataRequired,Length,AnyOf,EqualTo
import click
from flask_migrate import Migrate
migrate=Migrate(app,db)
bootstrap = Bootstrap(app)
thread = threading.Thread(target=doing)
thread.setDaemon(True)
thread.start()
login_manager = LoginManager()
login_manager.init_app(app)
limiter = Limiter(app, key_func=get_remote_address)
moment = Moment()
moment.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    user=User.query.get(int(user_id))
    return user
@app.route("/", methods=['GET', 'POST'])
def main():
	cur = datetime.datetime.utcnow()
	v = BenBen.query.join(BenBen.user).filter(
		extract('year', BenBen.time) == cur.year,
		extract('month', BenBen.time) == cur.month,
		extract('day', BenBen.time) == cur.day,
		LuoguUser.allow_paiming == True
	).count()
	b = BenBen.query.join(BenBen.user).with_entities(func.count().label('count'), BenBen.username, BenBen.uid).filter(
		extract('year', BenBen.time) == cur.year,
		extract('month', BenBen.time) == cur.month,
		extract('day', BenBen.time) == cur.day,
		LuoguUser.allow_paiming == True
	).group_by(BenBen.uid).order_by(desc(func.count())).limit(20)
	# print(b)

	class queryform (FlaskForm):
		username = StringField(
			'用户名', validators=[DataRequired(), Length(1, 20)])
		submit = SubmitField('查询')
	form = queryform()
	if form.validate_on_submit():
		user = LuoguUser.query.filter_by(username=form.username.data).first()
		if user:
			return redirect(url_for('user', uid=user.uid))
			if not user.allow_paiming:
				flash("该用户过分刷水被禁止排名和查询", 'danger')
				return redirect(url_for('main'))
		else:
			flash("用户不存在或在服务器运行的时间内没有发过犇犇", 'danger')
			return redirect(url_for('main'))
	return render_template('zhuye.html', v=v, b=b.all(), form=form)


@app.route("/user/<int:uid>")
def user(uid):
	cur = datetime.datetime.utcnow()
	u = LuoguUser.query.filter_by(uid=uid).first()
	if not u:
		flash("用户不存在或在服务器运行的时间内没有发过犇犇", 'danger')
		return redirect(url_for('main'))
	if not u.allow_paiming:
		flash("该用户过分刷水被禁止排名和查询", 'danger')
		return redirect(url_for('main'))
	ph = u.beipohai
	#print (u.allow_paiming)
	u = BenBen.query.filter(BenBen.uid==uid,BenBen.deleted==False)
	v = BenBen.query.filter(
		extract('year', BenBen.time) == cur.year,
		extract('month', BenBen.time) == cur.month,
		extract('day', BenBen.time) == cur.day,
		BenBen.uid == uid
	).count()
	pm= BenBen.query.join(BenBen.user).with_entities(func.count().label('count'), BenBen.username, BenBen.uid).filter(
		extract('year', BenBen.time) == cur.year,
		extract('month', BenBen.time) == cur.month,
		extract('day', BenBen.time) == cur.day,
		LuoguUser.allow_paiming == True
	).group_by(BenBen.uid).order_by(desc(func.count())).having(func.count()>v).count()
	return render_template('main.html', benbens=u[:-101:-1], v=v, pm=pm+1, ph=ph,uid=uid)


@app.route("/help")
def help():
	return render_template('help.html')


@app.route("/persecute", methods=["POST"])
@limiter.limit("8 per second")
@limiter.limit("320 per minute")
def persecute():
	uid = request.args['uid']
	u = LuoguUser.query.filter_by(uid=uid).first_or_404()
	u.beipohai += 1
	phcs = u.beipohai
	db.session.commit()
	return str(phcs)


@app.route("/banned")
def banned():
	users = LuoguUser.query.with_entities(
		LuoguUser.uid, LuoguUser.username).filter_by(allow_paiming=False).all()
	return jsonify(users)


@app.cli.command()
@click.option('--username', prompt=True, help='Username')
def fengjinyonghu(username):
	click.echo('开始查询...')
	u = LuoguUser.query.filter_by(username=username).first()
	if not u:
		click.echo('该用户不存在.')
		return
	click.echo('查询成功.')
	if not u.allow_paiming:
		click.echo('该用户已被限制')
		return
	click.echo('更改中...')
	u.allow_paiming = False
	db.session.add(u)
	db.session.commit()
	click.echo('成功.')


@app.cli.command()
@click.option('--username', prompt=True, help='Username')
def jiefengyonghu(username):
	click.echo('开始查询...')
	u = LuoguUser.query.filter_by(username=username).first()
	if not u:
		click.echo('该用户不存在.')
		return
	click.echo('查询成功.')
	if u.allow_paiming:
		click.echo('该用户没有被限制')
		return
	click.echo('更改中...')
	u.allow_paiming = True
	db.session.add(u)
	db.session.commit()
	click.echo('成功.')

@app.cli.command()
@click.option('--count', prompt=True)
def fakebenbens(count):
	click.echo('开始生成')
	count=int(count)
	benbenslist=['I AK IOI','洛谷真棒！','咕咕咕','冒泡','kkkAKIOI']
	userlist=LuoguUser.query.all()
	for i in range (count):
		b=random.choice(benbenslist)
		user=random.choice(userlist)
		abb = BenBen()
		abb.text = b
		abb.username = user.username
		abb.uid = user.uid
		abb.time = datetime.datetime.now()
		user.benbens.append(abb)
		db.session.add(abb)
		db.session.commit()
		click.echo("成功生成了一条")

@app.route("/ranklist")
def ranklist():
	page = request.args.get('page', 1, type=int)
	persecute = request.args.get('persecute', 0, type=int)
	begin = request.args.get('begin', 0, type=int)
	end = request.args.get('end', 0, type=int)
	_contentOnly=request.args.get('_contentOnly',0,type=int)
	if persecute:
		p = LuoguUser.query.with_entities(LuoguUser.username,LuoguUser.uid,LuoguUser.beipohai).filter(LuoguUser.beipohai != 0,LuoguUser.allow_paiming == True).order_by(
			desc(LuoguUser.beipohai)).paginate(page, per_page=20, error_out=False)
		if _contentOnly==1:
			return jsonify(p.items)
		return render_template('persecute.html', pagination=p, messages=p.items)
	if begin != 0 and end != 0:
		begin=datetime.datetime.fromtimestamp (begin)
		end=datetime.datetime.fromtimestamp (end)
		p = BenBen.query.join(BenBen.user).with_entities(func.count().label('count'),
														 BenBen.username, BenBen.uid).filter(BenBen.time.between(begin, end),
																							 LuoguUser.allow_paiming == True).group_by(BenBen.uid).order_by(desc(func.count())).paginate(page,
																																														 per_page=20,
																																														 error_out=False)
		if _contentOnly==1:
			return jsonify(p.items)
		return render_template('ranklisttime.html', pagination=p, messages=p.items,begin=begin,end=end)
	cur = datetime.datetime.utcnow()
	p = BenBen.query.join(BenBen.user).with_entities(func.count().label('count'), BenBen.username, BenBen.uid).filter(
		extract('year', BenBen.time) == cur.year,
		extract('month', BenBen.time) == cur.month,
		extract('day', BenBen.time) == cur.day,
		LuoguUser.allow_paiming == True).group_by(BenBen.uid).order_by(desc(func.count())).paginate(page, per_page=20, error_out=False)
	if _contentOnly==1:
			return jsonify(p.items)
	return render_template('ranklist.html', pagination=p, messages=p.items)


@app.route("/timequery", methods=["GET", "POST"])
def timequery():
	class timequeryform (FlaskForm):
		begin = DateTimeField('开始时间点', validators=[DataRequired()])
		end = DateTimeField('结束时间点', validators=[DataRequired()])
		submit = SubmitField('查询')
	form = timequeryform()
	if form.validate_on_submit():
		return redirect("/ranklist?begin={}&end={}".format(int (time.mktime(form.begin.data.timetuple())),int (time.mktime(form.end.data.timetuple()))))
	return render_template("timequery.html", form=form)

class ValidationError (ValueError):
	pass

class CheckPaste ():
	def __init__ (self):
		pass
	def __call__ (self,form,field):
		t=field.data
		if not re.match('^[a-z0-9]{8}',t) or len(t)!=8:
			raise ValidationError('不符合洛谷云剪切板的格式')
			return
		headers = {'User-Agent': "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"}
		k=requests.get('https://www.luogu.com.cn/paste/{}?_contentOnly=1'.format(t),headers=headers)
		t=k.json()
		if t['code']==403:
			raise ValidationError('这是一个非公开的剪贴板')
			return
		if t['code']==404:
			raise ValidationError('这个剪贴板不存在')
			return
		cur = datetime.datetime.now()
		cjsj=t['currentData']['paste']['time']
		cjsj=datetime.datetime.fromtimestamp(cjsj)
		if (cur-cjsj).days>=1:
			raise ValidationError('这个剪贴板的创建时间过早')
			return
		if t['currentData']['paste']['user']['uid']!=int (form.luoguid.data):
			raise ValidationError('创建者不是您')
			return
		text=t['currentData']['paste']['data']
		if text!=form.username.data:
			raise ValidationError('内容错误')
			return

@app.route("/testpaste", methods=['GET', 'POST'])
def test_paste ():
	class queryform (FlaskForm):
		username = StringField(
			'用户名', validators=[DataRequired(), Length(1, 20)])
		luoguid = StringField(
			'洛谷ID', validators=[DataRequired(), Length(1, 20)])
		paste = StringField(
			'剪贴板ID', validators=[DataRequired(), Length(1, 20),CheckPaste()])
		submit = SubmitField('查询')
	form=queryform()
	if form.validate_on_submit():
		return redirect('help')
	return render_template("test_paste.html",form=form)

@app.route("/api/checkbenben")
def api_checkbenben():
	uid=request.args.get('uid',-1,type=int)
	page=request.args.get('page',1,type=int)
	headers = {'User-Agent': "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"}
	try :
		benbens = requests.get('https://www.luogu.com.cn/api/feed/list?user={}&page={}'.format(uid,page),headers=headers).json()
	except :
		time.sleep(5)
		benbens = requests.get('https://www.luogu.com.cn/api/feed/list?user={}&page={}'.format(uid,page),headers=headers).json()
	benbens=benbens['feeds']['result']
	cur = datetime.datetime.now()
	cnt=0
	for i in benbens[::-1]:
		text=markdown.markdown(i['content'])
		username=i['user']['name']
		stime=datetime.datetime.fromtimestamp(i['time'])
		if BenBen.query.filter_by(uid=uid, time=stime).all():
			continue
		abb = BenBen()
		abb.text = text.replace('<p>',"").replace('</p>',"")
		abb.username = username
		abb.uid = uid
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
		if stime.date() == cur.date():
			cnt+=1
	return str(cnt),200,{"Access-Control-Allow-Origin":"*","Access-Control-Allow-Headers":"Origin, X-Requested-With, Content-Type, Accept",'Access-Control-Allow-Methods': 'PUT,POST,GET,DELETE,OPTIONS'}

@app.route ("/admin")
@login_required
def admin ():
    if not current_user.is_admin:
        flash ("无权限！爬！！！！")
        return redirect('/')
    page = request.args.get('page', 1, type=int)
    #l=LuoguUser.query.order_by(LuoguUser.username).paginate(page, per_page=20,error_out=False)
    l=LuoguUser.query.order_by(LuoguUser.username).all()
    #return render_template("admin.html",l=l.items,len=len);
    return render_template("admin.html",l=l,len=len)

@app.route('/login',methods=['GET','POST'])
def login ():
    class LoginForm(FlaskForm):
        username = StringField('Username', validators=[DataRequired(), Length(1, 20)])
        password = PasswordField('Password', validators=[DataRequired(), Length(1, 128)])
        remember = BooleanField('Remember')
        submit = SubmitField('Log in')
    if current_user.is_authenticated:
        return redirect('/')
    form=LoginForm()
    if form.validate_on_submit():
        #return str(form.remember.data)
        username=form.username.data
        password=form.password.data
        remember=True
        user=User.query.filter(User.username==username).first()
        #print (User.query.all())
        if user:
            if user.validate_password(password):
                login_user(user,remember)
                return redirect('/')
            else:
                flash("密码错误")
                return redirect('/')
        else:
            flash("用户不存在")
            return redirect('/')
    return render_template('login.html',form=form)

@app.route('/register',methods=['GET','POST'])
def register ():
    class RegisterForm(FlaskForm):
        username = StringField('Username', validators=[DataRequired(), Length(1, 20)])
        password = PasswordField('Password', validators=[DataRequired(), Length(1, 128)])
        password_check = PasswordField('Password_check', validators=[DataRequired(), Length(1, 128),EqualTo("password")])
        agree = BooleanField('Agree',validators=[])
        submit = SubmitField('Log in')
    if current_user.is_authenticated:
        return redirect('/')
    form=RegisterForm()
    if form.validate_on_submit():
        #return str(form.agree.data)
        username=form.username.data
        password=form.password.data
        user=User.query.filter(User.username==username).first()
        #print (User.query.all())
        if user:
            flash("该用户名已被使用")
        else:
            user=User()
            user.username=username
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash("成功")
            return redirect('/')
    return render_template('register.html',form=form)

@app.route("/logout")
@login_required
def logout ():
    logout_user()
    return redirect('/')

@app.route("/deletewant/new",methods=['GET','POST'])
def deletewantnew():
	benbenid=request.args.get('bid',-1,type=int)
	if (benbenid==-1):
		flash("未提供要删除的犇犇编号！")
		return redirect(url_for('main'))
	benben=BenBen.query.filter(BenBen.id==benbenid).first()
	if not benben:
		flash("这条犇犇不存在！")
		return redirect(url_for('main'))
	if benben.deletewant_id:
		return redirect(url_for('deletewant',id=benben.deletewant_id))
	class queryform (FlaskForm):
		reason = TextAreaField(
			'原因', validators=[DataRequired(), Length(1, 75)])
		submit = SubmitField('查询')
	form=queryform()
	if form.validate_on_submit():
		dwt=DeleteWant()
		dwt.reason=form.reason.data
		benben.deletewant=dwt
		db.session.add(dwt)
		db.session.commit()
		flash ("成功")
		return redirect(url_for('deletewant',id=dwt.id))

	return render_template('deletewantnew.html',benben=benben,form=form)

@app.route("/deletewant/<int:id>")
def deletewant(id):
	dwt=DeleteWant.query.filter(DeleteWant.id==id).first()
	if not dwt:
		flash("未找到该请求")
		return (redirect('/'))
	if dwt.approved==1 and dwt.benben.deleted==False:
		dwt.benben.deleted=True
		db.session.commit()
	return render_template("deletewant.html",dwt=dwt)

@app.cli.command()
@click.option('--id', prompt=True, help='Id')
@click.option('--appr', prompt=True, help='appr')
@click.option('--message', prompt=True, help='message')
def approved_dwt(id,appr,message):
	click.echo('开始查询...')
	dwt = DeleteWant.query.filter(DeleteWant.id == id).first()
	if not dwt:
		click.echo("没找到qwq")
		return
	dwt.approved=appr
	dwt.approved_message=message
	dwt.approved_time=datetime.datetime.now()
	if appr==1:
		click.echo("已通过")
	else:
		click.echo("已拒绝")
	db.session.commit()

@app.route ("/api/list/all")
def api_list_all():
    page=request.args.get('page',1,type=int)
    p = BenBen.query.with_entities(BenBen.id,BenBen.uid,BenBen.username,BenBen.text,BenBen.time).filter(BenBen.deleted == False).order_by(desc(BenBen.time)).paginate(page, per_page=20, error_out=False)
    return jsonify(p.items)