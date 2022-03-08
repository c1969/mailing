import os
import re
import csv
import json, socket, requests
from flask import Flask, redirect, render_template, session, url_for, request, g, make_response, flash, send_from_directory, send_file, Response, abort
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_consent import Consent
from flask_wtf.csrf import CSRFProtect, CSRFError

import uuid
import pickle
from datetime import datetime, timedelta
from PIL import Image
import qrcode

from db_routine import dbx
from errors import Errors

import pandas as pd
import numpy as np

from itsdangerous import URLSafeSerializer

import jwt

UPLOAD_FOLDER = 'static/upload/'
ALLOWED_EXTENSIONS_IMAGE = {'png', 'jpg', 'jpeg', 'tiff'}
ALLOWED_EXTENSIONS_DATA = {'xlsx', 'csv'}

IDP_URI = os.getenv('IDP_URI', 'https://idp.dev.hakro.com')
CLIENT_ID = os.getenv('CLIENT_ID', 'hakro-dialog-dev')
REDIRECT_URI = os.getenv('REDIRECT_URI', 'https://localhost:5000/idp/login')
CLIENT_SECRET = os.getenv("CLIENT_SECRET", "qPij5vw9DZPx2pZz0wKCMdRSFJ55NT")

app = Flask(__name__)

app.wsgi_app = ProxyFix(app.wsgi_app)
app.config['SECRET_KEY'] = "fdndflkadlkadkcmnvfldksfkllmcdlkamclkmckdmadlkamkl"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CONSENT_FULL_TEMPLATE'] = 'consent.html'
app.config['CONSENT_BANNER_TEMPLATE'] = 'consent_banner.html'
consent = Consent(app)
consent.add_standard_categories()

csrf = CSRFProtect(app)

auth_s = URLSafeSerializer("blubbblubfdfsdb12edoejfdolfndjnfflkjnfnlfndajlkn", "auth") 

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

def is_token_valid():
    token = request.cookies.get("token")
    
    if token is None:
        return False

    decoded = jwt.decode(token, options={"verify_signature": False})
    if decoded["client_id"] != CLIENT_ID and decoded["iss"] != IDP_URI + "/auth":
        return False

    headers = {
        "Authorization": f"Bearer {token}"
    }
    try:
        response = requests.get(f"{IDP_URI}/auth/connect/userinfo", headers = headers)
        return response.status_code == 200
    except Exception:
        return False

def redirect_to_login():
    response = make_response(redirect(f"{IDP_URI}/auth/connect/authorize?scope=openid+profile+email+offline_access&response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"))
    response.set_cookie("token", "", expires = 0)
    return response

@app.route('/idp/login')
def login():
    payload = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "code": request.args.get("code"),
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI
    }
    token_response = requests.post(f"{IDP_URI}/auth/connect/token", data = payload)
    if token_response.status_code == 200:
        response = make_response(redirect(url_for('index')))
        response.set_cookie('token', token_response.json()["access_token"])
        return response

    return redirect("https://hakro.com")

'''
USER FLOW 1
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    if not is_token_valid():
        return redirect_to_login()

    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        remote_address = request.environ['REMOTE_ADDR']
    else:
        remote_address = request.environ['HTTP_X_FORWARDED_FOR']
    pl = requests.get(f'http://api.ipstack.com/{remote_address}?access_key=785b92a2d12f1ff90e699b814867de6f')
    payload = pl.json()

    if request.method == "POST":
        session_id = set_session_id()
        os.mkdir(os.path.join(app.config['UPLOAD_FOLDER'], session_id))
        cid = db.get_costumer_id()
        d = dict(request.form)

        d['session_id'] = session_id
        if  payload:
            d['country'] = payload['country_code']
        else:
            d['country'] = "Unknown"



        file_data = request.files['file_data']
        file_logo = request.files['file_logo']
        if file_data.filename == '' or file_logo.filename == '':
            flash('No selected file')
            #return redirect(request.url)
        if file_data and allowed_file_data(file_data.filename):
            filename_data = secure_filename(file_data.filename)
            fdd = filename_data.rsplit('.', 1)
            fname_file = session_id + "." +fdd[1]
            file_data.save(os.path.join(app.config['UPLOAD_FOLDER'], session_id, fname_file))
            d['file_data'] = fname_file

        if file_logo and allowed_file_image(file_logo.filename):
            filename_logo = secure_filename(file_logo.filename)
            fdl = filename_logo.rsplit('.', 1)
            fname_logo = session_id + "." +fdl[1]
            file_logo.save(os.path.join(app.config['UPLOAD_FOLDER'], session_id, fname_logo))
            d['file_logo'] = fname_logo

        p3 = f'{session_id}.cust'
        pickle.dump(d, open(os.path.join(app.config['UPLOAD_FOLDER'], session_id, p3), 'wb'))

        expire_date = datetime.now() + timedelta(minutes=5)
        resp = make_response(redirect(url_for('checking', sid=session_id)))
        token = auth_s.dumps({"id": 0, "data": d})
        resp.set_cookie('_cid', token, expires=expire_date)
        return resp

    return render_template('index.html', d=payload)


@app.route('/checking', methods=['GET', 'POST'])
def checking():
    if not is_token_valid():
        return redirect_to_login()
    
    hash_cookie = request.cookies.get('_cid')
    if hash_cookie == None:
        return redirect(url_for('index'))
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
    if not is_token_valid():
        return redirect_to_login()

    hash_cookie = request.cookies.get('_cid')
    if hash_cookie == None:
        return redirect(url_for('index'))
    data_cookie = auth_s.loads(hash_cookie)
    s1 = data_cookie['data']

    session_id = request.args.get('sid')
    
    logo_path = os.path.join(app.config['UPLOAD_FOLDER'], session_id, s1['file_logo'])
    data_path = os.path.join(app.config['UPLOAD_FOLDER'], session_id, s1['file_data'])
    if s1['file_data'].endswith('.csv') or s1['file_data'].endswith('.CSV') :
            sniffer = csv.Sniffer()
            df = pd.read_csv(data_path, header=None, sep=';')
            dfx = df.iloc[:10]
    elif s1['file_data'].endswith('.xlsx') or s1['file_data'].endswith('.XLSX'):
            df = pd.read_excel(data_path, header=None)
            dfx = df.iloc[:10]
    elif s1['file_data'].endswith('.xls') or s1['file_data'].endswith('.XLS'):
            df = pd.read_excel(data_path, header=None)
            dfx = df.iloc[:10]
    else:
        return redirect(url_for('error', e=200))

    if df is not None:
        y, x = df.shape
        if x != 7:
            return redirect(url_for('error', e=202))
        if y > 2500:
            return redirect(url_for('error', e=203))
    else:
        return redirect(url_for('error', e=201))

    

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
    if not is_token_valid():
        return redirect_to_login()
    
    hash_cookie = request.cookies.get('_cid')
    if hash_cookie == None:
        return redirect(url_for('index'))
    data_cookie = auth_s.loads(hash_cookie)
    s1 = data_cookie['data']

    #session_id = s1['session_id']
    #TODO EXP DATE in Verganenheit
    s1 = {}
    expire_date = datetime.now() - timedelta(days=1)

    resp = make_response(render_template('done.html'))
    token = auth_s.dumps({"id": 0, "data": s1})
    resp.set_cookie('_cid', token, expires=expire_date)
    return resp


'''
USER FLOW 2
'''
@app.route('/qr/<qrid>', methods=['GET', 'POST'])
def qr(qrid):
    if not is_token_valid():
        return redirect_to_login()
    
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
    if not is_token_valid():
        return redirect_to_login()
    
    qrid = request.args.get('qrid', True)
    d = db.get_retailer_by_qr(qrid)
    e = db.get_dealer_for_retailer(d[0][1])

    return render_template('dk.html', d=d[0], e=e[0])

@app.route('/du', methods=['GET', 'POST'])
def du():
    if not is_token_valid():
        return redirect_to_login()
    
    qrid = request.args.get('qrid', True)

    return render_template('du.html', e=None)

@app.route('/error', methods=['GET', 'POST'])
def error():
    if not is_token_valid():
        return redirect_to_login()
    
    errorcode = request.args.get('e')
    err = E.get_error(errorid=errorcode)

    return render_template('error.html', err=err[0])

@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    csrf_err = True
    return render_template('error.html', err=e.description, csrf_err=csrf_err), 400

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", ssl_context='adhoc')