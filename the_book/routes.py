from flask import render_template, request, flash, redirect, url_for, Response
from the_book import app, db, bcrypt
# reference to the_book package
from the_book.forms import RegistrationForm, LoginForm, UpdateAccountForm, SearchForm
from the_book.models import User, Book, to_read_list, BookRating
from sqlalchemy.exc import IntegrityError
from flask_login import login_user, current_user, logout_user, login_required



@app.route('/')
def index():
    form = SearchForm(request.args, meta = {'csrf': False})
    search_by = form.search_by.data
    # print(form.search_by.data)
    # print(type(form.search_by.data))
    # search_by='title'
    search_input = form.search_input.data
    # print(form.search_input.data)
    # print(type(form.search_input.data))
    
    if form.validate():
        
        # flash("redirected","success")
        return redirect(url_for('search_result', search=search_input, by=search_by))
    # else:
    #     flash("error","info")

    return render_template('index.html', page_title="The Book", form=form)
 

@app.route('/search_result')
@app.route('/search_result/<search>&<by>')
def search_result(search,by):
    book_result = Book.query.filter(getattr(Book,str(by)).ilike(f'%{search}%')).all()
    print(book_result)
    return render_template('search_result.html', book_result=book_result)

@app.route('/book_detail/<book_id>')
def book_detail(book_id):
    book = Book.query.filter_by(id=book_id).first()
    title = book.title
    isbn = book.isbn
    return render_template('book_detail.html',book=book, title=title, isbn=isbn)

# @app.route('/boo_detail/<book_id>/add_to_shelf', methods=['POST'])
# @login_required 
# def add_to_shelf(book_id):
#     user = User.query.filter_by(id=current_user.id).first()
#     book = Book.query.filter_by(id=book_id).first()
#     try:
#         #add record to compound key table(many to many), 'readers' is the backref defined in the User class(table)
#         book.readers.append(user)
#         db.session.commit()
#         flash('The book is successfully added to your shelf!', 'success')
#         return redirect(url_for('book_detail', book_id=book.id))
#     except IntegrityError:
#         db.session.rollback()
#         flash('The book is already in your shelf.','info')
#         return redirect(url_for('book_detail', book_id=book.id))

@app.route('/api/shelf', methods=['POST'])
def add_to_shelf(book_id):
    print(book_id)
    user = User.query.filter_by(id=current_user.id).first()
    book = Book.query.filter_by(id=book_id).first()
    try:
        #add record to compound key table(many to many), 'readers' is the backref defined in the User class(table)
        book.readers.append(user)
        db.session.commit()
        return Response(status=201)
    except IntegrityError:
        db.session.rollback()
        error_code = 500
        return error_code


@app.route('/add_rating/<book_id>', methods=['POST'])
# @login_required 
def add_rating(book_id):
    
    user = User.query.filter_by(id=current_user.id).first()
    book = Book.query.filter_by(id=book_id).first()
    star = request.form.get('star')
    print(star)
    try:
        rating = BookRating(user=user, book=book, rating=star)
        db.session.add(rating)
        db.session.commit()
        flash('Your ratings have been added!', 'success')
        return redirect(url_for('book_detail', book_id=book.id))
    except IntegrityError:
        db.session.rollback()
        rating = BookRating.query.filter_by(user=user, book=book).first()
        rating.rating=star
        db.session.commit()
        flash('Your ratings have been updated.','success')
        return redirect(url_for('book_detail', book_id=book.id))


@app.route('/login', methods=['GET', 'POST'])
def login():
    # if user already logged in redirect to homepage
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        # get the first filted record in 'user' table
        user = User.query.filter_by(email=form.email.data).first() 
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            # get the url that before user get redirected to this 'login' page, the url is in the query string with 'next' keyword
            next_page = request.args.get('next')
            # if next_page is not none, redirect to the next_page, otherwise redirect to home page
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Login unsuccessful. Please check email and password.', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        # hash the user input password
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        
        # SQLAlchemy: write a 'user' record for 'user' table with user input data
        user = User(username=form.username.data, email=form.email.data, password=hashed_password) 
        
        # SQLAlchemy: add record to the database
        db.session.add(user) 
        # db.session.flush()
        db.session.commit()
        flash('Your account has been created! You are now able to log in.', 'success')
        return redirect(url_for('login'))
            
    return render_template('register.html', title='Register', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/account', methods=['GET', 'POST'])
@login_required #still need to tell the extension where our login route is located, to do this in the init.py
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        #sqlalchemy: change the data in db
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        # to avoid another post request when reload the page
        return redirect(url_for('account'))
    # populate the form field with current user info
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email

    book_list = Book.query.filter(Book.readers.any(id=current_user.id)).all()
    rate_books = Book.query.filter(Book.raters.has(user_id=current_user.id)).all()
    # for book in rate_books:
    #     ratings = book.raters.rating
    #     print(ratings)

    # print(book_list)
    # print(book_rating)
    return render_template('account.html', title='Account', form=form, book_list=book_list, rate_books=rate_books)




