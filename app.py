from flask import Flask, render_template
import sqlite3
import os

app = Flask(__name__)

DATABASE = 'database/ufr_sta.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs('database', exist_ok=True)
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
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('index.html', actualites=[])

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

@app.route('/galerie')
def galerie():
    return render_template('galerie.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

if __name__ == '__main__':
    app.run(debug=True)