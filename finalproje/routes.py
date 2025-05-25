from datetime import datetime, timedelta, date
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'gelistirme_anahtari'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

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
    # uye_id sütunu ve User ilişkisi kaldırıldı
    kitap_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    odunc_tarihi = db.Column(db.Date, nullable=False, default=date.today)
    iade_tarihi = db.Column(db.Date, nullable=False)
    iade_edildi = db.Column(db.Boolean, default=False)

    kitap = db.relationship('Book', back_populates='loans')

    @property
    def kalan_gun(self):
        if self.iade_edildi:
            return 0
        today = date.today()
        delta = (self.iade_tarihi - today).days
        return delta if delta > 0 else 0


def book_to_dict(book):
    return {
        'id': book.id,
        'isbn': book.isbn,
        'title': book.title,
        'author': book.author,
        'publisher': book.publisher,
        'category': book.category,
        'status': book.status
    }

def export_books_to_json():
    with app.app_context():
        books = Book.query.all()
        books_data = [book_to_dict(book) for book in books]

        with open('books.json', 'w', encoding='utf-8') as f:
            json.dump(books_data, f, ensure_ascii=False, indent=4)

        print("Kitaplar JSON dosyasına aktarıldı.")

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)))
