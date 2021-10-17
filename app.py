#-*- coding: utf-8
from flask_sqlalchemy import SQLAlchemy
from flask import Flask,render_template,redirect, url_for,flash,request,jsonify,abort,session
from flask_login import LoginManager, UserMixin,current_user,login_user,logout_user,login_required
from flask_moment import Moment
#from flask_ckeditor import CKEditor, CKEditorField
import threading
from functools import wraps
from sqlalchemy import extract,func,desc
import datetime
import random
import markdown
import re
import time
import requests
import flask_bootstrap
#import gunicorn
#import gevent
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
USERNAME = 'songhongyi'
PASSWORD = environ.get('mysqlpassword')
HOST = '127.0.0.1'
PORT = '3306'
DATABASE = 'ben_ben_spider'
app.config['SQLALCHEMY_DATABASE_URI'] = "{}+{}://{}:{}@{}:{}/{}?charset=utf8".format(DIALECT, DRIVER, USERNAME, PASSWORD, HOST, PORT,DATABASE)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+app.root_path+'/data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
from luogu_spider import t,BenBen,LuoguUser,User,DeleteWant,LoginRecord,Notification,doing
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField,DateTimeField, TextAreaField,PasswordField,BooleanField,RadioField
from wtforms.validators import DataRequired,Length,AnyOf,EqualTo
import click
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
migrate=Migrate(app,db)
bootstrap = Bootstrap(app)
#thread = threading.Thread(target=doing)
t.setDaemon(True)
t.start()
login_manager = LoginManager()
login_manager.init_app(app)
#ckeditor = CKEditor(app)
limiter = Limiter(app, key_func=get_remote_address)
moment = Moment()
moment.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    user=User.query.get(int(user_id))
    return user
login_manager.login_view='login'
login_manager.login_message='请先登录'

#app.jinja_env.globals['urdnoti']=

def redirct_back():
	if request.referrer:
		return redirect(request.referrer)
	else:
		return redirect('/')

def unconfimerd ():
	flash("请先进行认证")
	return redirect('/checkpaste')

def confimerd_required (func):
	@wraps(func)
	def decorated_view(*args, **kwargs):
		if not current_user.is_authenticated:
			return login_manager.unauthorized()
		elif not current_user.is_confirmed():
			return unconfimerd()
		return func(*args, **kwargs)
	return decorated_view

@app.route("/", methods=['GET', 'POST'])
def main():
	cur = datetime.datetime.now()
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
			# if not user.allow_paiming:
			# 	flash("该用户过分刷水被禁止排名和查询", 'danger')
			# 	return redirect(url_for('main'))
		else:
			flash("用户不存在或在服务器运行的时间内没有发过犇犇", 'danger')
			return redirect(url_for('main'))
	return render_template('zhuye.html', v=v, b=b.all(), form=form)


@app.route("/user/<int:uid>")
def user(uid):
	cur = datetime.datetime.now()
	u = LuoguUser.query.filter_by(uid=uid).first()
	if not u:
		flash("用户不存在或在服务器运行的时间内没有发过犇犇", 'danger')
		return redirect(url_for('main'))
	# if not u.allow_paiming:
	# 	flash("该用户过分刷水被禁止排名和查询", 'danger')
	# 	return redirect(url_for('main'))
	ph = u.beipohai
	apm=u.allow_paiming
	#print (u.allow_paiming)
	yulus=BenBen.query.filter(BenBen.uid==uid,BenBen.yulu==True).order_by(BenBen.time).all()
	u = BenBen.query.filter(BenBen.uid==uid,BenBen.deleted==False,BenBen.yulu==False).order_by(BenBen.time)
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
	return render_template('main.html', benbens=u[:-101:-1], v=v, pm=pm+1, ph=ph,uid=uid,yulus=yulus,td=datetime.timedelta(hours=8),apm=apm)


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


def __rstcmb():
	global t
	t.cancel()
	# t.__del__()
	time.sleep(2)
	t = threading.Timer(5.0, doing)
	t.setDaemon(True)
	t.start()

@app.cli.command()
def rstcmb ():
	__rstcmb()

@app.route("/api/rstcmb")
def apirstcmb():
	if not current_user.is_admin:
		return jsonify({"error":"Not a admin user"}),403
	if current_user.is_admin:
		__rstcmb()
		return jsonify({"success":'All right'})

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
	cur = datetime.datetime.now()
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
		return redirect("/ranklist?begin={}&end={}".format(int (time.mktime((form.begin.data-datetime.timedelta(hours=8)).timetuple())),int (time.mktime((form.end.data-datetime.timedelta(hours=8)).timetuple()))))
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

@app.route("/checkpaste", methods=['GET', 'POST'])
@login_required
def check_paste ():
	if current_user.is_confirmed():
		flash("您已认证")
		return redirect('/')
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
		luser=LuoguUser.query.filter(LuoguUser.uid==form.luoguid.data).first()
		if not luser:
			flash("洛谷用户不存在，请尝试加入")
			return render_template("check_paste.html", form=form)
		if luser.user:
			flash ("该用户已被认证！")
			return redirect('/')
		current_user.luogu_user=luser
		db.session.commit()
		return redirect('/')
	return render_template("check_paste.html",form=form)

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
		if stime.date() == cur.date():
			cnt+=1
	return str(cnt),200,{"Access-Control-Allow-Origin":"*","Access-Control-Allow-Headers":"Origin, X-Requested-With, Content-Type, Accept",'Access-Control-Allow-Methods': 'PUT,POST,GET,DELETE,OPTIONS'}

@app.route ("/admin")
@confimerd_required
def admin ():
    if not current_user.is_admin:
        flash ("无权限！爬！！！！")
        return redirect('/')
    #page = request.args.get('page', 1, type=int)
    #l=LuoguUser.query.order_by(LuoguUser.username).paginate(page, per_page=20,error_out=False)
    #l=LuoguUser.query.order_by(LuoguUser.username).all()
    #return render_template("admin.html",l=l.items,len=len);
    return render_template("admin.html")

@app.route ('/testip')
def testip():
    if request.headers.getlist("X-Forwarded-For"):
        ip = request.headers.getlist("X-Forwarded-For")[0]
    else:
        ip = request.remote_addr
    return ip

def iptoint (s:str):
	s=s.split('.')
	s=[int (i) for i in s]
	return s[0]*16777216+s[1]*65536+s[2]*256+s[3]

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
                if request.headers.getlist("X-Forwarded-For"):
                    ip = request.headers.getlist("X-Forwarded-For")[0]
                else:
                    ip = request.remote_addr
                lrc=LoginRecord()
                lrc.ip=iptoint(ip)
                db.session.add(lrc)
                lrc.user=current_user
                db.session.commit()
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
            send_notification(content='欢迎您再本站注册！祝您玩的愉快！<br> \n我们建议您尽快在<a href="/checkpaste" >这里</a>完成身份认证！<br> \n如您有任何问题，欢迎您联系<a href="/status">此列表</a>中的任何一位管理，我们很乐意帮您解答。',
                              recipient_id=user.id,annou=0)
            flash("成功",'success')
            return redirect('/')
    return render_template('register.html',form=form)

@app.route("/logout")
@login_required
def logout ():
    logout_user()
    return redirect('/')

@app.route("/deletewant/new",methods=['GET','POST'])
@confimerd_required
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
		dwt.submit_user_id=current_user.id
		benben.deletewant=dwt
		if current_user.luogu_id==benben.user_id:
			benben.deleted = True
			dwt.approved=1
			dwt.approved_message="自删请求"
		elif current_user.super_admin:
			benben.deleted = True
			dwt.approved=1
			dwt.approved_message="管理员请求，自动通过"
		else:
			if form.reason.data=="这里输入删除原因，不超过75个字符":
				flash("请输入删除原因")
				return redirect('/deletewant/new?bid={}'.format(benbenid))
		db.session.add(dwt)
		db.session.commit()
		flash ("成功",'success')
		return redirect(url_for('deletewant',id=dwt.id))

	return render_template('deletewantnew.html',benben=benben,form=form)

@app.route('/deletewant/list')
@confimerd_required
def deletewantlist():
	page=request.args.get('page',1,type=int)
	if not current_user.is_admin:
		p=DeleteWant.query.filter(DeleteWant.submit_user_id==current_user.id)
	else:
		p=DeleteWant.query.filter(DeleteWant.approved==0)
	p=p.paginate(page, per_page=20, error_out=False)
	return render_template("deletewantlist.html", pagination=p, messages=p.items)

@app.route("/deletewant/<int:id>")
@confimerd_required
def deletewant(id):
	dwt=DeleteWant.query.filter(DeleteWant.id==id).first()
	if not dwt:
		flash("未找到该请求")
		return (redirect('/'))
	if not current_user.is_admin and dwt.submit_user_id!=current_user.id:
		flash("无权限!")
		return (redirect('/'))
	if dwt.approved==1 and dwt.benben.deleted==False:
		dwt.benben.deleted=True
		db.session.commit()
	return render_template("deletewant.html",dwt=dwt,u=User.query.filter(User.id==dwt.submit_user_id).first())

@app.route('/admin/deletewant/<int:id>',methods=['GET','POST'])
@confimerd_required
def admindeletewant(id):
	if not current_user.is_admin:
		flash("无权限！爬！！！！")
		return redirect('/')
	dwt=DeleteWant.query.filter(DeleteWant.id==id).first()
	if not dwt:
		flash("不存在")
		return redirect('/')
	if dwt.approved!=0 and not current_user.super_admin:
		flash("已处理")
		return redirect('/')
	if dwt.submit_user_id == current_user.id and not current_user.super_admin:
		flash ("这是您发布的请求，禁止审核自己的请求，请找另一管理")
		return redirect('/')
	class queryform(FlaskForm):
		massage=TextAreaField("留言",validators=[DataRequired()],)
		approve = SubmitField('通过')
		deny = SubmitField('拒绝')
	form=queryform()
	#if request.method=='POST':
	#	return form.appr.data
	if form.validate_on_submit():
		if form.approve.data:
			dwt.approved=1
			dwt.benben.deleted=True
		else:
			dwt.approved=-1
			dwt.benben.deleted = False
		dwt.approved_message=form.massage.data
		send_notification('您提出的删除请求<a href="/deletewant/{}">#{}</a>已经完成了审核，详情请点击蓝色链接，若有异议请联系管理员'.format(dwt.id,dwt.id),dwt.submit_user_id,current_user.id)
		db.session.commit()
		flash("成功",'success')
		return redirect(url_for('deletewant',id=dwt.id))
	return render_template("admindeletewant.html",form=form,dwt=dwt,u=User.query.filter(User.id==dwt.submit_user_id).first())

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

@app.route("/userl/<int:id>")
def userl (id):
	user=User.query.filter(User.id==id).first()
	if not user:
		flash("用户不存在")
		return redirect('/')
	return render_template("userl.html",user=user)

def inttoip (s:int):
	t=""
	t+=str(s//16777216)
	s%=16777216
	t+='.'+str(s//65536)+'.'
	s%=65536
	t+=str(s//256)+'.'+str(s%256)
	return t

@app.route ('/admin/userl/<int:id>',methods=['GET','POST'])
@confimerd_required
def adminuserl (id):
	if not current_user.super_admin:
		flash("无权限，爬！")
		return redirect('/')
	user = User.query.filter(User.id == id).first()
	if not user:
		flash("用户不存在")
		return redirect('/')
	lrds=LoginRecord.query.join(LoginRecord.user).with_entities(func.count().label('count'), LoginRecord.ip,LoginRecord.time).filter(LoginRecord.user_id==user.id).group_by(LoginRecord.ip).order_by(desc(func.count()))
	class QueryForm(FlaskForm):
		adming=SubmitField('给予管理')
	form=QueryForm()
	if form.validate_on_submit():
		if form.adming.data:
			user.is_admin=not user.is_admin
			db.session.commit()
	return render_template('adminuserl.html',form=form,user=user,lrds=lrds,inttoip=inttoip)

@app.route("/api/adduser/<int:id>")
def add_user (id):
	user = LuoguUser.query.filter(LuoguUser.uid == id).first()
	if user:
		return jsonify({"status":"fail","message":"User exists"})
	user=LuoguUser()
	headers = {'User-Agent': "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"}
	data=requests.get("https://www.luogu.com.cn/api/user/search?keyword={}".format(id),headers=headers).json()
	data=data['users'][0]
	user.uid=id
	user.username=data['name']
	user.color=data['color']
	user.ccf_level=data['ccfLevel']
	db.session.add(user)
	db.session.commit()
	return jsonify({"status":"success"})

@app.route("/status")
def status ():
	bcount=BenBen.query.count()
	ulcount=User.query.count()
	lucount=LuoguUser.query.count()
	admins=User.query.filter(User.is_admin==1).all()
	cfdulcount=User.query.filter(User.luogu_user).count()
	return render_template("status.html",len=len,bcount=format(bcount,','),ulcount=format(ulcount,','),lucount=format(lucount,','),cfdulcount=format(cfdulcount,','),admins=admins)

@app.route("/notification")
@login_required
def notification():
	ntfcs=Notification.query.filter(Notification.recipient_id==current_user.id)
	ntl=ntfcs.all()
	urds=Notification.query.filter(Notification.recipient_id==current_user.id,Notification.readed==False).all()
	ntfcs.update({'readed':True})
	db.session.commit()
	return render_template('notification.html',ntl=ntl[::-1],urds=urds)

def send_notification (content:str,recipient_id,sender_id=1,annou=None):
	temp=Notification()
	temp.text=content
	temp.recipient_id=recipient_id
	temp.sender_id=sender_id
	temp.annou=annou
	db.session.add(temp)
	db.session.commit()

@app.route("/api/rstcmb")
@login_required
def api_rstcmb ():
	if current_user.is_admin:
		__rstcmb()
	else:
		return abort(503)
	return jsonify({"result":"success"})

@app.errorhandler(500)
def handler500 (error):
	return '<img src="https://http.cat/500"></img>'

@app.errorhandler(404)
def handler404 (error):
	return '<img src="https://http.cat/404"></img>'

@app.route ("/api/backup/extend")
def backup_extend():
	cur = datetime.datetime.now()
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
	).group_by(BenBen.uid).order_by(desc(func.count())).limit(50).all()
	num=BenBen.query.join(BenBen.user).with_entities(BenBen.uid).filter(
		extract('year', BenBen.time) == cur.year,
		extract('month', BenBen.time) == cur.month,
		extract('day', BenBen.time) == cur.day,
		LuoguUser.allow_paiming == True
	).group_by(BenBen.uid).count()
	#print (b)
	return jsonify({"num_user":num,"num_benben":v,"top_50":b})

@app.route ("/admin/announcement/<int:id>")
@confimerd_required
def admin_announcement (id):
	if not current_user.super_admin:
		return abort(503)
	t=Notification.query.filter(Notification.annou==id).first()
	if not t:
		flash("没有这个公告")
		return abort(404)
	text=t.text
	num_a=Notification.query.filter(Notification.annou==id).count()
	num_r=Notification.query.filter(Notification.annou==id,Notification.readed==1).count()
	return render_template("adminannouncement.html",text=text,num_a=num_a,num_r=num_r,percent=int((num_r/num_a)*100))

@app.route("/admin/announcement/new",methods=['GET','POST'])
@confimerd_required
def admin_announcement_new ():
	if not current_user.super_admin:
		return abort(503)
	class queryform (FlaskForm):
		submit = SubmitField('发送')
	form=queryform()
	if form.validate_on_submit():
		#return form.text.data
		luid=User.query.count()
		aid=db.session.query(func.max(Notification.annou).label('max_aid')).one().max_aid
		if not aid:
			aid=0
		contest=request.form['md-html-code']
		aid+=1
		for i in range (1,luid+1):
			send_notification(content=contest,recipient_id=i,sender_id=current_user.id,annou=aid)
		db.session.commit()
		return redirect(url_for('admin_announcement',id=aid))
	return render_template("announcementnew.html",form=form)

@app.route ("/api/addyulu")
@confimerd_required
def addyulu():
	if not current_user.is_admin:
		return abort (503)
	id=request.args.get('bid',-1,type=int)
	ben=BenBen.query.filter(BenBen.id==id).first_or_404()
	ben.yulu=True
	db.session.commit()
	return redirect(url_for('user',uid=ben.uid))

@app.route ("/api/backup/daily")
def backup_daily ():
	if  not request.headers.get('password') or not check_password_hash(environ.get('backuppasswordhash'),request.headers.get('password')):
		return abort(503)
	year = request.args.get('year',type=int)
	month = request.args.get('month', type=int)
	day = request.args.get('day', type=int)
	# lst=BenBen.query.with_entities(func.date_format(BenBen.time,"%H:%M").label('time'),func.count()).filter(
	# 	extract('year', BenBen.time) == year,
	# 	extract('month', BenBen.time) == month,
	# 	extract('day', BenBen.time) == day,
	# 	LuoguUser.allow_paiming == True).group_by('time').all()
	ti=datetime.datetime(year=year,month=month,day=day)
	lst=[{
				'time' : i,
				"count":BenBen.query.with_entities(BenBen.time,BenBen.uid).filter(
					BenBen.time.between(ti+datetime.timedelta(minutes=i),ti+datetime.timedelta(minutes=i+1))
				).count(),
				'list':BenBen.query.with_entities(BenBen.uid,func.count().label('count')).filter(
					BenBen.time.between(ti+datetime.timedelta(minutes=i),ti+datetime.timedelta(minutes=i+1))
				).group_by(BenBen.uid).order_by(desc(func.count())).all()
			} for i in range (24*60)]
	#alst=[sum(lst[:i+1]) for i in range (24*60)]
	return jsonify(lst)

headers = {
    'User-Agent': "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"}


@app.route ("/api/list/proxy")
def api_list_proxy ():
	page=request.args.get('page',1,type=int)
	p = BenBen.query.join(BenBen.user).with_entities(BenBen.id, BenBen.uid,BenBen.lid, BenBen.username, BenBen.md_code ,BenBen.text, BenBen.time,LuoguUser.ccf_level,LuoguUser.badge,LuoguUser.color).filter(
		BenBen.deleted == False,LuoguUser.allow_paiming==True).order_by(desc(BenBen.time)).paginate(page, per_page=20, error_out=False)
	r=list()
	for i in p.items:
		r.append({
			"content":i.md_code or i.text,
			"id":i.lid,
			"time":int(i.time.timestamp()),
			"type":1,
			"user":
				{
					"badge":i.badge,
					"ccfLevel":i.ccf_level,
					"color":i.color,
					"name":i.username,
					"uid":i.uid
				}
		})
	return jsonify(r)

@app.route("/chat",methods=['GET','POST'])
@confimerd_required
def chat ():
	rid=request.args.get("rid",-1,type=int)
	class queryform (FlaskForm):
		submit = SubmitField('发送')
	form=queryform()
	if form.validate_on_submit():
		if rid==-1 or not current_user.is_admin:
			rid=request.form.get('rid')
		send_notification(request.form['md-html-code'],rid,current_user.id)
		flash("成功",'success')
		return redirct_back()
	admins=User.query.filter(User.is_admin==True).all()
	return render_template("chat.html",admins=admins,form=form,rid=rid)

@app.route("/api/banuser")
@confimerd_required
def api_banuser():
	if not current_user.super_admin:
		flash ("无权限")
		redirct_back()
	uid=request.args.get("uid",-1,type=int)
	user=LuoguUser.query.filter(LuoguUser.uid==uid).first()
	if not user:
		flash("用户不存在")
		return redirct_back()
	if user.allow_paiming:
		flash ("已封禁","success")
		user.allow_paiming=False
	else:
		flash ("已解封","success")
		user.allow_paiming=True
	db.session.commit()
	return redirect("/user/{}".format(uid))

@app.route("/api/pbb/verify")
def apiverify():
	uid=request.args.get("uid",type=int)
	user = LuoguUser.query.filter(LuoguUser.uid == uid).first()
	if not user:
		add_user(uid)
	headers = {
		'User-Agent': "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"}
	data = requests.get("https://www.luogu.com.cn/api/user/search?keyword={}".format(uid), headers=headers).json()
	data = data['users'][0]
	slogan=data['slogan']
	if slogan!="exlg伪犇验证":
		return abort(403)
	if user.ptoken:
		return user.ptoken
	user.ptoken = str(uuid.uuid4()).replace('-',"")
	db.session.commit()
	return str(user.ptoken)

@app.route("/api/pbb/post",methods=['POST'])
def apipbbpost():
	uid=request.form.get("uid")
	token=request.form.get("token")
	user=LuoguUser.query.filter(LuoguUser.uid==uid).first()
	if not user:
		return "不存在的用户",406
	if user.ptoken!=token:
		return "token 错误",406
	text=request.form.get("text")
	if len(text)==0:
		return "禁止空白",406
	nbb=BenBen()
	nbb.md_code=text
	nbb.text=markdown.markdown(text).replace('<p>',"").replace('</p>',"")
	nbb.uid=uid
	nbb.username=user.username
	nbb.time=datetime.datetime.utcnow()+datetime.timedelta(hours=8)
	user.benbens.append(nbb)
	db.session.add(nbb)
	db.session.commit()
	return jsonify({"status": "succeed", "message": "发送成功"})
