from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required
from .models import User, Lector
from .extensions import db, login_manager

auth_bp = Blueprint('auth', __name__)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@auth_bp.route('/registro', methods=['GET', 'POST'])
@login_required
def registro():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        rol = request.form.get('rol')
        nombre = request.form.get('nombre')
        c_i = request.form.get('c_i')
        celular = request.form.get('celular')
        if User.query.filter_by(username=username).first():
            flash('El nombre de usuario ya está en uso.', 'danger')
            return redirect(url_for('auth.registro'))
        if Lector.query.filter_by(C_I=c_i).first():
            flash('Esta Cédula de Identidad ya está registrada.', 'danger')
            return redirect(url_for('auth.registro'))
        nuevo_usuario = User(username=username, role=rol)
        nuevo_usuario.set_password(password)
        db.session.add(nuevo_usuario)
        db.session.flush() 
        nuevo_lector = Lector(nombre=nombre, C_I=c_i, celular=celular, usuario_id=nuevo_usuario.id)
        db.session.add(nuevo_lector)
        db.session.commit()
        flash(f'Lector "{nombre}" registrado exitosamente en el sistema.', 'success')
        return redirect(url_for('auth.lista_usuarios'))
    return render_template('registro.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        usuario = User.query.filter_by(username=username).first()
        if usuario and usuario.check_password(password):
            login_user(usuario)
            return redirect(url_for('auth.lista_usuarios'))
        else:
            flash('Usuario o contraseña incorrectos.', 'danger')
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.lista_usuarios'))

@auth_bp.route('/usuarios')
@login_required
def lista_usuarios():
    busqueda = request.args.get('busqueda', '')
    if busqueda:
        usuarios = User.query.join(Lector).filter(
            (Lector.C_I.like(f'%{busqueda}%')) |
            (Lector.nombre.like(f'%{busqueda}%')) |
            (User.username.like(f'%{busqueda}%'))
        ).all()
    else:
        usuarios = User.query.all()
    return render_template('lista_usuarios.html', usuarios=usuarios, busqueda=busqueda)
