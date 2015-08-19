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
    print(fileo)
    hashgen = hashlib.md5()
    filebuf = fileo.stream.read(1024)
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
            ext = f[-1:] if len(f) > 1 else ""
            if ext in ('gz','bz2','xz') and f[-2:-1:] == 'tar':
                return '.tar.%s' % ext
            return '.' + ext


        hasher = hashlib.md5()

        # def chuncker(file_o, chsize=1024):
        #     while True:
        #         chunck = file_o.read(chsize)
        #         if not chunk: break
        #         hasher.update(chunk)

        try:
            while True:
                ch = filed.read(1024)
                if not ch: break
                hasher.update(ch)
        finally:
            filed.seek(0)
            
#        hashgen = str(base64.urlsafe_b64encode(str(hashlib.md5(filed.stream.read()))))[-7:]
        
        newname = base64.urlsafe_b64encode(str(hasher).encode('utf-8')).decode()
        filed.save(app.config['UPLOAD_FOLDER'] + '/' +  newname)
    return newname



if __name__ == '__main__':
    app.run(debug=True, host='192.168.2.64')    
