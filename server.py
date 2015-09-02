from flask import Flask, request, render_template, g
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
LISTEN_HOSTNAME = args.bind_host if args.bind_host is not None else LISTEN_HOST_NAME
LISTEN_PORT = args.bind_port if args.bind_port is not None else LISTEN_PORT
DEBUG = args.debug 

if DEBUG:
    LISTEN_HOSTNAME = '192.168.2.64'
    LISTEN_PORT = 5000

def conn():
    return sqlite3.connect(DB_PATH)

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
        filed.save(app.config['UPLOAD_FOLDER'] + '/' +  filehash64)
        filename = filed.filename
        urlhash = base64.urlsafe_b64encode(hashlib.md5(filehash + filename.encode('utf-8')).digest())
        return filehash64 + '\n' + urlhash.decode() + '\n'
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
