from flask import Flask, request, render_template, g, make_response, url_for, abort
import argparse
import os, sys
import sqlite3
import time, base64, hashlib, json

# file upload server. should be able to upload stuff via curl or similar
# for this to serve.

parser = argparse.ArgumentParser(description="Simple HTTP upload server")
parser.add_argument("-d", "--debug", help="As it says on the tin", action="store_true")
parser.add_argument("-H", "--bind-host", help="hostname to listen on, default 0.0.0.0 (all)", type=str)
parser.add_argument("-p", "--bind-port", help="port to listen on, default 80, or 5000 if flag -d is used", type=int)
parser.add_argument("--upload-folder", help="where user uploaded files get stored", type=str)
parser.add_argument("-c", "--config-file", help="path to config file, if it is not config.json", type=str, default="config.json")
parser.add_argument("-b", "--database", help="path to database. will override that specified in the config", type=str)

args = parser.parse_args()
print(args)
if not os.path.isfile(args.config_file):
    print("No config detected, exiting.")
    sys.exit(1)
with open(args.config_file) as config:
    config = json.loads(config.read())
    DB_PATH = config['database'] 
    UPLOAD_FOLDER = config['upload-directory']
    LISTEN_HOSTNAME = config['bind-host'] 
    LISTEN_PORT = config['bind-port']
    ALLOWED_EXTENSIONS = config['allowed-extensions']
    MAX_UPLOAD_SIZE = config['max-upload-size']

DB_PATH = args.database if args.database is not None else DB_PATH
LOG_PATH = ''
UPLOAD_FOLDER = args.upload_folder if args.upload_folder is not None else UPLOAD_FOLDER
LISTEN_HOSTNAME = args.bind_host if args.bind_host is not None else LISTEN_HOSTNAME
LISTEN_PORT = args.bind_port if args.bind_port is not None else int(LISTEN_PORT)
DEBUG = args.debug 

if DEBUG:
    LISTEN_HOSTNAME = '192.168.2.64'
    LISTEN_PORT = 5000

def conn():
    return sqlite3.connect(DB_PATH)

def get_db():
    db = getattr(g, '_database', None)
    if db is None: db = g._database = conn()
    return db

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_UPLOAD_SIZE

@app.before_request
def open_conn():
    g.db = conn()

@app.teardown_request
def close_on_except(exception):
    db = getattr(g, '_database', None)
    if db is not None: db.close()

@app.route('/', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        filed = request.files['file']
        print(app.config['UPLOAD_FOLDER'])
        def get_ext(filename):
            f = filename.split('.')
            ext = f[-1:] if len(f) > 1 else ""
            if ext in ('gz','bz2','xz') and f[-2:-1:] == 'tar':
                return '.tar.%s' % ext
            return '.' + ext


        hasher = hashlib.md5()

        try:
            while True:
                ch = filed.read(1024)
                if not ch: break
                hasher.update(ch)
        finally:
            filed.seek(0)

        def gen_hash(obj):
            hasher = hashlib.md5()
            try:
                while True:
                    ch = obj.read(1024)
                    if not ch: break
                    hasher.update(ch)
            finally:
                obj.seek(0)
            return hasher.digest()

        filehash = gen_hash(filed) #hasher.digest()
        filehash64 = base64.urlsafe_b64encode(filehash).decode()
        if not os.path.isfile(app.config['UPLOAD_FOLDER'] + '/' + filehash64):
            filed.save(app.config['UPLOAD_FOLDER'] + '/' +  filehash64)
        filename = filed.filename
        mimetype = filed.content_type
        urlhash = base64.urlsafe_b64encode(hashlib.md5(filehash + filename.encode('utf-8')).digest()).decode()
        curs = get_db().cursor()
        hostname_accessed = request.headers['Host']
        url_from_host = 'http://%s/%s' % (hostname_accessed, urlhash)
        url_from_flask = url_for('file_request', urlhash=urlhash)
        tup = (urlhash, filehash64, filename, mimetype)
        curs.execute('INSERT INTO hashes VALUES (?,?,?,?)', tup)
        curs.commit()
        return filehash64 + '\n' + urlhash + '\n' + url_from_host + '\n' + url_from_flask +'\n'
    return '''
    <!doctype html>
    <title>CLI file uploads</title>
    <body><p>Upload your files with 'curl -F "file=@path_to_your_file" host'</p>
    </body>'''

@app.route('/<urlhash>', methods=["GET"])
def file_request(urlhash): # download page
    curs = get_db().cursor()
    uhash = (urlhash,)
    curs.execute('SELECT * FROM hashes WHERE urlhash=?', uhash)
    row = curs.fetchone()
    if row is None: abort(404)
    else:
        filehash = row[1]
        filename = row[2]
        
        return send_from_directory(app.config['UPLOAD_FOLDER'], filehash, as_attachment=True, attachment_filename=filename)

@app.route('/<urlhash>/info', methods=["GET"])
def file_info(urlhash):
    curs = get_db().cursor()
    uhash = (urlhash,)
    curs.execute('SELECT * FROM hashes WHERE urlhash=?', uhash)
    row = curs.fetchone()
    if row is None: abort(404)
    else: 
        filehash = row[1]
        filename = row[2]
        mimetype = row[3]
        sizeof = os.path.getsize(UPLOAD_FOLDER + '/' + filehash)
        return """
        <!doctype html>
        <title>File Info</title>
        <body><h1>Information for %s</h1>
              <p><b>Filesize:</b> %s</p>
              <p><b>Mimetype:</b> %s</p>
        </body> """ % (filename, sizeof, mimetype)



if __name__ == '__main__':
    app.run(debug=DEBUG, host=LISTEN_HOSTNAME, port=LISTEN_PORT)    
