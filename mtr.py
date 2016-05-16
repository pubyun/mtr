#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import sys
import threading
import subprocess

LOGDIR = "log/"
HOSTS = "hosts.txt"
hosts = {}

class Mtr(threading.Thread):
    def __init__(self, ip):
        threading.Thread.__init__(self)
        self._ip = ip
        self._runing = True

    def stop(self):
        self._runing = False

    def run(self):
        while (self._runing):
            # mtr -c 60 -o "LSD NABWV" -rwn $1
            cmd = ["mtr", "-c", "60", "-o", "LSD NABWV", "-rwn", self._ip]
            proc = subprocess.Popen(cmd,stdout=subprocess.PIPE)
            fullname = os.path.join(LOGDIR, "%s.log" % self._ip)
            with open(fullname, "a") as f:
                for line in proc.stdout:
                    f.write(line)

def run_mtr():
    if not os.path.exists(LOGDIR):
        os.makedirs(LOGDIR)
    for ip in hosts:
        mtr = Mtr(ip)
        mtr.start()

def read_hosts():
    if not os.path.isfile(HOSTS):
        print "%s not exist" % HOSTS
        sys.exit(1)
    with open(HOSTS, "r") as f:
        for line in f:
            (ip, desc) = line.split()
            hosts[ip] = desc

def process_host_log(logfile):
    ip, file_extension = os.path.splitext(logfile)
    pat = re.compile(ip + "\s+(\d+\.\d+)%\s+(\d+)\s+(\d+)")
    fullname = os.path.join(LOGDIR, logfile)
    errors = 0
    count = 0
    with open(fullname, 'r') as f:
        for line in f:
            if line.startswith("Start: "):
                started = line
            m = pat.search(line)
            if m and int(m.group(3)) > 0:
                print started, line,
                errors += 1
                count += int(m.group(3))
    print "%s - %s: 丢包次数 %d 丢包数 %d" % (ip, hosts.get(ip, "未知"), errors, count)
    if errors:
        print "-" * 40
    else:
        print "*" * 40


def process_logs():
    for logfile in os.listdir(LOGDIR):
        if logfile.endswith(".log"):
            process_host_log(logfile)

def main():
    read_hosts()
    if len(sys.argv) > 1 and "log" == sys.argv[1]:
        process_logs()
    else:
        run_mtr()

if __name__ == '__main__':
    main()
