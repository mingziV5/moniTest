#!/usr/bin/python
#coding:utf-8

import Queue
import threading
import time
import json
import urllib2
import socket
import commands
import pdb
from moniItems import mon

import sys, os

trans_l = ['localhost:50000']

class porterThread (threading.Thread):
    def __init__(self, name, q_to_collect=None,q_to_send=None, interval=None):
        threading.Thread.__init__(self)
        self.name = name
        self.q_to_collect = q_to_collect
        self.q_to_send = q_to_send
        self.interval = interval
        self.sock_l = [None]

    def run(self):
        #print "Starting %s"  % self.name
        if self.name == 'collect':
            self.put_data()
        if self.name == 'user':
            self.put_user_data()
        elif self.name == 'sendjson':
            self.get_data()

    def put_data(self):
        m = mon()
        atime=int(time.time())
        while 1:
            if not self.q_to_collect.empty():
                data = self.q_to_collect.get()
                #atime = data['atime']
                #del(data['atime'])
                data.update(m.runAllGet())
            else:
                data = m.runAllGet()
 
            self.q_to_send.put(data)
            btime = int(time.time())
            time.sleep(self.interval-((btime-atime)%self.interval))
            
            #evt.set()用于线程间同步将flag设置为true
            #data = m.runAllGet()
            #print data 
            #self.queueLock.acquire()
            #self.q.put(data)
            #self.queueLock.release()
            #btime=int(time.time())
            #print '%s  %s' % (str(data), self.interval-((btime-atime)%30))
            #time.sleep(self.interval-((btime-atime)%self.interval))

    def put_user_data(self):
        m = mon()
        atime = int(time.time())
        while True:
            data = m.userDefineMon()
            self.q_to_collect.put(data)
            time.sleep(4)
            btime = int(time.time())
            time.sleep(self.interval-((btime-atime)%self.interval))

            #Event 用于put_user_data 和 put_data 线程间同步
            #evt = threading.Event()
            #data = m.userDefineMon()
            #data.update({'atime':atime})
            #self.q_to_collect.put(data)
            #evt.wait()等待flag信号
            
    def get_data(self):
        while 1:
            print "get" 
            #self.queueLock.acquire()
            if not self.q_to_send.empty():
                data = self.q_to_send.get()
                print data
                #pdb.set_trace()
                #sendData_mh(self.sock_l, trans_l, json.dumps(data))
            #self.queueLock.release()
            time.sleep(self.interval)

def startTh():
    q1 = Queue.Queue(10)
    q2 = Queue.Queue(10)
    user_collect = porterThread(name='user',q_to_collect=q1, interval=3)
    collect = porterThread(name='collect', q_to_collect=q1, q_to_send=q2, interval=3)
    user_collect.start()
    collect.start()
    #time.sleep(0.5)
    sendjson = porterThread(name='sendjson', q_to_send=q2, interval=3)
    sendjson.start()
    print  "start"
    user_collect.join()
    collect.join()
    sendjson.join()
if __name__ == "__main__":
    startTh()
