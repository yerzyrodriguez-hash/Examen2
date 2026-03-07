from app import create_app
from app.extensions import db
from app.models import User, Lector

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        if not User.query.filter_by(username="admin").first():
            admin_user = User(username="admin", role="admin")
            admin_user.set_password("1234")
            db.session.add(admin_user)
            db.session.flush()
            admin_perfil = Lector(nombre="ADMIN", C_I="0000001", usuario_id=admin_user.id)
            db.session.add(admin_perfil)
            db.session.commit()
            print("✅ Primer administrador creado (Usuario: admin | Contraseña: 1234)")
            
    app.run(debug=True)