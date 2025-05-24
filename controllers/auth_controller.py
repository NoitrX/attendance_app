from flask import flash, redirect, url_for
from models import db, User, UserBiometric
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
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return redirect(url_for('auth.register'))

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # variabel buat nampung semua foto dan path-nya
        images = []
        image_paths = []

        # proses foto yang di-upload manual
        for file in photos:
            if file and file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_GRAYSCALE)
                if img is None:
                    flash('Invalid image file.', 'error')
                    return redirect(url_for('auth.register'))
                images.append(img)
                filename = f"upload_{len(images)}_{file.filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                cv2.imwrite(filepath, img)
                image_paths.append(filename)

        for i in range(5):  
            photo_key = f'webcam_photos_{i}'
            if photo_key in request.form:
                base64_string = request.form[photo_key]
                img = app.base64_to_image(base64_string)
                images.append(img)
                filename = f"capture_{len(images)}_{int(np.random.rand() * 1000000)}.jpg"
                filepath = os.path.join(app.config['CAPTURE_FOLDER'], filename)
                cv2.imwrite(filepath, img)
                image_paths.append(filename)

        # validasi total foto
        if len(images) != 5:
            flash(f'Exactly 5 photos are required. Provided: {len(images)}.', 'error')
            return redirect(url_for('auth.register'))

        # hitung eigenfaces (buat nentuin biometric signature-nya)
        try:
            mean_face, eigenfaces, weights = app.compute_eigenfaces(images)
            biometric_data = json.dumps(weights.tolist())  
        except Exception as e:
            flash(f'Error processing images: {str(e)}', 'error')
            return redirect(url_for('auth.register'))

        new_user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=hashed_password,
            role=role
        )
        db.session.add(new_user)
        db.session.flush()  

        # simpan biometric + foto ke tabel user biometric
        for i, image_path in enumerate(image_paths):
            biometric = UserBiometric(
                user_id=new_user.id,
                biometric=biometric_data if i == 0 else None,  # simpan biometric-nya di satu record aja
                image=image_path
            )
            db.session.add(biometric)

        try:
            db.session.commit()
            flash('Registration successful!', 'success')
            return redirect(url_for('auth.register'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving to database: {str(e)}', 'error')
            return redirect(url_for('auth.register'))

def login_user(email, password, photo, app):
    with app.app_context():
        user = User.query.filter_by(email=email).first()

        if user and bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            flash('Login successful!', 'success')
            return redirect(url_for('auth.register'))  

        flash('Invalid email or password!', 'error')
        return redirect(url_for('auth.login'))
