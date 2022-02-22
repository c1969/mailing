import os
import re
from flask import Flask, redirect, render_template, session, url_for, request, g, make_response, flash, send_from_directory, send_file, Response, abort
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_consent import Consent

import uuid
import pickle
from datetime import datetime
from PIL import Image
import qrcode

from db_routine import dbx
from errors import Errors

import pandas as pd
import numpy as np

from itsdangerous import URLSafeSerializer

UPLOAD_FOLDER = 'static/upload/'
ALLOWED_EXTENSIONS_IMAGE = {'eps', 'png', 'jpg', 'jpeg', 'tiff'}
ALLOWED_EXTENSIONS_DATA = {'xlsx', 'csv'}

app = Flask(__name__)

app.wsgi_app = ProxyFix(app.wsgi_app)
app.config['SECRET_KEY'] = "fdndflkadlkadkcmnvfldksfkllmcdlkamclkmckdmadlkamkl"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CONSENT_FULL_TEMPLATE'] = 'consent.html'
app.config['CONSENT_BANNER_TEMPLATE'] = 'consent_banner.html'
consent = Consent(app)
consent.add_standard_categories()

auth_s = URLSafeSerializer("blubbblubb12edoejfdolfndjnfflkjnfnlfndajlkn", "auth") 

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

        '''
        if d['opt1'] == "on":
            d['opt1'] = str(datetime.now())
        if d['opt2'] == "on":
            d['opt2'] = str(datetime.now())
        if d['opt3'] == "on":
            d['opt3'] = str(datetime.now())
        '''


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
        #db.set_costumer_data(d)

        #return redirect(url_for('checking', sid=session_id))

        resp = make_response(redirect(url_for('checking', sid=session_id)))
        token = auth_s.dumps({"id": 0, "data": d})
        resp.set_cookie('_cid', token)
        return resp

    return render_template('index.html')

@app.route('/checking', methods=['GET', 'POST'])
def checking():

    hash_cookie = request.cookies.get('_cid')
    data_cookie = auth_s.loads(hash_cookie)
    s1 = data_cookie['data']

    session_id = request.args.get('sid')

    #logo_path = os.path.join(app.config['UPLOAD_FOLDER'], p[1], p[12])
    #data_path = os.path.join(app.config['UPLOAD_FOLDER'], p[1], p[11])

    #resp = make_response(redirect(url_for('index', sid=session_id)))
    resp = make_response(redirect(url_for('summary', sid=session_id)))
    token = auth_s.dumps({"id": 0, "data": s1})
    resp.set_cookie('_cid', token)
    return resp

@app.route('/summary', methods=['GET', 'POST'])
def summary():

    hash_cookie = request.cookies.get('_cid')
    data_cookie = auth_s.loads(hash_cookie)
    s1 = data_cookie['data']

    session_id = request.args.get('sid')
    
    logo_path = os.path.join(app.config['UPLOAD_FOLDER'], session_id, s1['file_logo'])
    data_path = os.path.join(app.config['UPLOAD_FOLDER'], session_id, s1['file_data'])
    if s1['file_data'].endswith('.csv') or s1['file_data'].endswith('.CSV') :
            df = pd.read_csv(data_path, header=None, sep=';')
    elif s1['file_data'].endswith('.xlsx') or s1['file_data'].endswith('.XLSX'):
            df = pd.read_excel(data_path, header=None)
    elif s1['file_data'].endswith('.xls') or s1['file_data'].endswith('.XLS'):
            df = pd.read_excel(data_path, header=None)
    else:
        return redirect(url_for('error', e=200))

    dfx = df.iloc[:10]

    len_df = len(df)
    if request.method == 'POST':
        s1['opt1'] = request.form.get('d_ok', True)
        s1['opt2'] = request.form.get('e_ok', True)
        s1['opt3'] = datetime.now()
        db.set_costumer_data(s1)
        d = {}
        for k, v in df.iterrows():
            qrid = str(uuid.uuid4())
            d['session_id'] = session_id
            d['firstname'] = v[0]
            d['lastname'] = v[1]
            d['company'] = v[2]
            d['street'] = v[3]
            d['number'] = v[4]
            d['zipcode'] = v[5]
            d['city'] = v[6]
            d['qr'] = qrid
            d['url'] = f'https://dialog.hakro.com/qr/{qrid}'
            db.set_retailer_data(d)

        return redirect(url_for('done'))

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=15,
        border=1,
    )
    qr.add_data('https://hakro.com')
    qr.make(fit=True)
    qr_filename = os.path.join(app.config['UPLOAD_FOLDER'], s1['session_id'], f'qr_{s1["session_id"]}.png')
    qr_code = qr.make_image(fill_color="black", back_color="transparent")
    qr_code.save(qr_filename)

    return render_template('summary.html', df=df, logo=logo_path, p=s1, len_df=len_df,qr=qr_filename, dfx=dfx)

@app.route('/done', methods=['GET', 'POST'])
def done():
    hash_cookie = request.cookies.get('_cid')
    data_cookie = auth_s.loads(hash_cookie)
    s1 = data_cookie['data']

    #session_id = s1['session_id']
    s1 = {}

    resp = make_response(render_template('done.html'))
    token = auth_s.dumps({"id": 0, "data": s1})
    resp.set_cookie('_cid', token)
    return resp

@app.route('/qr/<qrid>', methods=['GET', 'POST'])
def qr(qrid):
    if qrid == None:
        return abort(404)
    d = db.get_retailer_by_qr(qrid)
    if d: #dealer known
        e = db.get_dealer_for_retailer(d[0][1])
        if e:
            return redirect(url_for('dk', qrid=qrid))
        else:
            return redirect(url_for('du', qrid=qrid))
    else: #dealer unknown
        return redirect(url_for('du', qrid=0))

@app.route('/dk', methods=['GET', 'POST'])
def dk():
    qrid = request.args.get('qrid', True)
    d = db.get_retailer_by_qr(qrid)
    e = db.get_dealer_for_retailer(d[0][1])

    return render_template('dk.html', d=d[0], e=e[0])

@app.route('/du', methods=['GET', 'POST'])
def du():
    qrid = request.args.get('qrid', True)

    return render_template('du.html', e=None)

@app.route('/error', methods=['GET', 'POST'])
def error():
    errorcode = request.args.get('e')
    err = E.get_error(errorid=errorcode)

    return render_template('error.html', err=err[0])

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")