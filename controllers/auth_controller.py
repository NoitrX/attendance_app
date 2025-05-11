from flask import flash, redirect, url_for
from models import user, db, biometric
import face_recognition
import cv2
import numpy as np
import os
import bcrypt

def register_user(name, email, password, identifier, files, app):
    if len(files) < 5:
        flash('Minimal 5 foto diperlukan!')
        return redirect(url_for('auth.register'))

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user = User(name=name, email=email, password=hashed_password, identifier=identifier)
    db.session.add(user)
    db.session.commit()

    for file in files:
        if file:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{user.id}_{file.filename}")
            file.save(file_path)
            encoding = face_recognition.load_image_file(file_path)
            encodings = face_recognition.face_encodings(encoding)
            if encodings:
                biometric = Biometric(user_id=user.id, face_encoding=encodings[0].tobytes())
                db.session.add(biometric)
    db.session.commit()
    flash('Registrasi berhasil! Silakan login.')
    return redirect(url_for('auth.login'))

def login_user(email, password, photo, app):
    user = User.query.filter_by(email=email).first()
    if user and bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_{user.id}.jpg")
        photo.save(file_path)
        login_encoding = face_recognition.load_image_file(file_path)
        encodings = face_recognition.face_encodings(login_encoding)
        if not encodings:
            flash('Wajah tidak terdeteksi.')
            return redirect(url_for('auth.login'))

        biometrics = Biometric.query.filter_by(user_id=user.id).all()
        for biometric in biometrics:
            stored_encoding = np.frombuffer(biometric.face_encoding, dtype=np.float64)
            match = face_recognition.compare_faces([stored_encoding], encodings[0])[0]
            if match:
                from datetime import datetime
                current_time = datetime.now().time()
                schedule = Schedule.query.first()
                if schedule:
                    status = 'Tepat Waktu' if current_time <= schedule.end_time else 'Telat'
                    attendance = Attendance(user_id=user.id, status=status)
                    db.session.add(attendance)
                    db.session.commit()
                    flash(f'Absensi berhasil! Status: {status}')
                else:
                    flash('Tidak ada jadwal absensi saat ini.')
                return redirect(url_for('auth.login'))
        flash('Pengenalan wajah gagal.')
    else:
        flash('Kredensial salah.')
    return redirect(url_for('auth.login'))