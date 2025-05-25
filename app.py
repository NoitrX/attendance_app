from flask import Flask, request, render_template, flash, redirect, url_for
from flask_migrate import Migrate
from models import db
from config.config import Config
from routes import init_routes
from models.user import User
from models.user_biometric import UserBiometric
import cv2
import numpy as np
from PIL import Image
import io
import base64
import os
import bcrypt
import json

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    if 'CAPTURE_FOLDER' not in app.config:
        app.config['CAPTURE_FOLDER'] = os.path.join(os.path.dirname(__file__), '..', 'Captures')
    os.makedirs(app.config['CAPTURE_FOLDER'], exist_ok=True)

    db.init_app(app)
    Migrate(app, db)

    init_routes(app)

    @app.route('/')
    def index():
        return render_template('register.html', uploaded_images=[])

    @app.route('/register', methods=['POST'])
    def register():
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = 'user'

        if not all([first_name, last_name, email, password]):
            flash('All fields are required.', 'error')
            return redirect(url_for('index'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return redirect(url_for('index'))

        # bikin passwordnya jadi hash
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        images = []
        image_paths = []

        # nge-handle foto yang di-upload
        uploaded_files = request.files.getlist('photo')
        for file in uploaded_files:
            if file and file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_GRAYSCALE)
                if img is None:
                    flash('Invalid image file.', 'error')
                    return redirect(url_for('index'))
                images.append(img)
                filename = f"upload_{len(images)}_{file.filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                cv2.imwrite(filepath, img)
                image_paths.append(filename)

        # handle foto dari webcam 
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

        # harus pas 5 foto, gak boleh kurang/lebih
        if len(images) != 5:
            flash(f'Exactly 5 photos are required. Provided: {len(images)}.', 'error')
            return redirect(url_for('index'))

        try:
            # proses eigenface-nya 
            mean_face, eigenfaces, weights = compute_eigenfaces(images)
            biometric_data = json.dumps(weights.tolist())
        except Exception as e:
            flash(f'Error processing images: {str(e)}', 'error')
            return redirect(url_for('index'))

        # simpen data user dulu
        new_user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=hashed_password,
            role=role
        )
        db.session.add(new_user)
        db.session.flush()  # ambil id-nya biar bisa dipake ke tabel lain

        for i, image_path in enumerate(image_paths):
            biometric = UserBiometric(
                user_id=new_user.id,
                biometric=biometric_data if i == 0 else None,
                image=image_path
            )
            db.session.add(biometric)

        try:
            db.session.commit()
            flash('Registration successful!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving to database: {str(e)}', 'error')
            return redirect(url_for('index'))

    def base64_to_image(base64_string):
        img_data = base64.b64decode(base64_string.split(',')[1])
        img = Image.open(io.BytesIO(img_data))
        return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)

    def preprocess_image(image, size=(100, 100)):
        image = cv2.resize(image, size)
        image = image.astype(np.float32) / 255.0
        return image.flatten()

    def compute_eigenfaces(images):
        data_matrix = np.array([preprocess_image(img) for img in images])
        mean_face = np.mean(data_matrix, axis=0)
        centered_data = data_matrix - mean_face
        U, S, Vt = np.linalg.svd(centered_data, full_matrices=False)
        k = min(10, Vt.shape[0])
        eigenfaces = Vt[:k]
        weights = np.dot(centered_data, eigenfaces.T)
        return mean_face, eigenfaces, weights

    app.base64_to_image = base64_to_image
    app.preprocess_image = preprocess_image
    app.compute_eigenfaces = compute_eigenfaces

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
