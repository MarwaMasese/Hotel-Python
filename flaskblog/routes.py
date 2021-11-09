import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from flaskblog import app, db, bcrypt
from flaskblog.forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm
from flaskblog.models import Category, Offer, User, Offer, Category 
from flask_login import login_user, current_user, logout_user, login_required


@app.route("/")
@app.route("/home")
def home():
    page = request.args.get('page', 1, type=int)
    posts = Offer.query.order_by(Offer.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template('user-section/index.html', posts=posts)


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)


@app.route("/offer/new", methods=['GET', 'POST'])
@login_required
def new_offer():
    form = PostForm()
    if form.validate_on_submit():
        offer = Offer(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(offer)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post',
                           form=form, legend='New Post')

# view specific offer 
@app.route("/offer/<int:offer_id>")
def offer(offer_id):
    offer = Offer.query.get_or_404(offer_id)
    return render_template('user-section/product.html', title=offer.title, offer=offer)

#view specific Category 
@app.route("/category/<int:category_id>")
def category(category_id):
    category = Category.query.get_or_404(category_id)
    return render_template('user-section/category.html', title=offer.title, category=category)

# update offer
@app.route("/offer/<int:offer_id>/update", methods=['GET', 'POST'])
@login_required
def update_offer(offer_id):
    offer = Offer.query.get_or_404(offer_id)
    if offer.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        offer.title = form.title.data
        offer.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('offer', offer_id=offer.id))
    elif request.method == 'GET':
        form.title.data = offer.title
        form.content.data = offer.content
    return render_template('create_post.html', title='Update Post',
                           form=form, legend='Update Post')

# delete offer 

@app.route("/post/<int:offer_id>/delete", methods=['POST'])
@login_required
def delete_offer(offer_id):
    post = Offer.query.get_or_404(offer_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('home'))

#hotel profile 

@app.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Offer.query.filter_by(author=user)\
        .order_by(Offer.date_posted.desc())\
        .paginate(page=page, per_page=5)
    return render_template('user_posts.html', posts=posts, user=user)
