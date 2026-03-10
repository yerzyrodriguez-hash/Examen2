from flask_login import UserMixin
from .extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(db.Model, UserMixin):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default="lectores") 
    
    perfil = db.relationship('Lector', backref='cuenta', uselist=False, lazy=True)
    
    def set_password(self, password):
        self.password = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password, password)

class Lector(db.Model):
    __tablename__ = 'lectores'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    C_I = db.Column(db.String(120), unique=True, nullable=False)
    celular = db.Column(db.String(20), nullable=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), unique=True, nullable=False)
    
class Categoria(db.Model):
    __tablename__ = 'categorias'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    libros = db.relationship('Libro', backref='categoria', lazy=True)
    def __repr__(self):
        return f'<Categoria {self.nombre}>'


class Libro(db.Model):
    __tablename__ = 'libros'
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    autor = db.Column(db.String(100), nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'), nullable=False)
    
    @property
    def disponible(self):
        prestamos_pendientes = sum(1 for p in self.prestamos if p.estado == 'Pendiente')
        return self.stock > prestamos_pendientes

    def __repr__(self):
        return f'<Libro {self.titulo}>'

class Prestamo(db.Model):
    __tablename__ = 'prestamos'
    
    id = db.Column(db.Integer, primary_key=True)
    fecha_prestamo = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    fecha_devolucion = db.Column(db.DateTime, nullable=True)
    estado = db.Column(db.String(50), nullable=False, default='Pendiente')  # "Pendiente" o "Devuelto"
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    libro_id = db.Column(db.Integer, db.ForeignKey('libros.id'), nullable=False)

    usuario = db.relationship('User', backref='prestamos', lazy=True)
    libro = db.relationship('Libro', backref='prestamos', lazy=True)
    
    def __repr__(self):
        return f'<Prestamo {self.id} - {self.estado}>'
    
    def devolver(self):
        self.estado = 'Devuelto'
        self.fecha_devolucion = datetime.now()