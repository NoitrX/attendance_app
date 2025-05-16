from flask import Blueprint, render_template, request, redirect, url_for
from controllers.auth_controller import register_user, login_user

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        return register_user(
            request.form['name'],
            request.form['email'],
            request.form['password'],
            request.form['identifier'],
            request.files.getlist('photos'),
            app
        )
    return render_template('register.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        return login_user(
            request.form['email'],
            request.form['password'],
            request.files['photo'],
            app
        )
    return render_template('login.html')