from flask import Flask, request, render_template
import argparse
import os
import sqlite3
import time, base64, hashlib

# file upload server. should be able to upload stuff via curl or similar
# for this to serve.

parser = argparse.ArgumentParser(description="Simple HTTP upload server")
parser.add_argument("-d", "--debug", help="As it says on the tin", action="store_true")
parser.add_argument("-H", "--bind-host", help="hostname to listen on, default 0.0.0.0 (all)", type=str, default='0.0.0.0')
parser.add_argument("-p", "--bind-port", help="port to listen on, default 80, or 5000 if flag -d is used", type=int, default=80)
parser.add_argument("--upload-folder", help="where user uploaded files get stored", type=str)

args = parser.parse_args()
DB_PATH = "hashes.db"
LOG_PATH = ''
UPLOAD_FOLDER = 'uploads'
LISTEN_HOSTNAME = args.bind_host
LISTEN_PORT = args.bind_port
DEBUG = args.debug if not None else False

if args.debug:
    LISTEN_HOSTNAME = localhost
    LISTEN_PORT = 5000

def firstrun():
    ## generate config
    with sqlite3.connect(DB_PATH) as conn:
        if not os.path.isfile(DB_PATH):
            with open("schema.sql", 'rt') as schm:
                schema = schm.read()
            conn.executescript(schema)
            conn.commit()

def conn():
    return sqlite3.connect(DB_PATH)

pathtodir = 'uploads'
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = pathtodir
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024

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

        filehash = gen_hash(filed) #hasher.digest()
        filehash64 = base64.urlsafe_b64encode(filehash).decode()
        filed.save(app.config['UPLOAD_FOLDER'] + '/' +  filehash)
        filename = filed.filename
        urlhash = base64.urlsafe_b64encode(gen_hash((filehash + filename.encode('utf-8'))))
        return filehash + '\n'
    return '''
    <!doctype html>
    <title>CLI file uploads</title>
    <body><p>Upload your files with 'curl -F "file=@path_to_your_file" host'</p>
    </body>'''

@app.route('/<filehash>', methods=["GET"])
def file_request(filehash):
    if request.method == "GET":
        pass



if __name__ == '__main__':
    app.run(debug=DEBUG, host=LISTEN_HOSTNAME, port=LISTEN_PORT)    
