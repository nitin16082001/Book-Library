from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from werkzeug.utils import secure_filename
import time
import os

app = Flask(__name__, static_url_path='/static')

app.secret_key = 'nitu1608'  # Replace 'your_secret_key_here' with a strong, unique key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///book_registration.db'
# app.config['TEMPLATES_AUTO_RELOAD'] = True  # This is optional but can help during development
db = SQLAlchemy(app)

uploads_dir = os.path.join(app.root_path, 'static/Uploads')
os.makedirs(uploads_dir, exist_ok=True)
uploads_dir = os.path.join(app.root_path, 'static/Uploads/Books')
os.makedirs(uploads_dir, exist_ok=True)
uploads_dir = os.path.join(app.root_path, 'static/Uploads/Covers')
os.makedirs(uploads_dir, exist_ok=True)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    regAt = db.Column(db.String(100), nullable=False)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True)
    title = db.Column(db.String(100), nullable=False)
    writer = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    img_file = db.Column(db.String(100), nullable=False)
    pdf_file = db.Column(db.String(100), nullable=False)
    added_by = db.Column(db.String(100), nullable=False)
    added_at = db.Column(db.String(100), nullable=False)
    likes = db.Column(db.Integer, nullable=False, default=0)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['passWord']

        user = User.query.filter_by(email=username).first()

        if user and user.password == password:
            if user.role == "Admin":
                session['logged_in'] = True
                session['uname'] = user.name
                return redirect(url_for('admin'))
            
            else:
                session['logged_in'] = True
                session['uname'] = user.name
                return redirect(url_for('home'))
        else:
            return redirect("/")

@app.route('/home')
def home():
    if 'logged_in' in session:
        featured_books_data = Book.query.order_by(desc(Book.id)).limit(4).all()
        latest_books = Book.query.order_by(Book.id.desc()).slice(4, 12).all()
        user = session.get('uname')
        return render_template('Home.html', user=user, featured_books_data=featured_books_data, latest_books=latest_books)

    else:
        flash('Please log in to access the dashboard', 'danger')
        return redirect("/")

@app.route('/books')
def list_books():
    user = session.get('uname')
    books = Book.query.all()
    page = request.args.get('page', 1, type=int)
    start_idx = (page - 1) * 12
    end_idx = start_idx + 12
    books_on_page = books[start_idx:end_idx]
    total_pages = (len(books) + 12 - 1) // 12    
    return render_template('books.html', books=books_on_page, current_page=page, total_pages=total_pages, user=user)

@app.route('/about')
def about():
    user = session.get('uname')
    return render_template('about.html', user=user)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect("/")

@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        uname = request.form['uname']
        email = request.form['email']
        password = request.form['password']

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            message = "Email already registered"
            redirect_url = url_for('index')
        else:
            new_user = User(name=uname, email=email, password=password, role="Reader", regAt=str(time.strftime("%d-%m-%Y %I:%M:%S %p")))
            db.session.add(new_user)
            db.session.commit()
            
            message = "Registration successful"
            redirect_url = url_for('index')
        
        return render_template('index.html', message=message, redirect_url=redirect_url)

@app.route('/register_user', methods=['POST'])
def register_user():
    if request.method == 'POST':
        uname = request.form['name']
        email = request.form['email']
        password = request.form['password']

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("User is already exist", "alert")
        else:
            new_user = User(name=uname, email=email, password=password, role="Reader", regAt=str(time.strftime("%d-%m-%Y %I:%M:%S %p")))
            db.session.add(new_user)
            db.session.commit()
            
        return redirect(url_for("manage_user"))

@app.route('/admin')
def admin():
    if 'logged_in' in session:
        users = User.query.all()
        books = Book.query.all()
        total_users = User.query.count()
        total_books = Book.query.count()
        return render_template('dashboard.html', total_users=total_users, users=users, total_books=total_books, books=books)
    else:
        flash('Please log in to access the dashboard', 'danger')
        return render_template('index.html')


@app.route('/admin_logout')
def admin_logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect("/")

@app.route('/admin_dashboard')
def admin_dashboard():
    users = User.query.all()
    books = Book.query.all()
    total_users = User.query.count()
    total_books = Book.query.count()
    return render_template('dashboard.html', total_users=total_users, users=users, total_books=total_books, books=books)

@app.route('/manage_users')
def manage_user():
    user = User.query.all()
    return render_template('manage_user.html', user=user)

@app.route('/update_user/<int:id>', methods=['GET', 'POST'])
def update_user(id):
    if request.method == "POST":
        name = request.form['name']
        password = request.form['password']
        email = request.form['email']
        role = request.form['role']
        user = User.query.filter_by(id=id).first()
        user.name = name
        user.password=password
        user.email = email
        user.role = role
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("manage_user"))
    else:
        user = User.query.filter_by(id=id).first()
        return render_template("update_user.html", user=user)

@app.route('/delete_user/<int:id>', methods=['GET', 'POST'])
def delete_user(id):
    user = User.query.filter_by(id=id).first()
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for("manage_user"))

@app.route('/manage_books')
def manage_books():
    books = Book.query.all()
    return render_template('manage_books.html', books=books)

@app.route('/upload_book', methods=['POST'])
def upload_book():
    if request.method == "POST":
        title = request.form['title']
        writer = request.form['writer']
        category = request.form['category']
        img_file = request.files['img_file']
        pdf_file = request.files['pdf_file']
        added_by = session.get('uname')
        added_at = str(time.strftime("%d-%m-%Y %I:%M:%S %p"))

        existing_book = Book.query.filter_by(title=title).first()
        if existing_book:
            flash("Book already exists", "alert")
        else:
            img_filename = None
            pdf_filename = None

            if img_file:
                img_filename = os.path.join('static/Uploads/Covers', secure_filename(img_file.filename))
                img_file.save(img_filename)
            
            if pdf_file:
                pdf_filename = os.path.join('static/Uploads/Books', pdf_file.filename)
                pdf_file.save(pdf_filename)
    
            new_book = Book(
                title=title,
                writer=writer,
                category=category,
                img_file=img_filename.split("/")[-1],  # Corrected path to use forward slash
                pdf_file=pdf_filename.split("/")[-1],  # Corrected path to use forward slash
                added_by=added_by,
                added_at=added_at
            )
            db.session.add(new_book)
            db.session.commit()

            return redirect(url_for("manage_books"))


@app.route('/update_book/<int:id>', methods=['GET', 'POST'])
def update_book(id):
    if request.method == "POST":
        title = request.form['title']
        writer = request.form['writer']
        category = request.form['category']
        book = Book.query.filter_by(id=id).first()
        book.title = title
        book.writer = writer
        book.category = category
        db.session.add(book)
        db.session.commit()
        return redirect(url_for("manage_books"))
    else:
        book = Book.query.filter_by(id=id).first()
        return render_template("update_book.html", book=book)

@app.route('/delete_book/<int:id>')
def delete_book(id):
    book = Book.query.get_or_404(id)
    try:
        if os.path.exists(f"static/Uploads/Covers/{book.img_file}"):
            os.remove(f"static/Uploads/Covers/{book.img_file}")

        if os.path.exists(f"static/Uploads/Books/{book.pdf_file}"):
            os.remove(f"static/Uploads/Books/{book.pdf_file}")

        db.session.delete(book)
        db.session.commit()

        flash('Book deleted successfully', 'success')
        return redirect(url_for('manage_books'))
    except Exception as e:
        flash('An error occurred while deleting the book', 'danger')
        db.session.rollback()

    return redirect(url_for('manage_books'))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        existing_user = User.query.filter_by(email='nitin16082001@gmail.com').first()        
        if not existing_user:
            new_user = User(name='Nitin Yadav', email='nitin16082001@gmail.com', password='nitu1608', role="Admin", regAt=str(time.strftime("%d-%m-%Y %I:%M:%S %p")))
            db.session.add(new_user)
            db.session.commit()
    
    app.run(debug=False)
