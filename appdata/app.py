import os
import re
from flask import Flask, redirect, render_template, session, url_for, request, g, make_response, flash, send_from_directory, send_file, Response, abort
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix

import uuid
import pickle
from datetime import datetime
from PIL import Image
import qrcode

from db_routine import dbx
from errors import Errors

import pandas as pd
import numpy as np

UPLOAD_FOLDER = 'static/upload/'
ALLOWED_EXTENSIONS_IMAGE = {'eps', 'png'}
ALLOWED_EXTENSIONS_DATA = {'xlsx', 'csv'}

app = Flask(__name__)

app.wsgi_app = ProxyFix(app.wsgi_app)
app.config['SECRET_KEY'] = "fdndflkadlkadkcmnvfldksfkllmcdlkamclkmckdmadlkamkl"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = dbx()
E = Errors()

def set_session_id():
    return str(uuid.uuid4())

def allowed_file_image(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_IMAGE

def allowed_file_data(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_DATA


@app.route('/', methods=['GET', 'POST'])
def index():

    if request.method == "POST":
        session_id = set_session_id()
        os.mkdir(os.path.join(os.path.join(app.config['UPLOAD_FOLDER'], session_id)))
        cid = db.get_costumer_id()
        cid = cid
        d = dict(request.form)
        for c in cid:
            print(c, d['costumer_id'])
            if str(c[0]) == str(d['costumer_id']):
                return redirect(url_for('error', e=100))

        d['session_id'] = session_id

        if d['opt1'] == "on":
            d['opt1'] = datetime.now()
        if d['opt2'] == "on":
            d['opt2'] = datetime.now()
        if d['opt3'] == "on":
            d['opt3'] = datetime.now()

        file_data = request.files['file_data']
        file_logo = request.files['file_logo']
        if file_data.filename == '' or file_logo.filename == '':
            flash('No selected file')
            #return redirect(request.url)
        if file_data and allowed_file_data(file_data.filename):
            filename_data = secure_filename(file_data.filename)
            file_data.save(os.path.join(app.config['UPLOAD_FOLDER'], session_id, filename_data))
            d['file_data'] = filename_data

        if file_logo and allowed_file_image(file_logo.filename):
            filename_logo = secure_filename(file_logo.filename)
            file_logo.save(os.path.join(app.config['UPLOAD_FOLDER'], session_id, filename_logo))
            d['file_logo'] = filename_logo

        p3 = f'{session_id}.cust'
        pickle.dump(d, open(os.path.join(app.config['UPLOAD_FOLDER'], session_id, p3), 'wb'))
        db.set_costumer_data(d)

        return redirect(url_for('checking', sid=session_id))

    return render_template('index.html')

@app.route('/checking', methods=['GET', 'POST'])
def checking():
    session_id = request.args.get('sid')
    d = db.get_costumer_data(session_id)
    if d:
        p = d[0]
    else:
        return False

    logo_path = os.path.join(app.config['UPLOAD_FOLDER'], p[1], p[12])
    data_path = os.path.join(app.config['UPLOAD_FOLDER'], p[1], p[11])


    return redirect(url_for('summary', sid=session_id))

@app.route('/summary', methods=['GET', 'POST'])
def summary():
    session_id = request.args.get('sid')
    d = db.get_costumer_data(session_id)
    if d:
        p = d[0]
    else:
        return False
    
    logo_path = os.path.join(app.config['UPLOAD_FOLDER'], p[1], p[12])
    data_path = os.path.join(app.config['UPLOAD_FOLDER'], p[1], p[11])
    df = pd.read_csv(data_path, header=None, sep=';')
    len_df = len(df)
    print(df)
    if request.method == 'POST':
        return redirect(url_for('done'))


    #qr_code = qrcode.make(p[9])
    #qr_code.make_image(fill_color="black", back_color="yellow")
    #qr_filename = os.path.join(app.config['UPLOAD_FOLDER'], p[1], f'qr_{p[1]}.png')
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=15,
        border=1,
    )
    qr.add_data(p[9])
    qr.make(fit=True)
    qr_filename = os.path.join(app.config['UPLOAD_FOLDER'], p[1], f'qr_{p[1]}.png')
    qr_code = qr.make_image(fill_color="black", back_color="transparent")
    qr_code.save(qr_filename)

    return render_template('summary.html', df=df, logo=logo_path, p=p, len_df=len_df,qr=qr_filename)

@app.route('/done', methods=['GET', 'POST'])
def done():

    return render_template('done.html')

@app.route('/error', methods=['GET', 'POST'])
def error():
    errorcode = request.args.get('e')
    err = E.get_error(errorid=errorcode)

    return render_template('error.html', err=err[0])

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")