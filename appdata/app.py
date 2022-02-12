import os
from flask import Flask, redirect, render_template, url_for, request, g, make_response, flash, send_from_directory, send_file, Response, abort
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)

UPLOAD_FOLDER = 'static/upload/'

app.wsgi_app = ProxyFix(app.wsgi_app)
app.config['SECRET_KEY'] = "fdndflkadlkadkcmnvfldksfkllmcdlkamclkmckdmadlkamkl"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/', methods=['GET', 'POST'])
def index():


    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")