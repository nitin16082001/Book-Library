from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from werkzeug.utils import secure_filename
import time
import os

# Flask app setup
app = Flask(__name__, static_url_path='/static')
app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///book_registration.db'
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static/Uploads')

# Ensure required directories exist
for folder in ['Books', 'Covers']:
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], folder), exist_ok=True)

# DB setup
db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    regAt = db.Column(db.String(100), nullable=False)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    writer = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    img_file = db.Column(db.String(100), nullable=False)
    pdf_file = db.Column(db.String(100), nullable=False)
    added_by = db.Column(db.String(100), nullable=False)
    added_at = db.Column(db.String(100), nullable=False)
    likes = db.Column(db.Integer, default=0, nullable=False)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form['username']
    password = request.form['passWord']
    user = User.query.filter_by(email=email).first()
    
    if user and user.password == password:
        session['logged_in'] = True
        session['uname'] = user.name
        return redirect(url_for('admin' if user.role == 'Admin' else 'home'))

    flash('Invalid credentials', 'danger')
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/home')
def home():
    if 'logged_in' not in session:
        flash('Please log in to access the dashboard', 'danger')
        return redirect(url_for('index'))

    featured_books = Book.query.order_by(desc(Book.id)).limit(4).all()
    latest_books = Book.query.order_by(desc(Book.id)).offset(4).limit(8).all()
    return render_template('Home.html', user=session['uname'], featured_books_data=featured_books, latest_books=latest_books)

@app.route('/books')
def list_books():
    page = request.args.get('page', 1, type=int)
    per_page = 12
    pagination = Book.query.paginate(page=page, per_page=per_page)
    return render_template('books.html', books=pagination.items, current_page=page, total_pages=pagination.pages, user=session.get('uname'))

@app.route('/about')
def about():
    return render_template('about.html', user=session.get('uname'))

@app.route('/register', methods=['POST'])
def register():
    name = request.form['uname']
    email = request.form['email']
    password = request.form['password']

    if User.query.filter_by(email=email).first():
        return render_template('index.html', message='Email already registered', redirect_url=url_for('index'))

    new_user = User(name=name, email=email, password=password, role="Reader", regAt=current_time())
    db.session.add(new_user)
    db.session.commit()
    return render_template('index.html', message='Registration successful', redirect_url=url_for('index'))

@app.route('/admin')
def admin():
    if 'logged_in' not in session:
        flash('Please log in to access the dashboard', 'danger')
        return redirect(url_for('index'))

    return redirect(url_for('admin_dashboard'))

@app.route('/admin_dashboard')
def admin_dashboard():
    users = User.query.all()
    books = Book.query.all()
    return render_template('dashboard.html', total_users=len(users), users=users, total_books=len(books), books=books)

@app.route('/manage_users')
def manage_user():
    return render_template('manage_user.html', user=User.query.all())

@app.route('/register_user', methods=['POST'])
def register_user():
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']

    if User.query.filter_by(email=email).first():
        flash('User already exists', 'warning')
    else:
        new_user = User(name=name, email=email, password=password, role="Reader", regAt=current_time())
        db.session.add(new_user)
        db.session.commit()
    return redirect(url_for('manage_user'))

@app.route('/update_user/<int:id>', methods=['GET', 'POST'])
def update_user(id):
    user = User.query.get_or_404(id)
    if request.method == 'POST':
        user.name = request.form['name']
        user.password = request.form['password']
        user.email = request.form['email']
        user.role = request.form['role']
        db.session.commit()
        return redirect(url_for('manage_user'))
    return render_template('update_user.html', user=user)

@app.route('/delete_user/<int:id>', methods=['POST'])
def delete_user(id):
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('manage_user'))

@app.route('/manage_books')
def manage_books():
    return render_template('manage_books.html', books=Book.query.all())

@app.route('/upload_book', methods=['POST'])
def upload_book():
    title = request.form['title']
    writer = request.form['writer']
    category = request.form['category']
    img_file = request.files['img_file']
    pdf_file = request.files['pdf_file']

    if Book.query.filter_by(title=title).first():
        flash('Book already exists', 'warning')
        return redirect(url_for('manage_books'))

    img_filename = save_file(img_file, 'Covers')
    pdf_filename = save_file(pdf_file, 'Books')

    new_book = Book(title=title, writer=writer, category=category, img_file=img_filename, pdf_file=pdf_filename, added_by=session.get('uname'), added_at=current_time())
    db.session.add(new_book)
    db.session.commit()

    return redirect(url_for('manage_books'))

@app.route('/update_book/<int:id>', methods=['GET', 'POST'])
def update_book(id):
    book = Book.query.get_or_404(id)
    if request.method == 'POST':
        book.title = request.form['title']
        book.writer = request.form['writer']
        book.category = request.form['category']
        db.session.commit()
        return redirect(url_for('manage_books'))
    return render_template('update_book.html', book=book)

@app.route('/delete_book/<int:id>', methods=['POST'])
def delete_book(id):
    book = Book.query.get_or_404(id)
    try:
        for folder, file in [('Covers', book.img_file), ('Books', book.pdf_file)]:
            path = os.path.join(app.config['UPLOAD_FOLDER'], folder, file)
            if os.path.exists(path):
                os.remove(path)
        db.session.delete(book)
        db.session.commit()
        flash('Book deleted successfully', 'success')
    except Exception:
        db.session.rollback()
        flash('An error occurred while deleting the book', 'danger')
    return redirect(url_for('manage_books'))

# Helper functions
def save_file(file, subfolder):
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], subfolder, filename)
        file.save(file_path)
        return filename
    return ''

def current_time():
    return time.strftime("%d-%m-%Y %I:%M:%S %p")

# Initialize DB and admin user
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        admin_email = 'nitin16082001@gmail.com'
        if not User.query.filter_by(email=admin_email).first():
            db.session.add(User(name='Nitin Yadav', email=admin_email, password='********', role='Admin', regAt=current_time()))
            db.session.commit()

    app.run(debug=False)
