#!/usr/bin/env python
# coding: utf-8
# 所有内容加上注释，改成多线程或者多进程模式
'''
class STATE:
    def __init__(self):
        self.state = "accept"
        self.have_read = 0
        self.need_read = 10
        self.have_write = 0
        self.need_write = 0
        self.buff_write = ""
        self.buff_read = ""
        # sock_obj is a object
        self.sock_obj = ""
        self.popen_pipe = 0

    def printState(self):
        if DEBUG:
            dbgPrint('\n - current state of fd: %d' % self.sock_obj.fileno())
            dbgPrint(" - - state: %s" % self.state)
            dbgPrint(" - - have_read: %s" % self.have_read)
            dbgPrint(" - - need_read: %s" % self.need_read)
            dbgPrint(" - - have_write: %s" % self.have_write)
            dbgPrint(" - - need_write: %s" % self.need_write)
            dbgPrint(" - - buff_write: %s" % self.buff_write)
            dbgPrint(" - - buff_read:  %s" % self.buff_read)
            dbgPrint(" - - sock_obj:   %s" % self.sock_obj)

'''


from daemon import Daemon
import socket
import select
import time
import pdb

#多线程
from threading import Thread
from Queue import Queue

__all__ = ["nbNet", "sendData_mh"]
#DEBUG = True

from nbNetUtils import *

class nbNetBase(Thread):
    def __init__(self,thread_name,q):
        Thread.__init__(self)
        self.setName(thread_name)
        self.thread_queue = q        

    '''non-blocking Net'''
    def setFd(self, sock):
        """sock is class object of socket"""
        #dbgPrint("\n -- setFd start!")
        #申明一个STATE对象,STATE类见注释或nbNetUtils
        #默认state=‘accpet’
        tmp_state = STATE()
        #传入socket对象，完成初始化
        tmp_state.sock_obj = sock
        #将申明的state对象放入conn_state字典
        self.conn_state[sock.fileno()] = tmp_state
        #将conn_state字典放入queue中，线程间共享
        self.thread_queue.put(self.conn_state)
        #self.conn_state[sock.fileno()].printState()
        #dbgPrint("\n -- setFd end!")

#    def getSock(self,fd):
#        sock_state = self.thread_queue.get()[fd]
#        sock = sock_state.sock_obj
#        return sock
#
#    def getSockState(self.fd):
#        sock_state = self.thread_queue.get()
#        return sock_state

    def accept(self, fd): 
        """fd is fileno() of socket"""
        #dbgPrint("\n -- accept start!")
        #从conn_state字典中获取stat对象
        sock_state = self.conn_state[fd]
        #从stat对象中获取socket对象
        sock = sock_state.sock_obj
        
        conn_state
        sock = getSock(fd)
        #接收新的连接
        conn, addr = sock.accept()
        # set to non-blocking: 0，非阻塞模式
        conn.setblocking(0)
        #返回连接
        return conn
    
    def close(self, fd):
        """fd is fileno() of socket"""
        #pdb.set_trace()
        print "closing", fd, self.conn_state
        try:
            # cancel of listen to event
            #sock = self.conn_state[fd].sock_obj

            sock = getSock(fd)
            self.epoll_sock.unregister(fd)
            sock.close()
            self.conn_state.pop(fd)
            tmp_pipe = self.popen_pipe
            self.popen_pipe = 0
            tmp_pipe.close()
        except:
            #dbgPrint("Close fd: %s abnormal" % fd)
            pass
    #@profile
    def read(self, fd):
        """fd is fileno() of socket"""
        #pdb.set_trace()
        try:
            #sock_state = self.conn_state[fd]
            #conn = sock_state.sock_obj

            conn = getSock(fd)
            #如果需要读的内容已经读完，触发一个异常
            if sock_state.need_read <= 0:
                raise socket.error
            #读10字节
            one_read = conn.recv(sock_state.need_read)
            #dbgPrint("\tread func fd: %d, one_read: %s, need_read: %d" % (fd, one_read, sock_state.need_read))
            #如果没有读到内容，触发一个异常
            if len(one_read) == 0:
                raise socket.error
            # process received data
            #将一次读到的存入对象变量
            sock_state.buff_read += one_read
            #处理已读和未读的字节数
            sock_state.have_read += len(one_read)
            sock_state.need_read -= len(one_read)
            #sock_state.printState()

            # read protocol header
            '''
            定义一个协议头十个字节表示协议长度，判断协议头是否读完，读完将头十个字节转换为int
            如果int为0，或者小于0，表示协议体数据为空或者出错，触发异常
            正常大于0，将need_read设置为协议头定义的字节大小，清空buff
            '''
            if sock_state.have_read == 10:
                header_said_need_read = int(sock_state.buff_read)
                if header_said_need_read <= 0:
                    raise socket.error
                sock_state.need_read += header_said_need_read
                sock_state.buff_read = ''
                # call state machine, current state is read. 
                # after protocol header haven readed, read the real cmd content, 
                # call machine instead of call read() it self in common.
                #sock_state.printState()
                return "readcontent"
            elif sock_state.need_read == 0:
                # recv complete, change state to process it
                return "process"
            else:
                return "readmore"
        except (socket.error, ValueError), msg:
            try:
                if msg.errno == 11:
                    #dbgPrint("11 " + msg)
                    return "retry"
            except:
                pass
            return 'closing'
        

    #@profile
    def write(self, fd):
        #sock_state = self.conn_state[fd]
        #conn = sock_state.sock_obj

        conn = getSock(fd)
        #pdb.set_trace()
        
        if isinstance(sock_state.popen_pipe, file):
            try:
                output = sock_state.popen_pipe.read()
                #print output
            except (IOError, ValueError), msg:
                pass
            #have_send = conn.send("%010d%s" % (len(output), output))
            #todo

        else:
            last_have_send = sock_state.have_write
            try:
                # to send some Bytes, but have_send is the return num of .send()
                have_send = conn.send(sock_state.buff_write[last_have_send:])
                sock_state.have_write += have_send
                sock_state.need_write -= have_send
                if sock_state.need_write == 0 and sock_state.have_write != 0:
                    # send complete, re init status, and listen re-read
                    #sock_state.printState()
                    #dbgPrint('\n write data completed!')
                    return "writecomplete"
                else:
                    return "writemore"
            except socket.error, msg:
                return "closing"


    def run(self):
        while True:
            #dbgPrint("\nrun func loop:")
            # print conn_state
            #for i in self.conn_state.iterkeys():
                #dbgPrint("\n - state of fd: %d" % i)
                #self.conn_state[i].printState()
            #查询epoll对象，看是否有关注的event被触发
            epoll_list = self.epoll_sock.poll()
            #epoll_list是作为一个元组的列表返回（fileno,event code）
            for fd, events in epoll_list:
                #dbgPrint('\n-- run epoll return fd: %d. event: %s' % (fd, events))
                print self.conn_state
                print fd, events
                #通过conn_state字典查询被触发的socket状态
                sock_state = self.conn_state[fd]
                #判断是否是HUP事件，如果是将state置成“closing”
                if select.EPOLLHUP & events:
                    #dbgPrint("EPOLLHUP")
                    sock_state.state = "closing"
                #判断是否是ERR事件，如果是将state置成“closing”
                elif select.EPOLLERR & events:
                    #dbgPrint("EPOLLERR")
                    sock_state.state = "closing"
                #排除HUP和ERR事件后，将fd放入stat_machine
                self.state_machine(fd)

    def state_machine(self, fd):
        #time.sleep(0.1)
        #dbgPrint("\n - state machine: fd: %d, status: %s" % (fd, self.conn_state[fd].state))
        #获取socket_state的状态
        sock_state = self.conn_state[fd]
        #通过socket_state的状态，从socket method字典中获取对应的方法
        self.sm[sock_state.state](fd)

class nbNet(nbNetBase):
    def __init__(self, addr, port, logic):
        #dbgPrint('\n__init__: start!')
        #初始化存放stat对象的字典，key是fileno
        self.conn_state = {}
        #初始化一个socket，监听连接
        self.listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listen_sock.bind((addr, port))
        self.listen_sock.listen(10)
        #将listen_sock对象放入conn_state字典
        self.setFd(self.listen_sock)
        #初始化epoll，注册EPOLLIN事件
        self.epoll_sock = select.epoll()
        # LT for default, ET add ' | select.EPOLLET '
        self.epoll_sock.register(self.listen_sock.fileno(), select.EPOLLIN )
        self.logic = logic
        #socket method字典，状态和方法对应
        self.sm = {
            "accept" : self.accept2read,
            "read"   : self.read2process,
            "write"  : self.write2read,
            "process": self.process,
            "closing": self.close,
        }
        #dbgPrint('\n__init__: end, register no: %s' % self.listen_sock.fileno() )

    #@profile
    def process(self, fd):
        sock_state = self.conn_state[fd]
        #逻辑处理函数
        response = self.logic(fd, sock_state.buff_read)
        #pdb.set_trace()
        if response == None:
            conn = sock_state.sock_obj
            self.setFd(conn)
            self.conn_state[fd].state = "read"
            self.epoll_sock.modify(fd, select.EPOLLIN)
        else:  
            sock_state.buff_write = "%010d%s" % (len(response), response)
            sock_state.need_write = len(sock_state.buff_write)
            #sock_state.printState()
            #self.state_machine(fd)
            sock_state.state = "write"
            self.epoll_sock.modify(fd, select.EPOLLOUT)

             

    #@profile
    def accept2read(self, fd):
        #从accept中获取新的连接
        conn = self.accept(fd)
        #将新的连接注册为EPOLLIN
        self.epoll_sock.register(conn.fileno(), select.EPOLLIN)
        # new client connection fd be initilized 将新连接初始化为stat对象放入conn_state字典
        self.setFd(conn)
        # 将新初始化的stat对象的state置为‘read’
        self.conn_state[conn.fileno()].state = "read"
        # now end of accept, but the main process still on 'accept' status
        # waiting for new client to connect it.
        #dbgPrint("\n -- accept end!")

    #@profile
    def read2process(self, fd):
        """fd is fileno() of socket"""
        #pdb.set_trace()
        read_ret = ""
        try:
            #调用read方法，获取read返回状态
            read_ret = self.read(fd)
        except (Exception), msg:
            #dbgPrint(msg)
            read_ret = "closing"
        if read_ret == "process":
            # recv complete, change state to process it
            #sock_state.state = "process"
            self.process(fd)
        elif read_ret == "readcontent":
            pass
        elif read_ret == "readmore":
            pass
        elif read_ret == "retry":
            pass
        elif read_ret == "closing":
            self.conn_state[fd].state = 'closing'
            # closing directly when error.
            self.state_machine(fd)
        else:
            raise Exception("impossible state returned by self.read")

    #@profile
    def write2read(self, fd):
        try:
            write_ret = self.write(fd)
        except socket.error, msg:
            write_ret = "closing"

        if write_ret == "writemore":
            pass
        elif write_ret == "writecomplete":
            #写完成，重新将socket注册成EPOLLIN，state设置成'read'
            sock_state = self.conn_state[fd]
            conn = sock_state.sock_obj
            self.setFd(conn)
            self.conn_state[fd].state = "read"
            self.epoll_sock.modify(fd, select.EPOLLIN)
        elif write_ret == "closing":
            #dbgPrint(msg)
            self.conn_state[fd].state = 'closing'
            # closing directly when error.
            self.state_machine(fd)
    
counter = 0
if __name__ == '__main__':
    
    def logic(d_in):
        global counter
        counter += 1
        if counter % 100000 == 0:
            print counter, time.time()
        return("a")

    reverseD = nbNet('0.0.0.0', 9099, logic)
    reverseD.run()
