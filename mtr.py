#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import sys
import time
import datetime
import threading
import subprocess
import shlex
import Queue
import cStringIO
import codecs
import socket
import smtplib
from email.mime.text import MIMEText

LOGDIR = "log/"
HOSTS = "hosts.txt"

# 超过多少台机器同时丢包, 就发送报警
LOSTS_WARNING = 5
TO = ["sysadm@pubyun.com"]
FROM = "sysadm@sys.pubyun.com"

hosts = {}

class HandleMinute(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        queues = Queue.Queue()
        threads = [Mtr(ip, queues) for ip in hosts]
        # 主线程完成了，不管子线程是否完成，都要和主线程一起退出
        _ = [t.setDaemon(True) for t in threads]
        _ = [t.start() for t in threads]
        _ = [t.join() for t in threads]
        losts = []
        while not queues.empty():
            losts.append(queues._get())
        if (len(losts) > LOSTS_WARNING):
            self.warning(now, losts)

    def get_ip_address(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("114.114.114.114", 53))
            ip = s.getsockname()[0]
        except:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip

    def warning(self, now, losts):
        buffer = cStringIO.StringIO()
        output = codecs.getwriter("utf8")(buffer)
        output.write(u"测试时间: %s\n" % now)
        output.write(u"丢包主机: %d\n\n" % len(losts))
        output.write(
            u"归属地   IP地址          丢包率  发包 丢包  Last  Avg   Best  Wrst  StDev\n")
        losts.sort(key=lambda i: i[2], reverse=True)
        for (ip, msg, lost) in losts:
            output.write(u"%s: %s\n" % (hosts.get(ip, u"未知"), msg))
        msg = MIMEText(output.getvalue())
        output.close()
        msg['Subject'] = u'%s丢包告警, %d个IP丢包, %s' \
                         % (self.get_ip_address(), len(losts), now)
        msg['From'] = FROM
        msg['To'] = ", ".join(TO)
        s = smtplib.SMTP('localhost')
        s.sendmail(FROM, TO, msg.as_string())
        s.quit()


class Mtr(threading.Thread):
    def __init__(self, ip, queues):
        threading.Thread.__init__(self)
        self._ip = ip
        self._queues = queues
        cmd = "mtr -c 60 -o 'LSD NABWV' -rwn"
        self._cmd = shlex.split(cmd)
        self._cmd.append(self._ip)

    def run(self):
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        proc = subprocess.Popen(self._cmd, stdout=subprocess.PIPE)
        out, err = proc.communicate()
        fullname = os.path.join(LOGDIR, "%s.log" % self._ip)
        with open(fullname, "a") as f:
            # 写日志时间
            if "Start: " not in out:
                f.write("Start: %s\n" % now)
            f.write(out)
        # 如果丢包, 则返回IP和丢包信息
        pat = re.compile(self._ip + "\s+(\d+\.\d+)%\s+(\d+)\s+(\d+)")
        for line in out.split("\n"):
            m = pat.search(line)
            if m and int(m.group(3)) > 0:
                self._queues.put((self._ip, line[m.start():], int(m.group(3))))


def run_mtr():
    if not os.path.exists(LOGDIR):
        os.makedirs(LOGDIR)
    while True:
        time.sleep(60.0 - time.time() % 60.0)
        h = HandleMinute()
        h.setDaemon(True)
        h.start()


def read_hosts():
    if not os.path.isfile(HOSTS):
        print "%s not exist" % HOSTS
        sys.exit(1)
    with codecs.open(HOSTS, "r", "utf-8") as f:
        for line in f:
            (ip, desc) = line.split(None, 1)
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
