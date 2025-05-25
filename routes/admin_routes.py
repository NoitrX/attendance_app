from flask import Blueprint, render_template, request, redirect, url_for, flash
from controllers.admin_controller import get_all_users, delete_user
from models import User, db, UserAttendance, Schedule

admin = Blueprint('admin', __name__)

@admin.route('/admin')
def index():
    users = get_all_users()
    return render_template('admin/index.html', users=users)

@admin.route('/edit/<int:user_id>', methods=['GET', 'POST'])
def edit_user_route(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        user.first_name = request.form['first_name']
        user.last_name = request.form['last_name']
        user.email = request.form['email']
        user.role = request.form['role']

        db.session.commit()
        return redirect(url_for('admin.index')) 

    return render_template('admin/edit.html', user=user)

@admin.route('/users/<int:user_id>/delete', methods=['POST'])
def delete(user_id):
    user = User.query.get_or_404(user_id)

    UserAttendance.query.filter_by(user_id=user.id).delete()

    if user:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully!', 'success')  # ⬅️ ini bagian penting
    else:
        flash('User not found.', 'error')
        
    return redirect(url_for('admin.index'))


@admin.route('/users/<int:user_id>', methods=['GET'])
def user_detail(user_id):
    user = User.query.get_or_404(user_id)
    attendances = UserAttendance.query.filter_by(user_id=user.id).all()
    schedule_ids = [a.schedule_id for a in attendances]
    schedules = Schedule.query.filter(Schedule.id.in_(schedule_ids)).all()
    return render_template('admin/user_detail.html', user=user, attendances=attendances, schedules=schedules)
