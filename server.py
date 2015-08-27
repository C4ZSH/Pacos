from flask import Flask, request, render_template
import argparse
import os
import sqlite3
import time, base64, hashlib

# file upload server. should be able to upload stuff via curl or similar
# for this to serve.

def firstrun():
    ## generate config
    with sqlite3.connect("hashes.db") as conn:
        if not os.path.isfile("hashes.db"):
            with open("schema.sql", 'rt') as schm:
                schema = schm.read()
            conn.executescript(schema)



pathtodir = 'uploads'
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = pathtodir
app.config['MAX_CONTENT_LENGTH'] = 314 * 1024 * 1024

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
    app.run(debug=True, host='192.168.2.64')    
