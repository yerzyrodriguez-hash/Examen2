from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required
from .models import User, Lector, Libro, Categoria, Prestamo
from .extensions import db, login_manager
from datetime import datetime

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

@auth_bp.route('/eliminar/<int:id>')
@login_required
def eliminar_usuario(id):
    usuario = User.query.get_or_404(id)
    if usuario.username == 'admin':
        flash('Por seguridad, no puedes eliminar al administrador principal.', 'danger')
        return redirect(url_for('auth.lista_usuarios'))
    db.session.delete(usuario.perfil)
    db.session.delete(usuario)
    db.session.commit()
    flash('El usuario y su perfil han sido eliminados del sistema.', 'success')
    return redirect(url_for('auth.lista_usuarios'))

# ============= RUTAS PARA PRÉSTAMOS =============
@auth_bp.route('/prestamos')
@login_required
def lista_prestamos():
    estado = request.args.get('estado')
    
    if estado:
        prestamos = Prestamo.query.filter_by(estado=estado).all()
    else:
        prestamos = Prestamo.query.all()
    
    return render_template('prestamos.html', prestamos=prestamos)

@auth_bp.route('/prestamo/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_prestamo():
    if request.method == 'POST':
        usuario_id = request.form.get('usuario_id')
        libro_id = request.form.get('libro_id')

        if not usuario_id or not libro_id:
            flash('Debe seleccionar un usuario y un libro', 'danger')
            return redirect(url_for('auth.nuevo_prestamo'))

        libro = Libro.query.get(libro_id)

        prestamos_pendientes = Prestamo.query.filter_by(
            libro_id=libro_id, 
            estado='Pendiente'
        ).count()
        
        if prestamos_pendientes >= libro.stock:
            flash(f'No hay ejemplares disponibles de "{libro.titulo}"', 'danger')
            return redirect(url_for('auth.nuevo_prestamo'))
        
        prestamo = Prestamo(
            usuario_id=usuario_id,
            libro_id=libro_id
        )
        
        try:
            db.session.add(prestamo)
            db.session.commit()
            flash(f'Préstamo registrado exitosamente', 'success')
            return redirect(url_for('auth.lista_prestamos'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar préstamo: {str(e)}', 'danger')
            return redirect(url_for('auth.nuevo_prestamo'))
    
    usuarios = User.query.all()
    libros = Libro.query.all()
    return render_template('nuevo_prestamo.html', usuarios=usuarios, libros=libros)

@auth_bp.route('/prestamo/devolver/<int:id>')
@login_required
def devolver_prestamo(id):
    prestamo = Prestamo.query.get_or_404(id)
    
    if prestamo.estado == 'Pendiente':
        prestamo.estado = 'Devuelto'
        prestamo.fecha_devolucion = datetime.now()
        
        try:
            db.session.commit()
            flash(f'Libro "{prestamo.libro.titulo}" devuelto exitosamente', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al procesar devolución: {str(e)}', 'danger')
    else:
        flash('Este préstamo ya fue devuelto anteriormente', 'warning')
    
    return redirect(url_for('auth.lista_prestamos'))