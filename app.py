from flask import Flask, request, render_template, flash, redirect, url_for
from flask_migrate import Migrate
from models import db
from config.config import Config
from routes import init_routes
from models.user import User
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
import json
import logging

# Configure logging
logging.basicConfig(
    filename='face_recognition.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables for eigenface model and tracking
mean_face = None
eigenfaces = None
attempt_count = 0
success_count = 0

def create_app():
    global mean_face, eigenfaces, attempt_count, success_count

    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['CAPTURE_FOLDER'], exist_ok=True)

    def preprocess_image(image, size=(100, 100)):
        if image is None:
            raise ValueError("Image cannot be read.")
        image = cv2.resize(image, size)
        image = image.astype(np.float32) / 255.0
        return image.flatten()

    def base64_to_image(base64_string):
        img_data = base64.b64decode(base64_string.split(',')[1])
        img = Image.open(io.BytesIO(img_data))
        return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)

    def compute_eigenfaces(images):
        data_matrix = np.array([preprocess_image(img) for img in images])
        mean_face_local = np.mean(data_matrix, axis=0)
        centered_data = data_matrix - mean_face_local
        U, S, Vt = np.linalg.svd(centered_data, full_matrices=False)
        k = min(10, Vt.shape[0])
        eigenfaces_local = Vt[:k]
        weights = np.dot(centered_data, eigenfaces_local.T)
        return mean_face_local, eigenfaces_local, weights

    def build_eigenface_model():
        global mean_face, eigenfaces
        all_biometrics = UserBiometric.query.all()
        all_images = []
        image_mapping = []
        for biometric in all_biometrics:
            if biometric.image:
                img_path = os.path.join(app.config['CAPTURE_FOLDER'], biometric.image)
                img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
                if img is not None:
                    all_images.append(preprocess_image(img))
                    image_mapping.append(biometric.id)
        if not all_images:
            mean_face, eigenfaces = None, None
            return
        data_matrix = np.array(all_images)
        mean_face = np.mean(data_matrix, axis=0)
        centered_data = data_matrix - mean_face
        U, S, Vt = np.linalg.svd(centered_data, full_matrices=False)
        k = min(10, Vt.shape[0])
        eigenfaces = Vt[:k]
        weights = np.dot(centered_data, eigenfaces.T)
        for idx, biometric_id in enumerate(image_mapping):
            biometric = UserBiometric.query.get(biometric_id)
            biometric.biometric = json.dumps(weights[idx].tolist())
        db.session.commit()

    def recognize_face(img, mean_face, eigenfaces):
        if mean_face is None or eigenfaces is None:
            raise ValueError("Eigenface model not initialized.")
        processed_img = preprocess_image(img)
        weights = np.dot(processed_img - mean_face, eigenfaces.T)
        return weights

    def verify_biometric(new_weights, user_id, threshold=10.0):
        min_distance = float('inf')
        biometrics = UserBiometric.query.filter_by(user_id=user_id).filter(UserBiometric.biometric.isnot(None)).all()
        if not biometrics:
            return False
        for biometric in biometrics:
            stored_weights = np.array(json.loads(biometric.biometric))
            distance = np.linalg.norm(new_weights - stored_weights)
            if distance < min_distance:
                min_distance = distance
        return min_distance < threshold

    db.init_app(app)
    with app.app_context():
        db.create_all()
        build_eigenface_model()

    Migrate(app, db)
    init_routes(app)

    @app.route('/')
    def index():
        return render_template('register.html', uploaded_images=[])

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        global attempt_count, success_count
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            photo_base64 = request.form.get('photo')

            if not all([email, password, photo_base64]):
                flash('All fields must be filled, including photo.', 'error')
                return redirect(url_for('login'))

            try:
                # Step 1: Verify user via email and password
                user = User.query.filter_by(email=email).first()
                attempt_count += 1
                log_message = f"Recognition attempt #{attempt_count}: Email={email}"

                if not user:
                    log_message += " - Failed: User not found"
                    logger.info(log_message)
                    flash('Email not found.', 'error')
                    return redirect(url_for('login'))

                if not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
                    log_message += " - Failed: Incorrect password"
                    logger.info(log_message)
                    flash('Incorrect password.', 'error')
                    return redirect(url_for('login'))

                # Step 2: Verify biometric
                img = base64_to_image(photo_base64)
                weights = recognize_face(img, mean_face, eigenfaces)
                biometric_match = verify_biometric(weights, user.id)

                if biometric_match:
                    # Save attendance image
                    filename = f"attendance_{user.id}_{int(np.random.rand() * 1000000)}.jpg"
                    filepath = os.path.join(app.config['CAPTURE_FOLDER'], filename)
                    cv2.imwrite(filepath, img)
                    attendance = UserAttendance(
                        user_id=user.id,
                        attendance_time=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                        status='present',
                        schedule_id=1
                    )
                    db.session.add(attendance)
                    db.session.commit()
                    success_count += 1
                    log_message += f" - Success for user_id {user.id}, Image saved as {filename}"
                    logger.info(log_message)
                    flash('Attendance recorded successfully!', 'success')
                    return redirect(url_for('index'))
                else:
                    log_message += " - Failed: Biometric verification failed"
                    logger.info(log_message)
                    flash('Biometric verification failed.', 'error')

                # Log success rate every 10 attempts
                if attempt_count % 10 == 0 and attempt_count > 0:
                    success_rate = (success_count / attempt_count) * 100
                    logger.info(f"Success rate after {attempt_count} attempts: {success_rate:.2f}%")
            except Exception as e:
                log_message = f"Recognition attempt #{attempt_count} failed with error: {str(e)}"
                logger.error(log_message)
                flash(f'Error processing image: {str(e)}', 'error')

        return render_template('login.html')

    @app.route('/register', methods=['POST'])
    def register():
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = 'user'

        if not all([first_name, last_name, email, password]):
            flash('All fields must be filled.', 'error')
            return redirect(url_for('index'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return redirect(url_for('index'))

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        images = []
        image_paths = []

        uploaded_files = request.files.getlist('photo')
        for file in uploaded_files:
            if file and file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_GRAYSCALE)
                if img is None:
                    flash('Invalid image file.', 'error')
                    return redirect(url_for('index'))
                images.append(img)
                filename = f"upload_{len(images)}_{file.filename}"
                filepath = os.path.join(app.config['CAPTURE_FOLDER'], filename)
                cv2.imwrite(filepath, img)
                image_paths.append(filename)

        for i in range(5):
            photo_key = f'webcam_photos_{i}'
            if photo_key in request.form:
                base64_string = request.form[photo_key]
                img = base64_to_image(base64_string)
                images.append(img)
                filename = f"capture_{len(images)}_{int(np.random.rand() * 1000000)}.jpg"
                filepath = os.path.join(app.config['CAPTURE_FOLDER'], filename)
                cv2.imwrite(filepath, img)
                image_paths.append(filename)

        if len(images) != 5:
            flash(f'Exactly 5 photos are required. Provided: {len(images)}.', 'error')
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

        for image_path in image_paths:
            biometric = UserBiometric(
                user_id=new_user.id,
                biometric=None,
                image=image_path
            )
            db.session.add(biometric)

        try:
            db.session.commit()
            build_eigenface_model()
            flash('Registration successful!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving to database: {str(e)}', 'error')
            return redirect(url_for('index'))

    app.base64_to_image = base64_to_image
    app.preprocess_image = preprocess_image
    app.compute_eigenfaces = compute_eigenfaces

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)