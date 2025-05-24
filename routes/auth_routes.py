from flask import Blueprint, render_template, request, redirect, url_for, flash
from controllers.auth_controller import register_user, login_user

auth = Blueprint('auth', __name__, template_folder='templates')

_app = None

def init_auth(app):
    global _app
    _app = app

@auth.route('/register', methods=['GET', 'POST'])
def register():
    # kalo user baru buka halaman, tampilin form register aja
    if request.method == 'GET':
        return render_template('register.html', uploaded_images=[])

    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    email = request.form.get('email')
    password = request.form.get('password')
    role = 'user'  # default role, bisa diganti kalo ada admin dll

    # validasi input, jangan sampe ada yang kosong
    if not all([first_name, last_name, email, password]):
        flash('All fields are required.', 'error')
        return redirect(url_for('auth.register'))

    # langsung oper ke controller buat handle proses registrasi
    return register_user(
        first_name, 
        last_name, 
        email, 
        password, 
        role, 
        request.files.getlist('photo'), 
        request, 
        _app
    )

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not all([email, password]):
            flash('Email and password are required.', 'error')
            return redirect(url_for('auth.login'))

        return login_user(email, password, request.files.get('photo'), _app)

    return render_template('login.html')
