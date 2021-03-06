import os
import csv
import json
import socket
import requests
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

from db_routine import dbx, dby
from errors import Errors
from imager import Imager

import pandas as pd
import numpy as np

from itsdangerous import URLSafeSerializer

import jwt
import logging

import re

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

auth_s = URLSafeSerializer(
    "blubbblubfdfsdb12edoejfdolfndjnfflkjnfnlfndajlkn", "auth")

db = dbx()
db_qr = dby()
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

    response = get_user_info(token)
    if response is None:
        return False

    return response.status_code == 200


def get_user_info(token):
    headers = {
        "Authorization": f"Bearer {token}"
    }
    try:
        return requests.get(f"{IDP_URI}/auth/connect/userinfo", headers=headers)
    except Exception:
        return None


def redirect_to_login():
    response = make_response(redirect(
        f"{IDP_URI}/auth/connect/authorize?scope=openid+profile+email+offline_access&response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"))
    response.set_cookie("token", "", expires=0)
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
    token_response = requests.post(
        f"{IDP_URI}/auth/connect/token", data=payload)
    if token_response.status_code == 200:
        response = make_response(redirect(url_for('index')))
        response.set_cookie("token", token_response.json()["access_token"])
        return response

    return redirect("https://hakro.com")


def get_request_location():
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        remote_address = request.environ['REMOTE_ADDR']
    else:
        remote_address = request.environ['HTTP_X_FORWARDED_FOR']
    pl = requests.get(
        f'http://api.ipstack.com/{remote_address}?access_key=785b92a2d12f1ff90e699b814867de6f')
    app.logger.error(str(pl.json()))
    return pl.json()


def get_flipbook_link(location):
    if location.get("country_code") == "CH":
        return "https://www.flipsnack.com/C5EBD6AA9F7/7hger3547s/full-view.html"
    return "https://www.flipsnack.com/C5EBD6AA9F7/87fvghjnb3/full-view.html"


@app.route("/", methods=["GET"])
def expired():
    return render_template('expired.html')


@app.route("/magalog/<customer>", methods=["GET"])
@csrf.exempt
def magalog(customer):
    path = str(customer)
    if path:
        result = db.get_flipsnack_url(path)
        if result:
            return load_flipsnack_content(result[0])

    location = get_request_location()
    url = "https://www.flipsnack.com/C5EBD6AA9F7/hakro-verkaufsmailing-2022_de-at/full-view.html"
    if (path and path.upper() == "CH") or location.get("country_code") == "CH":
        url = "https://www.flipsnack.com/C5EBD6AA9F7/hakro-verkaufsmailing-2022_ch/full-view.html"
    return load_flipsnack_content(url)


def load_flipsnack_content(url):
    resp = requests.get(url)
    return resp.text


@app.route("/magalog/upload", methods=["POST"])
@csrf.exempt
def magalog_upload():
    df = pd.read_excel(request.get_data())
    for k, v in df.iterrows():
        row = {
            "customer": v["Kunde"],
            "path": v["Kunde kurz"],
            "flipsnack_url": v["flipsnack"]
        }
        db.insert_magalog_url(row)
    return "Upload successful!"


'''
USER FLOW 1
'''


@app.route('/upload', methods=['GET', 'POST'])
def index():
    if not is_token_valid():
        return redirect_to_login()

    location = get_request_location()
    flipbook_link = get_flipbook_link(location)

    if request.method == "POST":
        session_id = set_session_id()
        os.mkdir(os.path.join(app.config['UPLOAD_FOLDER'], session_id))
        cid = db.get_costumer_id()
        d = dict(request.form)
        d['session_id'] = session_id
        d["country"] = location.get("country_code", "Unknown")

        file_data = request.files['file_data']
        file_logo = request.files['file_logo']
        if file_data.filename == '' or file_logo.filename == '':
            flash('No selected file')
            # return redirect(request.url)
        if file_data and allowed_file_data(file_data.filename):
            filename_data = secure_filename(file_data.filename)
            fdd = filename_data.rsplit('.', 1)
            fname_file = session_id + "." + fdd[1]
            file_data.save(os.path.join(
                app.config['UPLOAD_FOLDER'], session_id, fname_file))
            d['file_data'] = fname_file

        if file_logo and allowed_file_image(file_logo.filename):
            filename_logo = secure_filename(file_logo.filename)
            fdl = filename_logo.rsplit('.', 1)
            fname_logo = session_id + "." + fdl[1]
            fpath = os.path.join(
                app.config['UPLOAD_FOLDER'], session_id, fname_logo)
            file_logo.save(fpath)
            d['file_logo'] = fname_logo

        p3 = f'{session_id}.cust'
        pickle.dump(d, open(os.path.join(
            app.config['UPLOAD_FOLDER'], session_id, p3), 'wb'))

        expire_date = datetime.now() + timedelta(minutes=5)
        resp = make_response(redirect(url_for('checking', sid=session_id)))
        token = auth_s.dumps({"id": 0, "data": d})
        resp.set_cookie('_cid', token, expires=expire_date)
        return resp

    return render_template('index.html', flipbook_link=flipbook_link)


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

    i = Imager()
    #print(os.path.join(app.config['UPLOAD_FOLDER'], session_id, s1['file_logo']))
    im = i.genImage(os.path.join(
        app.config['UPLOAD_FOLDER'], session_id, s1['file_logo']))
    print(f'debug: {im.size}')

    x, y = im.size
    o = i.getOrientation(x, y)
    print(o)
    res = i.harmonize(im, x, y, o, session_id)
    print(res)

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
    MAX_RES = 10
    fl = s1['file_logo'].rsplit('.', 1)
    logo_path = os.path.join(
        app.config['UPLOAD_FOLDER'], session_id, fl[0]+".png")
    data_path = os.path.join(
        app.config['UPLOAD_FOLDER'], session_id, s1['file_data'])
    if s1['file_data'].endswith('.csv') or s1['file_data'].endswith('.CSV'):
        with open(data_path, 'r') as csvfile:
            dialect = csv.Sniffer().sniff(csvfile.readline())
            sepsis = dialect.delimiter
        df = pd.read_csv(data_path, header=None, sep=sepsis, dtype=str)
        dfx = df.where(pd.notnull(df), "").iloc[:MAX_RES]
    elif s1['file_data'].endswith('.xlsx') or s1['file_data'].endswith('.XLSX') \
            or s1['file_data'].endswith('.xls') or s1['file_data'].endswith('.XLS'):
        try:
            df = pd.read_excel(data_path, header=None, dtype=str)
            dfx = df.where(pd.notnull(df), "").iloc[:MAX_RES]
        except Exception:
            return redirect(url_for('error', e=200))
    else:
        return redirect(url_for('error', e=200))

    if df is not None:
        y, x = df.shape
        if x < 7 or x > 11:
            return redirect(url_for('error', e=202))
        if y > 2500:
            return redirect(url_for('error', e=203))
    else:
        return redirect(url_for('error', e=201))

    df_nan = df.iloc[:, 0:6].isnull().values.any()
    if df_nan:
        return redirect(url_for('error', e=204))

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
            d['country'] = v.get(7)
            d['salutation'] = v.get(8)
            d['division'] = v.get(9)
            d['address_supplement'] = v.get(10)
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
    qr.add_data(f'https://dialog.hakro.com')
    qr.make(fit=True)
    qr_filename = os.path.join(
        app.config['UPLOAD_FOLDER'], s1['session_id'], f'qr_{s1["session_id"]}.png')
    qr_code = qr.make_image(fill_color="black", back_color="transparent")
    qr_code.save(qr_filename)

    return render_template('summary.html', df=df, logo=logo_path, p=s1, len_df=len_df, qr=qr_filename, dfx=dfx)


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
    # TODO EXP DATE in Verganenheit
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
    '''
       if not is_token_valid():
        return redirect_to_login() 
    '''

    if qrid == None:
        return abort(404)
    d = db.get_retailer_by_qr(qrid)
    if d:  # dealer known
        e = db.get_dealer_for_retailer(d[0][1])
        if e:
            if request.method == 'GET':
                r = d[0]
                retailer = {
                    "session_id": r[1],
                    "name": " ".join(filter(None, [r[2], r[3]])),
                    "company": r[4],
                    "street": " ".join(filter(None, [r[5], r[6]])),
                    "zip": r[7],
                    "city": r[8],
                    "qrid": r[9]
                }
                dealer = db.get_dealer_for_retailer(retailer["session_id"])[0]
                return render_template('dk.html', retailer=retailer, dealer=dealer)

            if request.method == 'POST':
                f = dict(request.form)
                print(f)
                f['known'] = 1
                res = db_qr.set_qr_feedback(f)
                if res:
                    return redirect(url_for('qrdone'))
        else:
            return redirect(url_for('du', qrid=qrid))
    else:  # dealer unknown
        # Daten von Sven fehlen - SteuerCD
        # return redirect(url_for('du', qrid=0))
        return redirect("https://www.hakro.com", code=302)


@app.route('/dk', methods=['GET', 'POST'])
def dk():

    if request.method == 'GET':
        qrid = request.args.get('qrid', True)
        r = db.get_retailer_by_qr(qrid)[0]
        retailer = {
            "session_id": r[1],
            "name": " ".join(filter(None, [r[2], r[3]])),
            "company": r[4],
            "street": " ".join(filter(None, [r[5], r[6]])),
            "zip": r[7],
            "city": r[8],
            "qrid": r[9]
        }
        dealer = db.get_dealer_for_retailer(retailer["session_id"])[0]
        return render_template('dk.html', retailer=retailer, dealer=dealer)

    if request.method == 'POST':
        f = dict(request.form)
        print(f)
        f['known'] = 1
        res = db_qr.set_qr_feedback(f)
        if res:
            return redirect(url_for('qrdone'))

    return redirect("https://www.hakro.com", code=302)


@app.route('/du', methods=['GET', 'POST'])
def du():
    if not is_token_valid():
        return redirect_to_login()

    qrid = request.args.get('qrid', True)

    return render_template('du.html', d=None, e=None)


@app.route('/qrdone', methods=['GET', 'POST'])
def qrdone():
    return render_template('qrdone.html')


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


'''
Metrics
'''


@app.route('/metrics/<passw>/kpi', methods=['GET'])
def metrics(passw):
    if not is_token_valid():
        return redirect_to_login()

    p = str(passw)
    mems = ['91541']
    if p not in mems:
        return redirect(url_for('index'))

    return render_template('metrics.html')


'''
Customers
'''


@app.route('/customers', methods=['GET'])
def customers():
    customers = db.get_data_costumer()

    statistics = {
        "customers": db.count_customers(),
        "addresses": db.count_addresses(),
        "swiss_addresses": db.count_swiss_addresses(),
        "addresses_from_swiss_customers": db.count_addresses_from_swiss_customers()
    }

    return render_template('customers.html', customers=customers, statistics=statistics)


@app.route("/customers/<session_id>", methods=["DELETE"])
def delete_customer(session_id):
    db.delete_customer(session_id)
    return make_response("", 204)


'''
Addresses
'''


@app.route('/addresses/<session_id>', methods=['GET'])
def addresses(session_id):
    addresses = db.get_data_retailer(str(session_id))
    customer = db.get_costumer_data(str(session_id))
    if not customer:
        return render_template("no_addresses.html")
    return render_template('addresses.html', addresses=addresses, customer=customer[0])


@app.route("/addresses/<id>", methods=["DELETE"])
def delete_address(id):
    db.delete_address(id)
    return make_response("", 204)


@app.route("/statistics", methods=["GET"])
def statistics():
    salutation = db.count_salutation()
    firstname = db.count_firstname()
    lastname = db.count_lastname()
    company = db.count_company()

    return render_template("statistics.html", salutation=salutation, firstname=firstname, lastname=lastname, company=company)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", ssl_context='adhoc')
