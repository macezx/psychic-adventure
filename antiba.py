from __future__ import print_function
import re,os
bare = re.compile(r'.*pam\_unix\(sshd\:auth\)\: authentication failure;.*');
rhre = re.compile(r'.*rhost=(.*) ');
hostdict = {};
dbfile = "db"

def procline(line):
    m = bare.match(line);
    if(m is not None):
        m = rhre.match(line);
        if(m is not None):
            host = m.group(1).strip();
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
    db = [];
    if os.path.exists(dbfile):
        ins = open(dbfile,'r');
        try:
            for line in ins:
                line = line.strip()
                db.append(line);
        finally:
            ins.close();
    db.sort();

    hosts = hostdict.keys();
    hosts.sort();
    if len(db) > 0:
        import bisect
        for host in hosts:
            if host not in db:
                bisect.insort(db,host);
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

def runiptscrpts():
    iprestart = "service iptables restart";
    iplog = "iptables -N LOGGING";
    iptemp = "iptables -A INPUT -s {0} -j LOGGING &> /dev/NULL";
    ipend = ["iptables -A LOGGING -m limit --limit 2/min -j LOG " +
    "--log-prefix \"IPTables-Dropped: \" --log-level 4",
    "iptables -A LOGGING -j DROP"];
    db = [];

    if os.path.exists(dbfile):
        ins = open(dbfile,'r');
        try:
            for line in ins:
                line = line.strip()
                db.append(line);
        finally:
            ins.close();

        if len(db) > 0 :
            db.sort();
            import subprocess,shlex
            retcode = subprocess.call(shlex.split(iprestart));
            retcode = subprocess.call(shlex.split(iplog));
            if retcode != 127:
                for host in db:
                    cmd = iptemp.format(host);
                    retcode = subprocess.call(cmd, shell=True);
                    if retcode != 0:
                        print("adding rule failed");
                        break;
                for str in ipend:
                    retcode = subprocess.call(shlex.split(str));
                    if retcode != 0:
                        print("ending failed");
                        break;
            else:
                print("iprestart failed");
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

        runiptscrpts();
