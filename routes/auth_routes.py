from flask import Blueprint, render_template, request, redirect, url_for
from controllers.auth_controller import register_user, login_user
from models import User, db

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
            
        )
    return render_template('register.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        return login_user(
            request.form['email'],
            request.form['password'],
            request.files['photo'],
            
        )
    return render_template('login.html')