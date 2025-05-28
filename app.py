from flask import Flask, request, render_template, flash, redirect, url_for
from flask_migrate import Migrate
from models import db
import face_recognition
from config.config import Config
from routes import init_routes
from models.user import User
from models.schedule import Schedule
from models.user_biometric import UserBiometric
from models.user_attendance import UserAttendance
from datetime import datetime
import cv2
import numpy as np
from PIL import Image
import io
import base64
import os
import bcrypt
import logging
import pytz

# Configure logging
logging.basicConfig(
    filename='face_recognition.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['CAPTURE_FOLDER'], exist_ok=True)

    def base64_to_image(base64_string):
        try:
            img_data = base64.b64decode(base64_string.split(',')[1])
            img = Image.open(io.BytesIO(img_data))
            return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        except Exception as e:
            flash(f'Error processing image: {str(e)}', 'error')
            logger.error(f'Image processing error: {str(e)}')
            return None

    db.init_app(app)
    with app.app_context():
        db.create_all()

    Migrate(app, db)
    init_routes(app)

    @app.route('/')
    def index():
        return render_template('register.html', uploaded_images=[])

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            base64_string = request.form.get('photo')

            logger.info(f'Login attempt for email: {email}')

            if not all([email, password, base64_string]):
                flash('Email, password, and photo are required.', 'error')
                logger.warning('Missing required fields in login attempt')
                return redirect(url_for('login'))

            # Authenticate user
            user = User.query.filter_by(email=email).first()
            if not user or not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
                flash('Invalid email or password.', 'error')
                logger.warning(f'Invalid credentials for email: {email}')
                return redirect(url_for('login'))

            # Process photo
            img = base64_to_image(base64_string)
            if img is None:
                logger.error('Failed to process login photo')
                return redirect(url_for('login'))

            # Generate face encoding
            new_encodings = face_recognition.face_encodings(img)
            if len(new_encodings) != 1:
                flash('Exactly one face must be detected in the photo.', 'error')
                logger.warning('Invalid number of faces detected in login photo')
                return redirect(url_for('login'))

            # Retrieve stored biometric encodings
            biometrics = UserBiometric.query.filter_by(user_id=user.id).all()
            if not biometrics:
                flash('No biometric data found for this user.', 'error')
                logger.warning(f'No biometric data for user ID: {user.id}')
                return redirect(url_for('login'))

            stored_encodings = [np.frombuffer(b.biometric, dtype=np.float64) for b in biometrics]
            new_encoding = new_encodings[0]

            # Compare faces
            results = face_recognition.compare_faces(stored_encodings, new_encoding, tolerance=0.6)
            if not any(results):
                flash('Face verification failed.', 'error')
                logger.warning(f'Face verification failed for user ID: {user.id}')
                return redirect(url_for('login'))

            # Record attendance
            try:
                jakarta_tz = pytz.timezone('Asia/Jakarta')
                attendance_time = datetime.now(jakarta_tz).strftime('%Y-%m-%d %H:%M:%S')
                attendance = UserAttendance(
                    user_id=user.id,
                    attendance_time=attendance_time,
                    status='Present',
                    schedule_id=1
                )
                db.session.add(attendance)
                db.session.commit()
                flash('Attendance recorded successfully!', 'success')
                logger.info(f'Attendance recorded for user ID: {user.id} at {attendance_time}')
            except Exception as e:
                db.session.rollback()
                flash(f'Error recording attendance: {str(e)}', 'error')
                logger.error(f'Error recording attendance for user ID: {user.id}: {str(e)}')
            return redirect(url_for('index'))

        return render_template('login.html')

    @app.route('/register', methods=['POST'])
    def register():
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = 'user'

        logger.info(f'Registration attempt for email: {email}')

        if not all([first_name, last_name, email, password]):
            flash('All fields must be filled.', 'error')
            logger.warning('Missing required fields in registration')
            return redirect(url_for('index'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            logger.warning(f'Email already registered: {email}')
            return redirect(url_for('index'))

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        images = []
        image_paths = []
        temp_files = []

        # Process uploaded files
        uploaded_files = request.files.getlist('photo')
        for file in uploaded_files:
            if file and file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)
                if img is None:
                    flash(f'Invalid image file: {file.filename}', 'error')
                    logger.warning(f'Invalid image file: {file.filename}')
                    return redirect(url_for('index'))
                encodings = face_recognition.face_encodings(img)
                if len(encodings) != 1:
                    flash(f'Exactly one face must be detected in {file.filename}.', 'error')
                    logger.warning(f'No single face detected in uploaded file: {file.filename}')
                    return redirect(url_for('index'))
                images.append(img)
                filename = f"upload_{len(images)}_{file.filename}"
                filepath = os.path.join(app.config['CAPTURE_FOLDER'], filename)
                cv2.imwrite(filepath, img)
                image_paths.append(filename)
                temp_files.append(filepath)

        # Process webcam photos
        for i in range(10):
            photo_key = f'webcam_photos_{i}'
            if photo_key in request.form:
                base64_string = request.form[photo_key]
                img = base64_to_image(base64_string)
                if img is None:
                    logger.error('Failed to process webcam photo')
                    return redirect(url_for('index'))
                encodings = face_recognition.face_encodings(img)
                if len(encodings) != 1:
                    flash(f'Exactly one face must be detected in webcam photo {i + 1}.', 'error')
                    logger.warning(f'No single face detected in webcam photo {i + 1}')
                    return redirect(url_for('index'))
                images.append(img)
                filename = f"capture_{len(images)}_{int(np.random.rand() * 1000000)}.jpg"
                filepath = os.path.join(app.config['CAPTURE_FOLDER'], filename)
                cv2.imwrite(filepath, img)
                image_paths.append(filename)
                temp_files.append(filepath)

        if not (1 <= len(images) <= 10):
            for filepath in temp_files:
                if os.path.exists(filepath):
                    os.remove(filepath)
            flash(f'Provide 1–10 photos with detectable faces. Provided: {len(images)}.', 'error')
            logger.warning(f'Invalid photo count: {len(images)}')
            return redirect(url_for('index'))

        new_user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=hashed_password,
            role=role
        )
        db.session.add(new_user)
        db.session.flush()

        for i, img in enumerate(images):
            encoding = face_recognition.face_encodings(img)[0]
            biometric = UserBiometric(
                user_id=new_user.id,
                biometric=np.array(encoding).tobytes(),
                image=image_paths[i]
            )
            db.session.add(biometric)

        try:
            db.session.commit()
            flash('Registration successful!', 'success')
            logger.info(f'Registration successful for user ID: {new_user.id}')
        except Exception as e:
            db.session.rollback()
            for filepath in temp_files:
                if os.path.exists(filepath):
                    os.remove(filepath)
            flash(f'Error saving to database: {str(e)}', 'error')
            logger.error(f'Registration error for email {email}: {str(e)}')
        return redirect(url_for('index'))

    app.base64_to_image = base64_to_image

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
