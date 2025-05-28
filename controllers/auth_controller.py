from flask import flash, redirect, url_for,jsonify,session
from models import user, db, user_biometric , UserAttendance, schedule, UserBiometric ,User 
from werkzeug.security import check_password_hash
import cv2
import numpy as np
from PIL import Image
import io
import base64
import os
import bcrypt
import json



def register_user(first_name, last_name, email, password, role, photos, request, app):
    with app.app_context():
        # cek email yang udah kepake
            return redirect(url_for('auth.register'))

def login_user(email, password, photo, app):
    return redirect(url_for('auth.login'))



# Login Admin
def login_admin(email, password):
    admin_user = user.User.query.filter_by(email=email).first()
    
  
    if not admin_user:
        return jsonify({
            "success": False,
            "message": "User not found"
        }), 404
    
   
    if admin_user.role != 'admin':
        return jsonify({
            "success": False,
            "message": "User is not an admin"
        }), 403
    
   
    if not check_password_hash(admin_user.password_hash, password):
        return jsonify({
            "success": False,
            "message": "Invalid password"
        }), 401
    
   
    session['user_id'] = admin_user.id
    session['email'] = admin_user.email
    session['role'] = admin_user.role
    
    return jsonify({
        "success": True,
        "email": admin_user.email,
        "message": "Admin login successful"
    }), 200

