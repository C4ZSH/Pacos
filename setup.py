#!/usr/bin/python3

import json, sys, sqlite3, os, argparse

parser = argparse.ArgumentParser(description="setup script")
parser.add_argument("-c", "--config", help="Config file location. Changes will be saved here, and database location will be taken from this file.", default="config.json")
parser.add_argument("-i", "--init-db-only", help="Do not create new config; only initialise db", action="store_true")
args = parser.parse_args()

conffile = args.config

def confgen():
    print("Setup script")
    print("Creating config. If you already have a config and would like to initialise the database, please ^C and rerun this script with the flag -i")
    host = input("If you are unsure what to enter, pressing return will use reasonable defaults\nHostname to listen on (default: all): ")
    v_host = '0.0.0.0' if host == '' else host
    port = input("Port to listen on (default: 80): ")
    if port != '' and (not port.isdigit() or int(port) > 65534):
        port = input("Please enter a valid port, or press enter to use default: ")
    v_port = 80 if port == '' else port
    uploaddir = input("Path to directory for user-uploaded files (default: sthen/uploads/): ")
    v_uploaddir = 'uploads' if uploaddir == '' else uploaddir
    allowed_ext = input("Allowed file extensions, seperated by spaces. Press enter to allow all\n> ")
    v_allowed_ext = allowed_ext.split()
    hashdb = input("Path to sqlite3 database used. If none exists at this location it will be created. (default: hashes.db): ")
    v_hashdb = hashdb if hashdb != '' else 'hashes.db'
    maxsize = input("Maximum allowed file size for uploads in bytes, or use suffix K, M, or G (default: 50 MB): ")
    v_maxsize = 50 * 1024 * 1024
    ssufx = {'K': 1024, 'M': 1024*1024, 'G': 1024**3}
    if maxsize.strip()[-1:].upper() in ssufx and maxsize.strip()[:-1].isdigit(): 
        v_maxsize = int(maxsize.strip()[:-1]) * ssufx[maxsize.strip()[-1:].upper()]
    data = {'bind-host': v_host, 'bind-port': v_port, 'max-upload-size': v_maxsize, 
            'upload-directory': v_uploaddir, 'allowed-extensions': v_allowed_ext, 
            'database': v_hashdb}
    conffile = sys.argv[1] if len(sys.argv) > 1 else 'config.json'
    confirm = input('Confirm that you wish this config to be written to %s. This will overwrite any previous file at this location. Create config? [y/n] ' % conffile)
    if confirm == 'n': sys.exit(0)
    with open(conffile, 'w') as config:
        json.dump(data, config, sort_keys=True, indent=4)
    print('Wrote config to %s. Edit this file or run this script again to make changes.' % conffile)
    return v_hashdb

def init_db(DB_PATH):
    if not os.path.isfile(DB_PATH):
        with sqlite3.connect(DB_PATH) as conn:
            with open("schema.sql", 'rt') as schm:
                schema = schm.read()
                conn.executescript(schema)
                conn.commit()    


if __name__ == '__main__': 
    if not args.init_db_only:
        try: db = confgen()
        except KeyboardInterrupt:
            print('\n')
            sys.exit(0)
        print("Initialising new database at %s" % db)
    else:
        with open(conffile) as conf:
            conf = json.loads(conf.read())
            db = conf['database']
    init_db(db)
