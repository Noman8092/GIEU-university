from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file,send_from_directory,abort
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from datetime import datetime
from datetime import date
import sqlite3
import os
import markdown
#-------------------------------------------------------Create a Flask App , I said Flask-----------------------------------> 
app = Flask(__name__)
app.secret_key = "your_secret_key"  # Replace with a strong secr





#-----------------------------------------------------Student Result Data connect with flask--------------------------------->

def fetch_result(roll, name):
    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE roll=? AND name=?", (roll, name))
    row = cursor.fetchone()
    conn.close()
    return row
 

# ------------------ -----------------------------------Configuration ----------------------------------------------------------->
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ---------------------------------------------Create upload folder if not exists------------------------------------------------>
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ------------------------------------------------------------- Helpers --------------------------------------------------------->
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#----------------------------------------------Database Connection Helper--------------------------------------------------------->



def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def add_missing_student_columns():
    """Ensure all required columns exist in the 'students' table."""
    required_columns = {
        'phone': "TEXT",
        'address': "TEXT",
        'roll': "TEXT",
        'last_login': "TEXT",
        'discussion_status': "TEXT DEFAULT 'pending'"
    }

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get existing column names
        cursor.execute("PRAGMA table_info(students)")
        existing_columns = {column[1] for column in cursor.fetchall()}

        # Add missing columns
        for column, column_type in required_columns.items():
            if column not in existing_columns:
                cursor.execute(f"ALTER TABLE students ADD COLUMN {column} {column_type}")
                print(f"✅ Added column: {column}")

        conn.commit()

# ✅ Call this at the top of your app (once)
add_missing_student_columns()







app.config['UPLOAD_FOLDER'] = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# ----------------------- Initialize blog table ----------------------
# init_db.py
import sqlite3

def init_db():
    conn = sqlite3.connect('database.db')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS blogs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            content TEXT NOT NULL,
            image TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()
print("✅ Blog table created successfully.")



# ----------------------- Blog Routes -------------------------------
@app.route('/blogs', endpoint='blog_page')
def blogs():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    blogs = conn.execute('SELECT * FROM blogs ORDER BY date DESC').fetchall()
    conn.close()
    return render_template('blogs.html', blogs=blogs)

@app.route('/admin/blogs', methods=['GET', 'POST'])
def admin_blogs():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    blogs = conn.execute('SELECT * FROM blogs ORDER BY date DESC').fetchall()
    conn.close()
    return render_template('admin_blogs.html', blogs=blogs)

@app.route('/add_blog', methods=['POST'])
def add_blog():
    title = request.form['title']
    author = request.form['author']
    content = request.form['content']
    image = request.files['image']

    filename = None
    if image and image.filename != '':
        filename = secure_filename(image.filename)
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    conn = sqlite3.connect('database.db')
    conn.execute('INSERT INTO blogs (title, author, content, image) VALUES (?, ?, ?, ?)',
                 (title, author, content, filename))
    conn.commit()
    conn.close()

    flash("Blog added successfully!", "success")
    return redirect('/admin/blogs')

@app.route('/delete_blog/<int:id>')
def delete_blog(id):
    conn = sqlite3.connect('database.db')
    conn.execute('DELETE FROM blogs WHERE id=?', (id,))
    conn.commit()
    conn.close()
    flash("Blog deleted successfully!", "success")
    return redirect('/admin/blogs')




@app.route('/blog/<int:blog_id>')
def blog_detail(blog_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM blogs WHERE id = ?", (blog_id,))
    blog = c.fetchone()
    conn.close()

    # Convert blog[3] (content) from Markdown to HTML
    blog_content_html = markdown.markdown(blog[3])

    return render_template("blog_detail.html", blog=blog, blog_content=blog_content_html)


# ------------------------------------------------- Home route Public Routes ------------------------------------------>
@app.route('/')
def home():
    return render_template("index1.html")
#----------------------------------------------------Courses Route ----------------------------------------------------->
@app.route('/courses')
def view_courses():
    conn = get_db_connection()
    courses = conn.execute("SELECT * FROM courses").fetchall()
    conn.close()
    return render_template('courses.html', courses=courses)

#-------------------------------------------Don't show courses before  user login---------------------------------------------
@app.route('/course/<int:id>')
def course_detail(id):
    if not session.get('user_id'):
        flash("Please login to view full course details.", "warning")
        return redirect(url_for('login'))
    conn = get_db_connection()
    course = conn.execute("SELECT * FROM courses WHERE id = ?", (id,)).fetchone()
    conn.close()
    return render_template("course_detail.html", course=course)

#--------------------------------------------------------Faculty Route------------------------------------------------------>

@app.route('/faculty')
def faculty():
    return render_template("faculty.html")

@app.route('/gallery')
def gallery():
    return render_template("gallery.html")

# ------------------ ---------------------------------Student Registration & Login----------- ------------------------------------>

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        phone = request.form['phone']
        address = request.form['address']

        try:
            conn = get_db_connection()
            conn.execute("""
                INSERT INTO students (name, email, password, phone, address)
                VALUES (?, ?, ?, ?, ?)
            """, (name, email, password, phone, address))
            conn.commit()
            conn.close()
            flash("Registration successful!", "success")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Email already registered.", "danger")
            return redirect(url_for('register'))
    return render_template("register.html")


#------------------------------------------------------Student Login Route------------------------------------------> 
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password_input = request.form['password']

        conn = get_db_connection()
        student = conn.execute("SELECT * FROM students WHERE email = ?", (email,)).fetchone()

        if student and check_password_hash(student['password'], password_input):
            session['user_id'] = student['id']
            session['user_name'] = student['name']

            login_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            conn.execute("UPDATE students SET last_login = ? WHERE id = ?", (login_time, student['id']))
            conn.commit()
            conn.close()

            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials", "danger")
            conn.close()
            return redirect(url_for('login'))

    return render_template("login.html")

#-------------------------------------------------Student Dashboard Route---------------------------------------------->
@app.route('/dashboard')
def dashboard():
    if not session.get('user_id'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    courses = conn.execute("SELECT * FROM courses").fetchall()
    conn.close()

    return render_template("dashboard.html", name=session['user_name'], courses=courses)

#-----------------------------------------------------Certificate Route --------------------------------------->
@app.route('/generate_certificate')
def generate_certificate():
    if 'user_name' not in session:
        return redirect(url_for('login'))

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width / 2, height - 100, "Certificate of Completion")

    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2, height - 160, f"Awarded to: {session['user_name']}")

    c.setFont("Helvetica", 14)
    c.drawCentredString(width / 2, height - 200, "For successfully completing the course")

    date = datetime.now().strftime("%d %B %Y")
    c.setFont("Helvetica-Oblique", 12)
    c.drawCentredString(width / 2, height - 240, f"Issued on: {date}")

    c.showPage()
    c.save()

    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="certificate.pdf", mimetype='application/pdf')

#------------------------------------------------------Student Log Out Route------------------------------------->
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for('login'))


#---------------------------------------------To Veiw Result Of Students -------------------------------------------->

@app.route('/result', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        roll = request.form['roll']
        name = request.form['name']
        result = fetch_result(roll, name)
        if result:
            total = sum(result[3:])  # Sum all 8 subject marks
            student = {
                'roll': result[0],
                'name': result[1],
                'position': result[2],
                'subjects': result[3:],
                'total': total
            }
            return render_template('result.html', student=student)
        else:
            return "<h2>❌ نتیجہ نہیں ملا۔ براہ کرم نام اور رول نمبر درست درج کریں۔</h2><a href='/'>واپس جائیں</a>"
    return render_template('index.html')
 
    
# ------------------ -------------------------------Admin Login  Routes ---------------------------------------->
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == "admin" and password == "admin123":
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid admin credentials", "danger")
    return render_template("admin/admin_login.html")

#-----------------------------------------------------Admin Dashboard Route ------------------------------------>
@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    courses = conn.execute("SELECT * FROM courses").fetchall()
    conn.close()
    return render_template("admin/admin_dashboard.html", courses=courses)

#-------------------------------------------------------Admin Add Courses Route --------------------------------------->
@app.route('/admin/add_course', methods=['GET', 'POST'])
def add_course():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        pdf_file = request.files['pdf']
        pdf_filename = ""

        if pdf_file and allowed_file(pdf_file.filename):
            filename = secure_filename(pdf_file.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            pdf_file.save(path)
            pdf_filename = f"/{path}"

        conn = get_db_connection()
        conn.execute("INSERT INTO courses (title, description, pdf) VALUES (?, ?, ?)", 
                     (title, description, pdf_filename))
        conn.commit()
        conn.close()
        flash("Course added successfully!", "success")
        return redirect(url_for('admin_dashboard'))

    return render_template("admin/add_course.html")

#----------------------------------------------------Admin Add, Delete Courses Route --------------------------->
@app.route('/admin/delete_course/<int:id>')
def delete_course(id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    conn.execute("DELETE FROM courses WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash("Course deleted!", "warning")
    return redirect(url_for('admin_dashboard'))
#--------------------------------------------------Admin Show Loged In Student Data Route ----------------------------->
@app.route('/admin/students')
def view_students():
    search = request.args.get('search', '')
    date = request.args.get('date', '')
    discussion = request.args.get('discussion', '')

    conn = get_db_connection()
    query = "SELECT * FROM students WHERE 1=1"
    params = []

    if search:
        query += " AND (name LIKE ? OR email LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    if date:
        query += " AND DATE(last_login) = ?"
        params.append(date)

    if discussion:
        query += " AND discussion_status = ?"
        params.append(discussion)

    students = conn.execute(query, params).fetchall()
    conn.close()

    return render_template('admin/admin_students.html', students=students)


#------------------------------------------------Admin See Student Discussed or Not Route ---------------------------->
@app.route('/admin/mark_discussed/<int:id>')
def mark_discussed(id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    conn.execute("UPDATE students SET discussion_status = 'discussed' WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash("Marked as discussed", "success")
    return redirect(url_for('view_students'))

#--------------------------------------------Admin Delete Logod In Student Data------------------------------>
@app.route('/admin/delete_student/<int:id>')
def delete_student(id):
    # Check if admin is logged in
    if not session.get('admin'):
        flash("Admin login required.", "danger")
        return redirect(url_for('admin_login'))

    # Prevent admin from deleting their own account
    if session.get('user_id') == id:
        flash("❌ You cannot delete your own account.", "danger")
        return redirect(url_for('view_students'))

    # Proceed to delete student from database
    conn = get_db_connection()
    conn.execute("DELETE FROM students WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    flash("✅ Student deleted successfully!", "success")
    return redirect(url_for('view_students'))



#-------------------------------------------------Books Upload --------------------------------------------->
UPLOAD_FOLDER_IMAGES = 'static/images'
UPLOAD_FOLDER_BOOKS = 'static/books'
os.makedirs(UPLOAD_FOLDER_IMAGES, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_BOOKS, exist_ok=True)
#-----------------------------------------------Books Uploading Database-------------------------------------->
# Database setup
def init_db():
    with sqlite3.connect('books.db') as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            image TEXT NOT NULL,
            file TEXT NOT NULL
        )''')
init_db()

#--------------------------------------------------------------Books Route ----------------------------------------->
@app.route('/books')
def books():
    with sqlite3.connect('books.db') as conn:
        books = conn.execute("SELECT * FROM books").fetchall()
    return render_template('books.html', books=books)

#-------------------------------------------------------Admin Add Books Route----------------------------------------->
@app.route('/admin/books', methods=['GET', 'POST'])
def admin_books():
    if request.method == 'POST':
        title = request.form['title']
        image = request.files['image']
        file = request.files['file']

        if title and image and file:
            image_filename = secure_filename(image.filename)
            book_filename = secure_filename(file.filename)
            image.save(os.path.join(UPLOAD_FOLDER_IMAGES, image_filename))
            file.save(os.path.join(UPLOAD_FOLDER_BOOKS, book_filename))

            with sqlite3.connect('books.db') as conn:
                conn.execute("INSERT INTO books (title, image, file) VALUES (?, ?, ?)", 
                             (title, image_filename, book_filename))
            flash("Book added successfully", "success")
            return redirect(url_for('admin_books'))

    with sqlite3.connect('books.db') as conn:
        books = conn.execute("SELECT * FROM books").fetchall()
    return render_template('admin_books.html', books=books)

#-----------------------------------------------------------Admin Delete Books Ruote -------------------------------->
@app.route('/delete-book/<int:id>')
def delete_book(id):
    with sqlite3.connect('books.db') as conn:
        book = conn.execute("SELECT image, file FROM books WHERE id=?", (id,)).fetchone()
        if book:
            os.remove(os.path.join(UPLOAD_FOLDER_IMAGES, book[0]))
            os.remove(os.path.join(UPLOAD_FOLDER_BOOKS, book[1]))
            conn.execute("DELETE FROM books WHERE id=?", (id,))
            flash("Book deleted", "danger")
    return redirect(url_for('admin_books'))

#-----------------------------------------------------Students Read Books Route ------------------------------------------->
@app.route('/read-book/<filename>')
def read_book(filename):
    return send_from_directory(UPLOAD_FOLDER_BOOKS, filename)


#---------------------------------------------------- Admin Edit Book Route using sqlite3 ----------------------------------->


#-----------------------------------------------------Admin Logout Route ------------------------------------------------->
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    flash("Logged out from admin panel", "info")
    return redirect(url_for('admin_login'))

# ------------------ -------------------------------------Run ------------------------------------------>
if __name__ == '__main__':
    app.run(debug=True)
