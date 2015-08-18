from flask import Flask, request, render_template
import argparse
import os
import time, base64, hashlib

# file upload server. should be able to upload stuff via curl or similar
# for this to serve.

def firstrun():
    ## generate config
    pass

    
def name_file(fileo, extension):
    bs = 78931
    hashgen = hashlib.md5()
    filebuf = fileo.read(bs)
    while len(filebuf) > 0:
        hashgen.update(filebuf)
        filebuf = hashgen.update(filebuf)

    return base64.urlsafe_b64encode(str(hashgen))[-7:] + '.' + (extension or "")
#    return base64.urlsafe_b64encode(str(hashlib.md5(str(time.time()).encode('utf-8'))).encode('utf-8'))[-8:] + (extension or '')

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
            if len(f) > 1: ext = +f[-1:]
            if ext in ('gz','bz2','xz') and f[-2:-1:] = 'tar':
                return '.tar.%s' % ext
            return '.' + ext
        filed.save(app.config['UPLOAD_FOLDER'] + name_file(filed, get_ext(filed.filname))
    
