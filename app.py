from flask import Flask, render_template

app = Flask(__name__)

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