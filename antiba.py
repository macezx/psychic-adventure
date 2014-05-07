from __future__ import print_function
import re
bare = re.compile(r'.*pam\_unix\(sshd\:auth\)\: authentication failure;.*');
rhre = re.compile(r'.*rhost=(.*) ');
hostdict = {};

def procline(line):
    m = bare.match(line);
    if(m is not None):
        m = rhre.match(line);
        if(m is not None):
            host = m.group(1);
            if(hostdict.has_key(host)):
                hostdict[host] += 1;
            else:
                hostdict[host] = 1;

def stats():
    import os
    statsdir = './stats';
    if not (os.path.exists(statsdir)):
        os.mkdir(statsdir);
    elif not (os.path.isdir(statsdir)):
        print(statsdir + " is not a directory");
        return;

    hosts = hostdict.items();
    hosts.sort(key=lambda tup:tup[1], reverse=True);
    import datetime
    os = open(os.path.join(statsdir,datetime.datetime.now().strftime("%y-%m-%d-%H-%M-%S")),'w');
    try:
        for host in hosts:
            line = "{0:<16}\t{1:<6}".format(host[0], host[1]);
            os.write(line + "\n");
    finally:
        os.close();

def updatedb():
    dbfile = "db"
    db = [];
    import os

    if os.path.exists(dbfile):
        ins = open(dbfile,'r');
        try:
            for line in ins:
                db.append(line);
        finally:
            ins.close();
    db.sort();

    hosts = hostdict.keys();
    hosts.sort();
    if len(db) > 0:
        from bisect import bisect
        for host in hosts:
            index = bisect(db, host);
            if not( index != len(db) and db[index] == host):
                db.insert(index, host);
    else:
        db = hosts;

    tmp = dbfile + ".tmp";
    if os.path.exists(tmp):
        os.remove(tmp)
    ous = open(tmp,"w");
    try:
        for host in db:
            ous.write(host+"\n");
    finally:
        ous.close();

    if os.path.exists(dbfile):
        os.rename(dbfile, dbfile+".bak");
        os.rename(dbfile+".tmp", dbfile);
        os.remove(dbfile + ".bak");
    else:
        os.rename(dbfile+".tmp", dbfile);

    del hosts;
    del db;

import sys
if(__name__ == "__main__") :
    if(len(sys.argv) < 2):
        print("cmd data_path");
    else:
        ins = open(sys.argv[1]);
        try:
            for line in ins:
                procline(line);
        finally:
            ins.close();

        stats();
        updatedb();

        hostdict.clear();
        del hostdict;
