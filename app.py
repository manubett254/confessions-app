from flask import Flask, render_template, redirect, url_for, flash, request
from models import db, User, Confession, Comment, ConfessionReaction, CommentReaction
from forms import RegisterForm, LoginForm, ConfessionForm, CommentForm
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_migrate import Migrate
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.consumer import oauth_authorized
from sqlalchemy.orm.exc import NoResultFound
from dotenv import load_dotenv
import os
import random

load_dotenv()
from flask import url_for




app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config["OAUTHLIB_INSECURE_TRANSPORT"] = True  # only for local dev

google_bp = make_google_blueprint(
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    scope=[
        "openid",
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email"
    ],
    redirect_to="index"
)

app.register_blueprint(google_bp, url_prefix="/login")

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
migrate = Migrate(app, db)
print("Insecure Transport Enabled:", os.getenv("OAUTHLIB_INSECURE_TRANSPORT"))


@oauth_authorized.connect_via(google_bp)
def google_logged_in(blueprint, token):
    if not token:
        flash("Failed to log in with Google.", category="danger")
        return False
   
    resp = blueprint.session.get("https://www.googleapis.com/oauth2/v2/userinfo")

    if not resp.ok:
        flash("Failed to fetch user info from Google.", category="danger")
        return False

    user_info = resp.json()
    email = user_info["email"]

    query = User.query.filter_by(email=email)
    try:
        user = query.one()
    except NoResultFound:
        user = User(
            username=f"Anon-{random.randint(1000, 9999)}",
            email=email
        )
        db.session.add(user)
        db.session.commit()

    login_user(user)
    flash("Successfully signed in via Google.", category="success")
    return False


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('register'))
        new_user = User(
            username=form.username.data,
            password=generate_password_hash(form.password.data)
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Account created. You can log in now.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('index'))
        flash('Invalid login credentials.', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/')
def index():
    confessions = Confession.query.order_by(Confession.timestamp.desc()).all()
    return render_template('index.html', confessions=confessions)

@app.route('/confess', methods=['GET', 'POST'])
def confess():
    form = ConfessionForm()
    if form.validate_on_submit():
        new_confession = Confession(
            content=form.content.data,
            timestamp=datetime.utcnow(),
            author=current_user if current_user.is_authenticated else None
        )
        db.session.add(new_confession)
        db.session.commit()
        flash('Your confession has been posted.', 'success')
        return redirect(url_for('index'))
    return render_template('confess.html', form=form)

@app.route('/confession/<int:confession_id>', methods=['GET', 'POST'])
def confession_detail(confession_id):
    confession = Confession.query.get_or_404(confession_id)
    form = CommentForm()

    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash('You must be logged in to comment.', 'danger')
            return redirect(url_for('login'))
        new_comment = Comment(
            content=form.content.data,
            author=current_user,
            confession=confession
        )
        db.session.add(new_comment)
        db.session.commit()
        flash('Comment posted.', 'success')
        return redirect(url_for('confession_detail', confession_id=confession_id))

    comments = sorted(confession.comments, key=lambda c: c.timestamp)
    return render_template('confession_detail.html', confession=confession, comments=comments, form=form)

@app.route('/react/<int:confession_id>/<emoji>')
def react(confession_id, emoji):
    confession = Confession.query.get_or_404(confession_id)
    new_reaction = ConfessionReaction(
        emoji=emoji,
        confession_id=confession.id,
        user_id=current_user.id if current_user.is_authenticated else None
    )
    db.session.add(new_reaction)
    db.session.commit()
    flash(f'You reacted {emoji}!', 'success')
    return redirect(request.referrer)

@app.route('/react_comment/<int:comment_id>/<emoji>')
def react_comment(comment_id, emoji):
    comment = Comment.query.get_or_404(comment_id)
    new_reaction = CommentReaction(
        emoji=emoji,
        comment_id=comment.id,
        user_id=current_user.id if current_user.is_authenticated else None
    )
    db.session.add(new_reaction)
    db.session.commit()
    flash(f'You reacted {emoji} to a comment!', 'success')
    return redirect(request.referrer)

@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.username != 'admin':  # adjust this check as you prefer
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    confessions = Confession.query.order_by(Confession.timestamp.desc()).all()
    comments = Comment.query.order_by(Comment.timestamp.desc()).all()
    users = User.query.all()

    return render_template('admin_dashboard.html',
                           confessions=confessions,
                           comments=comments,
                           users=users)




if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
