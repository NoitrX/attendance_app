from flask import flash, redirect, url_for
from models import user, db, user_biometric , UserAttendance, schedule, User


def get_all_users():
    from models.user import User
    return User.query.all()

def update_user(user_id, new_data):
    user_to_update = User.query.get(user_id)
    if not user_to_update:
        flash('User tidak ditemukan.')
        return redirect(url_for('admin.index'))

    # Misal new_data ini dictionary: {'first_name': ..., 'last_name': ..., dst}
    user_to_update.first_name = new_data.get('first_name', user_to_update.first_name)
    user_to_update.last_name = new_data.get('last_name', user_to_update.last_name)
    user_to_update.email = new_data.get('email', user_to_update.email)
    user_to_update.role = new_data.get('role', user_to_update.role)

    db.session.commit()
    flash('User berhasil diupdate.')
    return redirect(url_for('admin.index'))

def delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash('User berhasil dihapus.')
    else:
        flash('User tidak ditemukan.')
    return redirect(url_for('admin.index'))
