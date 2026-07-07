from flask import Flask, render_template, request, redirect, url_for, session, abort
import sqlite3
import os
import re
import uuid
from functools import wraps
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'ufrsta2026'

DATABASE = 'database/ufr_sta.db'
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'ufrsta2026'
UPLOAD_FOLDER = 'static/uploads/enseignants'
GALLERY_UPLOAD_FOLDER = 'static/uploads/galerie'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['GALLERY_UPLOAD_FOLDER'] = GALLERY_UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def slugify(value):
    value = value or ""
    value = re.sub(r"[^\w\s-]", "", value.lower())
    return re.sub(r"[-\s]+", "-", value).strip("-")


def init_db():
    os.makedirs('database', exist_ok=True)
    os.makedirs(GALLERY_UPLOAD_FOLDER, exist_ok=True)
    conn = get_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS actualites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titre TEXT NOT NULL,
        date TEXT NOT NULL,
        description TEXT NOT NULL,
        photo TEXT
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS activites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titre TEXT NOT NULL,
        date TEXT NOT NULL,
        lieu TEXT NOT NULL,
        organisateur TEXT NOT NULL,
        description TEXT NOT NULL
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS formations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        niveau TEXT NOT NULL,
        duree TEXT NOT NULL,
        departement TEXT NOT NULL,
        description TEXT NOT NULL
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS galerie (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titre TEXT NOT NULL,
        album TEXT NOT NULL,
        date TEXT,
        photo TEXT NOT NULL
    )''')
    columns = [row[1] for row in conn.execute('PRAGMA table_info(galerie)').fetchall()]
    if 'date' not in columns:
        conn.execute('ALTER TABLE galerie ADD COLUMN date TEXT')
    conn.execute('''CREATE TABLE IF NOT EXISTS enseignants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        grade TEXT NOT NULL,
        departement TEXT NOT NULL,
        email TEXT NOT NULL,
        domaines TEXT NOT NULL,
        photo TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

def login_requis(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'admin' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ========== ROUTES PUBLIQUES ==========

@app.route('/')
def index():
    conn = get_db()
    actualites = conn.execute('SELECT * FROM actualites ORDER BY id DESC LIMIT 3').fetchall()
    conn.close()
    return render_template('index.html', actualites=actualites)

@app.route('/formations')
def formations():
    return render_template('formations.html')

@app.route('/departements')
def departements():
    return render_template('departements.html')

@app.route('/actualites')
def actualites():
    return render_template('actualites.html')

@app.route('/activites')
def activites():
    return render_template('activites.html')

@app.route('/enseignants')
def enseignants():
    conn = get_db()
    enseignants = conn.execute('SELECT * FROM enseignants ORDER BY id ASC').fetchall()
    conn.close()
    return render_template('enseignants.html', enseignants=enseignants)

@app.route('/galerie')
def galerie():
    conn = get_db()
    photos = conn.execute('SELECT * FROM galerie ORDER BY album, id DESC').fetchall()
    conn.close()

    albums = []
    grouped = {}
    for photo in photos:
        album_name = photo['album']
        if album_name not in grouped:
            grouped[album_name] = {
                'title': album_name,
                'date': photo['date'] or '',
                'cover': photo['photo'],
                'slug': slugify(album_name),
                'photos': []
            }
        grouped[album_name]['photos'].append(photo)

    albums = list(grouped.values())
    albums.sort(key=lambda item: item['date'] or '', reverse=True)
    return render_template('galerie.html', albums=albums)


@app.route('/galerie/<slug>')
def galerie_album(slug):
    conn = get_db()
    photos = conn.execute('SELECT * FROM galerie ORDER BY id DESC').fetchall()
    conn.close()

    album_photos = [photo for photo in photos if slugify(photo['album']) == slug]
    if not album_photos:
        abort(404)

    return render_template(
        'galerie_album.html',
        album_title=album_photos[0]['album'],
        album_date=album_photos[0]['date'] or '',
        photos=album_photos
    )

@app.route('/contact')
def contact():
    return render_template('contact.html')

# ========== LOGIN ==========

@app.route('/admin/login', methods=['GET', 'POST'])
def login():
    erreur = None
    if request.method == 'POST':
        if request.form['username'] == ADMIN_USERNAME and request.form['password'] == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin'))
        else:
            erreur = 'Identifiants incorrects !'
    return render_template('admin/login.html', erreur=erreur)

@app.route('/admin/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('login'))

# ========== ADMIN ==========

@app.route('/admin')
@login_requis
def admin():
    return render_template('admin/index.html')

# --- ACTUALITÉS ---
@app.route('/admin/actualites')
@login_requis
def admin_actualites():
    conn = get_db()
    actualites = conn.execute('SELECT * FROM actualites ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('admin/actualites.html', actualites=actualites)

@app.route('/admin/actualites/ajouter', methods=['POST'])
@login_requis
def ajouter_actualite():
    conn = get_db()
    conn.execute('INSERT INTO actualites (titre, date, description) VALUES (?, ?, ?)',
                 (request.form['titre'], request.form['date'], request.form['description']))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_actualites'))

@app.route('/admin/actualites/supprimer/<int:id>')
@login_requis
def supprimer_actualite(id):
    conn = get_db()
    conn.execute('DELETE FROM actualites WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_actualites'))

# --- ACTIVITÉS ---
@app.route('/admin/activites')
@login_requis
def admin_activites():
    conn = get_db()
    activites = conn.execute('SELECT * FROM activites ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('admin/activites.html', activites=activites)

@app.route('/admin/activites/ajouter', methods=['POST'])
@login_requis
def ajouter_activite():
    conn = get_db()
    conn.execute('INSERT INTO activites (titre, date, lieu, organisateur, description) VALUES (?, ?, ?, ?, ?)',
                 (request.form['titre'], request.form['date'], request.form['lieu'],
                  request.form['organisateur'], request.form['description']))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_activites'))

@app.route('/admin/activites/supprimer/<int:id>')
@login_requis
def supprimer_activite(id):
    conn = get_db()
    conn.execute('DELETE FROM activites WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_activites'))

# --- FORMATIONS ---
@app.route('/admin/formations')
@login_requis
def admin_formations():
    conn = get_db()
    formations = conn.execute('SELECT * FROM formations ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('admin/formations.html', formations=formations)

@app.route('/admin/formations/ajouter', methods=['POST'])
@login_requis
def ajouter_formation():
    conn = get_db()
    conn.execute('INSERT INTO formations (nom, niveau, duree, departement, description) VALUES (?, ?, ?, ?, ?)',
                 (request.form['nom'], request.form['niveau'], request.form['duree'],
                  request.form['departement'], request.form['description']))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_formations'))

@app.route('/admin/formations/supprimer/<int:id>')
@login_requis
def supprimer_formation(id):
    conn = get_db()
    conn.execute('DELETE FROM formations WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_formations'))

# --- ENSEIGNANTS ---
@app.route('/admin/enseignants')
@login_requis
def admin_enseignants():
    conn = get_db()
    enseignants = conn.execute('SELECT * FROM enseignants ORDER BY id ASC').fetchall()
    conn.close()
    return render_template('admin/enseignants.html', enseignants=enseignants)

@app.route('/admin/enseignants/ajouter', methods=['POST'])
@login_requis
def ajouter_enseignant():
    nom = request.form['nom']
    grade = request.form['grade']
    departement = request.form['departement']
    email = request.form['email']
    domaines = request.form['domaines']

    photo = None
    if 'photo' in request.files:
        file = request.files['photo']
        if file and file.filename:
            filename = secure_filename(file.filename)
            if '.' in filename:
                extension = filename.rsplit('.', 1)[1].lower()
                if extension in ALLOWED_EXTENSIONS:
                    photo = f"{nom.lower().replace(' ', '_')}_{len(os.listdir(UPLOAD_FOLDER)) + 1}.{extension}"
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], photo))

    conn = get_db()
    conn.execute('INSERT INTO enseignants (nom, grade, departement, email, domaines, photo) VALUES (?, ?, ?, ?, ?, ?)',
                 (nom, grade, departement, email, domaines, photo))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_enseignants'))

@app.route('/admin/enseignants/supprimer/<int:id>')
@login_requis
def supprimer_enseignant(id):
    conn = get_db()
    enseignant = conn.execute('SELECT * FROM enseignants WHERE id=?', (id,)).fetchone()
    if enseignant and enseignant['photo']:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], enseignant['photo'])
        if os.path.exists(file_path):
            os.remove(file_path)
    conn.execute('DELETE FROM enseignants WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_enseignants'))

# --- GALERIE ---
@app.route('/admin/galerie')
@login_requis
def admin_galerie():
    conn = get_db()
    photos = conn.execute('SELECT * FROM galerie ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('admin/galerie.html', photos=photos)

@app.route('/admin/galerie/ajouter', methods=['POST'])
@login_requis
def ajouter_photo():
    titre = request.form.get('titre', '').strip()
    album = request.form.get('album', '').strip()
    date = request.form.get('date', '').strip()

    files = request.files.getlist('photo')
    if not files:
        return redirect(url_for('admin_galerie'))

    conn = get_db()
    for file in files:
        if not file or not file.filename:
            continue
        filename = secure_filename(file.filename)
        if '.' in filename:
            extension = filename.rsplit('.', 1)[1].lower()
            if extension in ALLOWED_EXTENSIONS:
                unique_name = f"{uuid.uuid4().hex}.{extension}"
                save_path = os.path.join(app.config['GALLERY_UPLOAD_FOLDER'], unique_name)
                file.save(save_path)
                photo_path = f"uploads/galerie/{unique_name}"

                # If title not provided, use filename (without extension)
                row_title = titre if titre else os.path.splitext(filename)[0]

                conn.execute('INSERT INTO galerie (titre, album, date, photo) VALUES (?, ?, ?, ?)',
                             (row_title, album, date, photo_path))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_galerie'))

@app.route('/admin/galerie/supprimer/<int:id>')
@login_requis
def supprimer_photo(id):
    conn = get_db()
    photo = conn.execute('SELECT * FROM galerie WHERE id=?', (id,)).fetchone()
    if photo and photo['photo']:
        file_path = os.path.join('static', photo['photo'])
        if os.path.exists(file_path):
            os.remove(file_path)
    conn.execute('DELETE FROM galerie WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_galerie'))

if __name__ == '__main__':
    app.run(debug=True)