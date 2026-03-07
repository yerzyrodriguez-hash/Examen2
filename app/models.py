from flask_login import UserMixin
from .extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

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