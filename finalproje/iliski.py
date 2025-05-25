from datetime import datetime, timedelta, date
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'gelistirme_anahtari'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    register_date = db.Column(db.DateTime, default=datetime.utcnow)

    loans = db.relationship('Loan', back_populates='uye', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Book(db.Model):
    __tablename__ = 'book'
    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(20), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    publisher = db.Column(db.String(100))
    category = db.Column(db.String(50))
    status = db.Column(db.String(20), default="Rafta")

    loans = db.relationship('Loan', back_populates='kitap')

class Loan(db.Model):
    __tablename__ = 'loan'
    id = db.Column(db.Integer, primary_key=True)
    uye_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    kitap_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    odunc_tarihi = db.Column(db.Date, nullable=False, default=date.today)
    iade_tarihi = db.Column(db.Date, nullable=False)
    iade_edildi = db.Column(db.Boolean, default=False)

    uye = db.relationship('User', back_populates='loans')
    kitap = db.relationship('Book', back_populates='loans')

    @property
    def kalan_gun(self):
        if self.iade_edildi:
            return 0
        today = date.today()
        delta = (self.iade_tarihi - today).days
        return delta if delta > 0 else 0

# ✅ JSON dışa aktarma fonksiyonu
def to_json():
    with app.app_context():
        users = User.query.all()
        data = []

        for user in users:
            user_data = {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'register_date': user.register_date.strftime('%Y-%m-%d %H:%M:%S') if user.register_date else None,
                'loans': []
            }

            for loan in user.loans:
                loan_data = {
                    'id': loan.id,
                    'odunc_tarihi': loan.odunc_tarihi.strftime('%Y-%m-%d') if loan.odunc_tarihi else None,
                    'iade_tarihi': loan.iade_tarihi.strftime('%Y-%m-%d') if loan.iade_tarihi else None,
                    'iade_edildi': loan.iade_edildi,
                    'book': {
                        'id': loan.kitap.id,
                        'isbn': loan.kitap.isbn,
                        'title': loan.kitap.title,
                        'author': loan.kitap.author,
                        'publisher': loan.kitap.publisher,
                        'category': loan.kitap.category,
                        'status': loan.kitap.status
                    }
                }
                user_data['loans'].append(loan_data)

            data.append(user_data)

        with open('kullanici_odunc_kitaplar.json', 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

        print("✅ JSON dosyası oluşturuldu: kullanici_odunc_kitaplar.json")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Veritabanı tablolarını oluşturur
        to_json()
