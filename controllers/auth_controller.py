from flask import flash, redirect, url_for
from models import user, db, user_biometric , UserAttendance, schedule


def register_user(name, email, password, identifier, files, app):
    return redirect(url_for('auth.login'))

def login_user(email, password, photo, app):
    return redirect(url_for('auth.login'))