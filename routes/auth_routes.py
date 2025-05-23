from controllers.auth_controller import register_user, login_user, login_admin
from flask import Blueprint, render_template, request, redirect, url_for,flash
from models.schedule import Schedule
from models import db

auth = Blueprint('auth', __name__)

@auth.route('/', methods=['GET', 'POST'])
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


@auth.route('/login-admin', methods=['GET', 'POST'])
def login_admin_route():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        return login_admin(email,password)
    return render_template('login_admin.html')
@auth.route('/admin/schedules')
def schedule_index():
    schedules = Schedule.query.all()
    return render_template('Admin/index.html', schedules=schedules)


@auth.route('/admin/create', methods=['GET', 'POST'])
def schedule_create():
    if request.method == 'POST':
        try:
            title = request.form['title']
            start = request.form['start_time']
            end = request.form['end_time']
            status = request.form['status']
            
            schedule = Schedule(
                schedule_title=title,
                start_time=start,
                end_time=end,
                status=status
            )
            db.session.add(schedule)
            db.session.commit()
            return redirect(url_for('auth.schedule_index', created=1))
        except Exception as e:
            print(f"Error: {e}")
            return redirect(url_for('auth.schedule_index', error=1))
    
    # Return untuk method GET
    return render_template('Admin/create.html')


@auth.route('/admin/edit/<int:id>', methods=['GET', 'POST'])
def schedule_edit(id):
    schedule = Schedule.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
           
            required_fields = ['title', 'start_time', 'end_time']
            if not all(k in request.form for k in required_fields):
                return redirect(url_for('auth.schedule_edit', id=id, error=2))
            
            
            start_time = request.form['start_time']
            end_time = request.form['end_time']
            
            # Update data
            schedule.schedule_title = request.form['title']
            schedule.start_time = start_time  
            schedule.end_time = end_time      
            schedule.status = request.form.get('status', 'Aktif')
            
            db.session.commit()
            return redirect(url_for('auth.schedule_index', updated=1))
            
        except Exception as e:
            db.session.rollback()
            print(f"Edit error: {e}")
            return redirect(url_for('auth.schedule_edit', id=id, error=1))
    
    return render_template('Admin/edit.html', schedule=schedule)
   


@auth.route('/schedule/delete/<int:id>', methods=['POST'])
def schedule_delete(id):
    schedule = Schedule.query.get_or_404(id)
    db.session.delete(schedule)
    db.session.commit()
    return redirect(url_for('auth.schedule_index', deleted=1))

@auth.route('/schedule/toggle/<int:id>', methods=['POST'])
def schedule_toggle(id):
    schedule = Schedule.query.get_or_404(id)
    schedule.status = 'Tidak Aktif' if schedule.status == 'Aktif' else 'Aktif'
    db.session.commit()
    return redirect(url_for('auth.schedule_index'))


