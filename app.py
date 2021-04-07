from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from forms import RegisterForm, LoginForm, CommentForm
from flask_bootstrap import Bootstrap
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import login_user, LoginManager, current_user, logout_user, login_required
import datetime
import os
from dotenv import load_dotenv


dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv(key='TOKEN')
Bootstrap(app)

login_manager = LoginManager()
login_manager.init_app(app)

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///desks.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

from models import User, TaskCard, Desk, association_table, db, Comment


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/', methods=['GET', 'POST'])
def main_page():
    try:
        query_user_desk = Desk.query.join(association_table).join(User).filter(
            (association_table.c.desks_id == Desk.id) & (association_table.c.users_id ==
                                                         current_user.id)
        ).all()
    except AttributeError:
        query_user_desk = []
    print(query_user_desk)
    for item in query_user_desk:
        print(item.name)
    if request.method == 'POST':
        name = request.form.get('name')
        mode = request.form.get('mode')
        new_desk = Desk(
            name=name,
            mode=mode,
        )
        current_user.desks.append(new_desk)
        db.session.add(new_desk)
        db.session.commit()
        return redirect(url_for('main_page'))
    return render_template('index.html', desks=query_user_desk, current_user=current_user)


def str_to_date(string: str):
    return datetime.datetime.strptime(string, '%Y-%m-%d')


@app.route('/desk/<int:index>', methods=['GET', 'POST'])
@login_required
def desk(index):
    desk_obj = Desk.query.filter_by(id=index).first()
    cards = TaskCard.query.filter_by(parent_desk_id=index).all()
    desk_users = User.query.join(association_table).join(Desk).filter(
        (association_table.c.desks_id == index) & (association_table.c.users_id ==
                                                   User.id)
    ).all()
    if request.method == 'POST':
        card_name = request.form.get('name')
        until_date = request.form.get('trip-start')
        finish_date = str_to_date(until_date)

        new_card = TaskCard(
            header=card_name,
            deadline=finish_date,
            parent_desk_id=index,
            has_done=False
        )
        db.session.add(new_card)
        db.session.commit()
        return redirect(url_for('desk', index=index))
    return render_template('desk.html', desk=desk_obj, cards=cards, users=desk_users)

@app.route('/desk/change/<int:card_id>')
@login_required
def change_status(card_id):
    card = TaskCard.query.filter_by(id=card_id).first()
    card.has_done = True
    db.session.commit()
    return redirect(url_for('desk', index=card.parent_desk_id))

@app.route('/desk/<int:index>/<int:card_id>', methods=['GET', 'POST'])
@login_required
def show_card(index, card_id):
    card = TaskCard.query.filter_by(id=card_id).first()
    form = CommentForm()
    comments = Comment.query.filter_by(parent_card_id=card_id).all()
    if request.method == 'POST':
        descr = request.form.get('description')
        title = request.form.get('title')
        date = request.form.get('trip-start')
        comment = request.form.get('comment')
        if descr:
            card.description = descr
            db.session.commit()
        if title:
            card.header = title
            db.session.commit()
        if date:
            card.deadline = str_to_date(date)
            db.session.commit()
        if comment:
            new_comment = Comment(
                text=comment,
                parent_card_id=card_id,
                parent_user_id=current_user.id
            )
            db.session.add(new_comment)
            db.session.commit()
        return redirect(url_for('show_card', card_id=card_id, index=index))
    return render_template('card.html',
                           card=card,
                           index=index,
                           form=form,
                           comments=comments
                           )


@app.route('/<int:index>/add-user', methods=['POST'])
@login_required
def add_user(index):
    user_name = request.form.get('user_name')
    user = User.query.filter_by(name=user_name).first()
    if not user:
        flash('User does not exist!')
        return redirect(url_for('desk', index=index))
    else:
        desk_add = Desk.query.filter_by(id=index).first()
        desk_users = desk_add.users
        if user in desk_users:
            flash('Such user already with us!')
            return redirect(url_for('desk', index=index))
        user.desks.append(desk_add)
        db.session.commit()
        return redirect(url_for('desk', index=index))


@app.route('/desk/delete/<int:card_id>')
@login_required
def delete(card_id):
    card = TaskCard.query.filter_by(id=card_id).first()
    comments = Comment.query.filter_by(parent_card_id=card_id).all()
    for comment in comments:
        db.session.delete(comment)
    db.session.delete(card)
    db.session.commit()
    return redirect(url_for('desk', index=card.parent_desk_id))


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('This email does not exist. Please try again')
            return redirect(url_for('login'))
        else:
            if check_password_hash(user.password, password):
                login_user(user)
                return redirect(url_for('main_page'))
            else:
                flash('Your password is incorrect. Please try again')
                return redirect(url_for('login'))
    return render_template('login.html', form=form)


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        user = User.query.filter_by(email=email).first()
        if not user:
            hashed_pass = generate_password_hash(password)
            new_user = User(email=email,
                            password=hashed_pass,
                            name=name)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('main_page'))
        else:
            flash('Such user already exists. Log in!')
            return redirect(url_for('login'))
    return render_template('register.html', form=form, current_user=current_user)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main_page'))


if __name__ == '__main__':
    app.run()
