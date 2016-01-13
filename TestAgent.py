#! /usr/bin/env python
import commands
import socket
import time
import os
import multiprocessing
import uuid
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer

#HTTPServer的监听端口
PORT=12345

class HttpHandler(BaseHTTPRequestHandler):
    tmpfile=''
    #处理POST消息
    def do_POST(self):
        print self.path
        content_len = int(self.headers.getheader('content-length',0))
        #获取timeout
        timeout = int(self.headers.getheader('timeout',0))
        if timeout==0:
            timeout=5
        #解析消息并存储为文件
        script=self.rfile.read(content_len)
        x=uuid.uuid4()
        self.tmpfile="."+str(x.int)
        fd=open(self.tmpfile,'w')
        fd.write(script)
        fd.close()
        os.system("chmod +x "+self.tmpfile)
        script="./"+self.tmpfile
        #执行脚本
        self.ExecuteScript(script,timeout)
        
    def ExecuteScript(self,script,timeout=5):
        #启动另一个进程执行脚本
        p=multiprocessing.Process(target=self.ScriptWorker,args=(script,))
        p.start()
        i=0
        while i<timeout:
            if(not p.is_alive()):
                return "successful"
            else:
                time.sleep(1)
            i=i+1
        #超时的话终止进程并杀掉执行任务的进程
        p.terminate()
        os.system("kill -9 "+str(p.pid))
        self.send_error(400,"time out")
        self.request.shutdown(socket.SHUT_RDWR)
        self.request.close()
        #删除临时文件
        if self.tmpfile != '':
            os.system("rm "+self.tmpfile)
        self.tmpfile=''
        
    def ScriptWorker(self,script):
        #执行脚本，返回状态码和输出
        (status,result)=commands.getstatusoutput(script)
        print script
        print result
        #如果成功返回200，如果失败返回400
        if status == 0:
            self.send_response(200)
        else:
            self.send_response(400)
        self.send_header('Content-type','text/html')
        self.end_headers()
        self.wfile.write(result)
        #删除临时文件
        if self.tmpfile != '':
            os.system("rm "+self.tmpfile)
        self.tmpfile=''
        
if __name__=='__main__':
    os.system('rm .*')
    server_address=('0.0.0.0',PORT)
    http_server=HTTPServer(server_address,HttpHandler)
    http_server.serve_forever()
        
