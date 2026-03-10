from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from functools import wraps
from .models import Libro, Categoria
from .extensions import db

inventario_bp = Blueprint('inventario', __name__)

def solo_admin(f):
    @wraps(f)
    def decorado(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Acceso restringido: solo el administrador puede realizar esta acción.', 'danger')
            return redirect(url_for('inventario.catalogo'))
        return f(*args, **kwargs)
    return decorado

# libros

@inventario_bp.route('/catalogo')
@login_required
def catalogo():
    categorias = Categoria.query.order_by(Categoria.nombre).all()
    cat_filtro = request.args.get('categoria_id', '')

    if cat_filtro:
        libros = Libro.query.filter_by(categoria_id=cat_filtro).order_by(Libro.titulo).all()
    else:
        libros = Libro.query.order_by(Libro.titulo).all()

    return render_template(
        'catalogo.html',
        libros=libros,
        categorias=categorias,
        cat_filtro=cat_filtro
    )

@inventario_bp.route('/libros/nuevo', methods=['GET', 'POST'])
@login_required
@solo_admin
def nuevo_libro():
    categorias = Categoria.query.order_by(Categoria.nombre).all()

    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        autor = request.form.get('autor', '').strip()
        stock_raw = request.form.get('stock', '0')
        categoria_id = request.form.get('categoria_id')

        if not titulo:
            flash('El título no puede estar en blanco.', 'danger')
            return render_template('libro_form.html', categorias=categorias, accion='Registrar')

        try:
            stock = int(stock_raw)
        except ValueError:
            flash('El stock debe ser un número entero.', 'danger')
            return render_template('libro_form.html', categorias=categorias, accion='Registrar')

        if stock < 0:
            flash('El stock no puede ser negativo.', 'danger')
            return render_template('libro_form.html', categorias=categorias, accion='Registrar')

        if not categoria_id:
            flash('Debes seleccionar una categoría.', 'danger')
            return render_template('libro_form.html', categorias=categorias, accion='Registrar')

        nuevo = Libro(titulo=titulo, autor=autor, stock=stock, categoria_id=int(categoria_id))
        db.session.add(nuevo)
        db.session.commit()
        flash(f'Libro "{titulo}" registrado exitosamente.', 'success')
        return redirect(url_for('inventario.catalogo'))

    return render_template('libro_form.html', categorias=categorias, accion='Registrar')

@inventario_bp.route('/libros/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@solo_admin
def editar_libro(id):
    libro = Libro.query.get_or_404(id)
    categorias = Categoria.query.order_by(Categoria.nombre).all()

    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        autor = request.form.get('autor', '').strip()
        stock_raw = request.form.get('stock', '0')
        categoria_id = request.form.get('categoria_id')

        if not titulo:
            flash('El título no puede estar en blanco.', 'danger')
            return render_template('libro_form.html', libro=libro, categorias=categorias, accion='Actualizar')

        try:
            stock = int(stock_raw)
        except ValueError:
            flash('El stock debe ser un número entero.', 'danger')
            return render_template('libro_form.html', libro=libro, categorias=categorias, accion='Actualizar')

        if stock < 0:
            flash('El stock no puede ser negativo.', 'danger')
            return render_template('libro_form.html', libro=libro, categorias=categorias, accion='Actualizar')

        if not categoria_id:
            flash('Debes seleccionar una categoría.', 'danger')
            return render_template('libro_form.html', libro=libro, categorias=categorias, accion='Actualizar')
        libro.titulo = titulo
        libro.autor = autor
        libro.stock = stock
        libro.categoria_id = int(categoria_id)
        db.session.commit()
        flash(f'Libro "{titulo}" actualizado correctamente.', 'success')
        return redirect(url_for('inventario.catalogo'))

    return render_template('libro_form.html', libro=libro, categorias=categorias, accion='Actualizar')


@inventario_bp.route('/libros/eliminar/<int:id>')
@login_required
@solo_admin
def eliminar_libro(id):
    libro = Libro.query.get_or_404(id)
    db.session.delete(libro)
    db.session.commit()
    flash(f'Libro "{libro.titulo}" eliminado del sistema.', 'success')
    return redirect(url_for('inventario.catalogo'))

#categortia

@inventario_bp.route('/categorias')
@login_required
@solo_admin
def lista_categorias():
    categorias = Categoria.query.order_by(Categoria.nombre).all()
    return render_template('lista_categorias.html', categorias=categorias)


@inventario_bp.route('/categorias/nueva', methods=['GET', 'POST'])
@login_required
@solo_admin
def nueva_categoria():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()

        if not nombre:
            flash('El nombre de la categoría no puede estar en blanco.', 'danger')
            return render_template('categoria_form.html', accion='Crear')

        if Categoria.query.filter_by(nombre=nombre).first():
            flash(f'La categoría "{nombre}" ya existe.', 'danger')
            return render_template('categoria_form.html', accion='Crear')

        nueva = Categoria(nombre=nombre)
        db.session.add(nueva)
        db.session.commit()
        flash(f'Categoría "{nombre}" creada exitosamente.', 'success')
        return redirect(url_for('inventario.lista_categorias'))

    return render_template('categoria_form.html', accion='Crear')

@inventario_bp.route('/categorias/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@solo_admin
def editar_categoria(id):
    categoria = Categoria.query.get_or_404(id)

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()

        if not nombre:
            flash('El nombre no puede estar en blanco.', 'danger')
            return render_template('categoria_form.html', categoria=categoria, accion='Actualizar')

        existente = Categoria.query.filter_by(nombre=nombre).first()
        if existente and existente.id != id:
            flash(f'Ya existe una categoría con el nombre "{nombre}".', 'danger')
            return render_template('categoria_form.html', categoria=categoria, accion='Actualizar')

        categoria.nombre = nombre
        db.session.commit()
        flash(f'Categoría actualizada a "{nombre}".', 'success')
        return redirect(url_for('inventario.lista_categorias'))

    return render_template('categoria_form.html', categoria=categoria, accion='Actualizar')

@inventario_bp.route('/categorias/eliminar/<int:id>')
@login_required
@solo_admin
def eliminar_categoria(id):
    categoria = Categoria.query.get_or_404(id)

    if categoria.libros:
        flash(
            f'No puedes eliminar "{categoria.nombre}" porque tiene '
            f'{len(categoria.libros)} libro(s) asociado(s). '
            'Reasigna o elimina esos libros primero.',
            'danger'
        )
        return redirect(url_for('inventario.lista_categorias'))

    db.session.delete(categoria)
    db.session.commit()
    flash(f'Categoría "{categoria.nombre}" eliminada.', 'success')
    return redirect(url_for('inventario.lista_categorias'))