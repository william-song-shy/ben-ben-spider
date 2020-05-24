from flask_sqlalchemy import SQLAlchemy
from flask import Flask,render_template
from flask import Flask,render_template,redirect, url_for,flash,request,jsonify,abort
import threading
from sqlalchemy import extract,func,desc
import datetime
import random
app = Flask(__name__)
app.secret_key = '11451419260817avdgsjrhsjaj4'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+app.root_path+'/data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
from luogu_spider import doing,BenBen,LuoguUser
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField,DateTimeField
from wtforms.validators import DataRequired,Length
import click
bootstrap = Bootstrap(app)
thread = threading.Thread(target=doing)
thread.setDaemon(True)
thread.start()
db.create_all()
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
            if not user.allow_paiming:
                flash("该用户过分刷水被禁止排名和查询", 'danger')
                return redirect(url_for('main'))
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
    if not u.allow_paiming:
        flash("该用户过分刷水被禁止排名和查询", 'danger')
        return redirect(url_for('main'))
    ph = u.beipohai
    #print (u.allow_paiming)
    u = u.benbens
    v = BenBen.query.filter(
        extract('year', BenBen.time) == cur.year,
        extract('month', BenBen.time) == cur.month,
        extract('day', BenBen.time) == cur.day,
        BenBen.uid == uid
    ).count()
    pmq = db.session.execute("select count(*) from (select uid,username,count(*) as count from ben_ben where time>=datetime('now','start of day','+0 day') and time<datetime('now','start of day','+1 day') group by uid order by count desc) where count > {}".format(v))
    pm = 0
    for i in pmq:
        pm += i[0]
    return render_template('main.html', benbens=u[:-101:-1], v=v, pm=pm, ph=ph)


@app.route("/help")
def help():
    return render_template('help.html')


@app.route("/persecute", methods=["POST"])
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
	uids={'songhongyi':122079,'kkksc03':1,'chen_zhe':8457,'一扶苏一':65363}
	usernamelist=['kkksc03','songhongyi','chen_zhe','一扶苏一']
	for i in range (count):
		b=random.choice(benbenslist)
		p=random.choice(usernamelist)
		user=LuoguUser.query.filter_by(username=p).first()
		if not user:
			user = LuoguUser(username=p, uid=uids[p])
			db.session.add(user)
		abb = BenBen()
		abb.text = b
		abb.username = p
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
    begin = request.args.get('begin', "", type=str)
    end = request.args.get('end', "", type=str)
    if persecute:
        p = LuoguUser.query.filter(LuoguUser.beipohai != 0).order_by(
            desc(LuoguUser.beipohai)).paginate(page, per_page=20, error_out=False)
        return render_template('persecute.html', pagination=p, messages=p.items)
    if begin != "" and end != "":
        p = BenBen.query.join(BenBen.user).with_entities(func.count().label('count'),
                                                         BenBen.username, BenBen.uid).filter(BenBen.time.between(begin, end),
                                                                                             LuoguUser.allow_paiming == True).group_by(BenBen.uid).order_by(desc(func.count())).paginate(page,
                                                                                                                                                                                         per_page=20,
                                                                                                                                                                                         error_out=False)
        return render_template('ranklisttime.html', pagination=p, messages=p.items,begin=begin,end=end)
    cur = datetime.datetime.now()
    p = BenBen.query.join(BenBen.user).with_entities(func.count().label('count'), BenBen.username, BenBen.uid).filter(
        extract('year', BenBen.time) == cur.year,
        extract('month', BenBen.time) == cur.month,
        extract('day', BenBen.time) == cur.day,
        LuoguUser.allow_paiming == True).group_by(BenBen.uid).order_by(desc(func.count())).paginate(page, per_page=20, error_out=False)
    return render_template('ranklist.html', pagination=p, messages=p.items)


@app.route("/timequery", methods=["GET", "POST"])
def timequery():
    class timequeryform (FlaskForm):
        begin = DateTimeField('开始时间点', validators=[DataRequired()])
        end = DateTimeField('结束时间点', validators=[DataRequired()])
        submit = SubmitField('查询')
    form = timequeryform()
    if form.validate_on_submit():
        return redirect("/ranklist?begin={}&end={}".format(form.begin.data, form.end.data))
    return render_template("timequery.html", form=form)
