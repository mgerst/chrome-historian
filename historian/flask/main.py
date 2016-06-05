from flask import Flask, render_template

from historian.history import History

app = Flask(__name__)


@app.route('/')
def index():
    hist = History(app.config['HISTORIES'])
    hist.parse()

    return render_template('index.html', hist=hist)
