from datetime import datetime, timedelta, date
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
import os

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


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


with app.app_context():
    db.create_all()




@app.route("/")
def ana_sayfa():
    toplam_kitap = Book.query.count()
    uye_sayisi = User.query.count()
    odunc_kitaplar = Loan.query.filter_by(iade_edildi=False).count()
    # Geciken kitaplar (iade tarihi geçmiş ve iade edilmemiş)
    geciken_kitaplar = Loan.query.filter(
        Loan.iade_tarihi < date.today(),
        Loan.iade_edildi == False
    ).count()

    son_odunc_islemleri = Loan.query.order_by(Loan.odunc_tarihi.desc()).limit(10).all()

    # Her işlem için durum belirle
    for islem in son_odunc_islemleri:
        if islem.iade_edildi:
            islem.durum = 'Normal'
        else:
            kalan = (islem.iade_tarihi - date.today()).days
            if kalan < 0:
                islem.durum = 'Gecikmiş'
            elif kalan <= 3:
                islem.durum = 'Son 3 Gün'
            else:
                islem.durum = 'Normal'

    yeni_kitaplar = Book.query.order_by(Book.id.desc()).limit(6).all()
    yeni_uyeler = User.query.order_by(User.register_date.desc()).limit(6).all()

    return render_template('index.html',
                           toplam_kitap=toplam_kitap,
                           uye_sayisi=uye_sayisi,
                           odunc_kitaplar=odunc_kitaplar,
                           geciken_kitaplar=geciken_kitaplar,
                           son_odunc_islemleri=son_odunc_islemleri,
                           yeni_kitaplar=yeni_kitaplar,
                           yeni_uyeler=yeni_uyeler)

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        if not name or not email or not password:
            flash("Lütfen tüm alanları doldurun.", "danger")
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Bu e-posta zaten kayıtlı!', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(name=name, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Kayıt başarılı! Giriş yapabilirsiniz.', 'success')
        return redirect(url_for('login'))

    return render_template("register.html")


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Giriş başarılı!', 'success')
            return redirect(url_for('ana_sayfa'))
        else:
            flash('Geçersiz e-posta veya şifre.', 'danger')
            return redirect(url_for('login'))

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Çıkış yapıldı.", "info")
    return redirect(url_for('ana_sayfa'))


@app.route("/kitaplar")
@login_required
def kitaplar():
    search = request.args.get('search', '').strip()
    category = request.args.get('category', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 5

    query = Book.query

    if search:
        search_like = f"%{search}%"
        query = query.filter(
            (Book.title.ilike(search_like)) |
            (Book.author.ilike(search_like)) |
            (Book.isbn.ilike(search_like))
        )

    if category:
        query = query.filter_by(category=category)

    pagination = query.order_by(Book.title).paginate(page=page, per_page=per_page, error_out=False)
    books = pagination.items

    return render_template("kitaplar.html", books=books, page=page, pagination=pagination, search=search, category=category)


@app.route("/kitap/ekle", methods=['GET', 'POST'])
@login_required
def kitap_ekle():
    if request.method == 'POST':
        isbn = request.form.get('isbn')
        title = request.form.get('title')
        author = request.form.get('author')
        publisher = request.form.get('publisher')
        category = request.form.get('category')
        status = request.form.get('status', 'Rafta')

        if not isbn or not title or not author:
            flash("ISBN, Kitap Adı ve Yazar zorunludur.", "danger")
            return redirect(url_for('kitap_ekle'))

        if Book.query.filter_by(isbn=isbn).first():
            flash("Bu ISBN zaten kayıtlı.", "danger")
            return redirect(url_for('kitap_ekle'))

        new_book = Book(isbn=isbn, title=title, author=author, publisher=publisher, category=category, status=status)
        db.session.add(new_book)
        db.session.commit()

        flash("Kitap başarıyla eklendi.", "success")
        return redirect(url_for('kitaplar'))

    return render_template("kitap_ekle.html")


@app.route("/kitap/<int:book_id>/duzenle", methods=['GET', 'POST'])
@login_required
def kitap_duzenle(book_id):
    book = Book.query.get_or_404(book_id)

    if request.method == 'POST':
        book.isbn = request.form.get('isbn')
        book.title = request.form.get('title')
        book.author = request.form.get('author')
        book.publisher = request.form.get('publisher')
        book.category = request.form.get('category')
        book.status = request.form.get('status', 'Rafta')

        db.session.commit()
        flash("Kitap güncellendi.", "success")
        return redirect(url_for('kitaplar'))

    return render_template("kitap_duzenle.html", book=book)


@app.route("/kitap/<int:book_id>/sil", methods=['POST'])
@login_required
def kitap_sil(book_id):
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    flash("Kitap silindi.", "success")
    return redirect(url_for('kitaplar'))


@app.route("/odunc", methods=['GET', 'POST'])
@login_required
def odunc():
    if request.method == 'POST':
        uye_id = request.form.get('uye_id')
        kitap_id = request.form.get('kitap_id')

        if not uye_id or not kitap_id:
            flash("Lütfen üye ve kitap seçiniz.", "danger")
            return redirect(url_for('odunc'))

        kitap = Book.query.get(kitap_id)
        if not kitap:
            flash("Kitap bulunamadı.", "danger")
            return redirect(url_for('odunc'))

        if kitap.status == "Ödünçte":
            flash("Seçilen kitap zaten ödünç verilmiş.", "danger")
            return redirect(url_for('odunc'))

        odunc_tarihi = date.today()
        iade_tarihi = odunc_tarihi + timedelta(days=30)

        yeni_odunc = Loan(
            uye_id=uye_id,
            kitap_id=kitap_id,
            odunc_tarihi=odunc_tarihi,
            iade_tarihi=iade_tarihi
        )
        kitap.status = "Ödünçte"

        db.session.add(yeni_odunc)
        db.session.commit()

        flash("Kitap başarıyla ödünç verildi.", "success")
        return redirect(url_for('odunc'))

    uyeler = User.query.all()
    kitaplar = Book.query.filter_by(status="Rafta").all()
    aktif_oduncler = Loan.query.filter_by(iade_edildi=False).all()

    return render_template("odunc.html", uyeler=uyeler, kitaplar=kitaplar, aktif_oduncler=aktif_oduncler)


@app.route("/iade_al/<int:odunc_id>", methods=['POST'])
@login_required
def iade_al(odunc_id):
    odunc = Loan.query.get_or_404(odunc_id)
    if odunc.iade_edildi:
        flash("Bu ödünç zaten iade edilmiş.", "warning")
        return redirect(url_for('odunc'))

    odunc.iade_edildi = True
    kitap = Book.query.get(odunc.kitap_id)
    if kitap:
        kitap.status = "Rafta"
    db.session.commit()

    flash("Kitap iade alındı.", "success")
    return redirect(url_for('odunc'))


@app.route("/uyeler")
@login_required
def uyeler():
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 5

    query = User.query

    if search:
        search_like = f"%{search}%"
        query = query.filter(
            (User.name.ilike(search_like)) |
            (User.email.ilike(search_like)) |
            (User.phone.ilike(search_like)) |
            (User.membership_type.ilike(search_like))
        )

    pagination = query.order_by(User.name).paginate(page=page, per_page=per_page, error_out=False)
    uyeler = pagination.items

    return render_template("uyeler.html", uyeler=uyeler, page=page, pagination=pagination, search=search)



from flask import request, redirect, url_for, flash, render_template
from flask_login import login_required, current_user

# Ayarları kaydetmek ve almak için basit key-value fonksiyonlar (örnek)
settings_store = {}

def set_setting(key, value):
    settings_store[key] = value

def get_setting(key, default=None):
    return settings_store.get(key, default)

@app.route('/ayarlar', methods=['GET', 'POST'])
@login_required
def ayarlar():
    if request.method == 'POST':
        form_type = request.form.get('form_type')

        if form_type == 'general':
            library_name = request.form.get('library_name', '').strip()
            address = request.form.get('address', '').strip()
            max_borrow_days = request.form.get('max_borrow_days', '').strip()
            max_book_count = request.form.get('max_book_count', '').strip()

            if not library_name or not max_borrow_days.isdigit() or not max_book_count.isdigit():
                flash('Lütfen tüm alanları doğru doldurunuz.', 'danger')
            else:
                set_setting('library_name', library_name)
                set_setting('address', address)
                set_setting('max_borrow_days', max_borrow_days)
                set_setting('max_book_count', max_book_count)
                flash('Genel ayarlar kaydedildi.', 'success')

        elif form_type == 'security':
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')

            if not current_password or not new_password or not confirm_password:
                flash('Lütfen tüm şifre alanlarını doldurun.', 'danger')
            elif new_password != confirm_password:
                flash('Yeni şifre ve onay aynı değil.', 'danger')
            else:
                if current_user.check_password(current_password):
                    current_user.set_password(new_password)
                    db.session.commit()  # Eğer db varsa aktif et
                    flash('Şifre başarıyla değiştirildi.', 'success')
                else:
                    flash('Mevcut şifre yanlış.', 'danger')

        elif form_type == 'notifications':
            notif_late_books = 'notif_late_books' in request.form
            notif_new_user = 'notif_new_user' in request.form
            notif_system_updates = 'notif_system_updates' in request.form
            notif_email = request.form.get('notif_email', '').strip()

            set_setting('notif_late_books', str(int(notif_late_books)))
            set_setting('notif_new_user', str(int(notif_new_user)))
            set_setting('notif_system_updates', str(int(notif_system_updates)))
            set_setting('notif_email', notif_email)

            flash('Bildirim tercihleri kaydedildi.', 'success')

        return redirect(url_for('ayarlar'))

    # GET isteğinde ayarları al ve template'e gönder
    general_settings = {
        'library_name': get_setting('library_name', 'Kütüphane VS'),
        'address': get_setting('address', '123 Kütüphane Caddesi, Ankara'),
        'max_borrow_days': get_setting('max_borrow_days', '30'),
        'max_book_count': get_setting('max_book_count', '5'),
    }

    notifications_settings = {
        'notif_late_books': bool(int(get_setting('notif_late_books', '1'))),
        'notif_new_user': bool(int(get_setting('notif_new_user', '1'))),
        'notif_system_updates': bool(int(get_setting('notif_system_updates', '0'))),
        'notif_email': get_setting('notif_email', 'admin@kutuphanevs.com'),
    }

    return render_template(
        'ayarlar.html',
        general_settings=general_settings,
        notifications_settings=notifications_settings
    )



@app.route("/uye/ekle", methods=["GET", "POST"])
@login_required
def uye_ekle():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        if not name or not email or not password:
            flash("Lütfen tüm alanları doldurun.", "danger")
            return redirect(url_for("uye_ekle"))

        if User.query.filter_by(email=email).first():
            flash("Bu e-posta zaten kayıtlı.", "danger")
            return redirect(url_for("uye_ekle"))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(name=name, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash("Yeni üye eklendi.", "success")
        return redirect(url_for("uyeler"))

    return render_template("uye_ekle.html")

@app.route("/uye/<int:uye_id>/duzenle", methods=['GET', 'POST'])
@login_required
def uye_duzenle(uye_id):
    uye = User.query.get_or_404(uye_id)

    if request.method == "POST":
        uye.name = request.form.get("name")
        uye.email = request.form.get("email")
        password = request.form.get("password")

        if password:
            uye.password = generate_password_hash(password, method='pbkdf2:sha256')

        db.session.commit()
        flash("Üye bilgileri güncellendi.", "success")
        return redirect(url_for("uyeler"))

    return render_template("uye_duzenle.html", uye=uye)

@app.route("/uye/<int:uye_id>/sil", methods=["POST"])
@login_required
def uye_sil(uye_id):
    uye = User.query.get_or_404(uye_id)
    db.session.delete(uye)
    db.session.commit()
    flash("Üye silindi.", "success")
    return redirect(url_for("uyeler"))

from flask import render_template, send_file
from datetime import date
from sqlalchemy import func, desc
import pandas as pd
from io import BytesIO
from fpdf import FPDF

@app.route("/raporlar")
@login_required
def raporlar():
    current_date = date.today()

    # En çok ödünç alan üyeler
    en_cok_odunc_alanlar = db.session.query(User.name, db.func.count(Loan.id))\
        .join(Loan).group_by(User.id).order_by(db.func.count(Loan.id).desc()).limit(5).all()

    # Geciken kitaplar
    geciken_kitaplar = Loan.query.filter(
        Loan.iade_tarihi < current_date,
        Loan.iade_edildi == False
    ).all()

    # Popüler kitaplar
    populer_kitaplar = db.session.query(Book.title, db.func.count(Loan.id))\
        .join(Loan).group_by(Book.id).order_by(db.func.count(Loan.id).desc()).limit(5).all()

    return render_template("raporlar.html",
                           en_cok_odunc_alanlar=en_cok_odunc_alanlar,
                           geciken_kitaplar=geciken_kitaplar,
                           populer_kitaplar=populer_kitaplar,
                           current_date=current_date)




@app.route('/profil', methods=['GET', 'POST'])
@login_required
def profil():
    user = current_user  # flask-login ile giriş yapan kullanıcı
    if request.method == 'POST':
        user.name = request.form['name']
        user.email = request.form['email']
        # Diğer güncellemeler burada
        db.session.commit()


    return render_template('profil.html', user=user)


#if __name__ == "__main__":
    #app.run(debug=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)))
