#python3
# -*- coding: utf-8 -*-
from flask import Flask, request,session, redirect, g
import base64
import os
dirname = os.path.abspath(os.path.dirname(__file__))
# src= dirname + "/upload"
import sys
#sys.path.append(r'/opt/app/MANAGER/AnsibleDeployProgram/ansibleScript')
# sys.path.append(src)
#import cx_Oracle
#import FilesUpload.upload as fsup
#import yaml
import urllib.request,ssl, urllib,json
import urllib;

print("111")
app = Flask(__name__)
#app.config.from_pyfile("settings.py")


@app.route('/token/validate', methods=['POST','GET'])
def validate():
    #print("222")
    #token_args=request.values.get("token") or "token is not exist"
    #print("token_args:"+token_args)
    #token=app.config['TOKEN']

    import re
    r_url=str(request.url)
    print(r_url)
    pattern = re.compile(r'redirect=(.*)')
    matcher = re.search(pattern, r_url)
    encode_redirect_data = str(matcher.group(1))
    redirect_data = urllib.parse.unquote(encode_redirect_data)
    
     
    #redirect = request.values.get("redirect")
    #redirect = "https://abc"
    #print(str(redirect))
    #pm_redirect=base64.b64encode(redirect.encode('UTF-8'))
    #jm_redirect = base64.b64decode(pm_redirect).decode('UTF-8')
    #print(str(jm_redirect))
    #redirect_data = str(jm_redirect)

    print("redirect_data")
    print(redirect_data)

    #if token_args == token:
    if True:
        return redirect(redirect_data)
    else:
        return "Please check token!"


@app.route('/api/task', methods=['POST','GET'])
def get_task():
    remotes_args = request.values.get("hostsIp") or "hostsIp is not exist"
    username_args = request.values.get("username") or "username is not exist"
    modules_args = request.values.get("module") or "modules is not exist"
    args_args = request.values.get("args") or "args is not exist"
#    conn_mysql_audit(remotes_args, username_args, modules_args, args_args)
    #ansible_server = AnsibleServer()
    #return ansible_server.get_task()
    return "get_task"


@app.route('/', methods=['POST', 'GET'])
def web_init():
    #return fsup.init_web()
    return "web_init"


@app.route('/upload', methods=['POST','GET'])
def web_upload():
    modules_args = 'upload'
#    conn_mysql_audit('null', 'null', modules_args, 'null')
    #return fsup.upload()
    return "web_upload"


@app.route('/show',methods=['GET'])
def web_show():
    modules_args = 'show'
    conn_mysql_audit('null', 'null', modules_args, 'null')
    #return fsup.show()
    return "web_show"


@app.route('/remove', methods=['GET'])
def web_removeFile():
    modules_args = 'remove'
    conn_mysql_audit('null', 'null', modules_args, 'null')
    #return fsup.removeFile()
    return "web_removeFile"


@app.route('/download', methods=['POST'])
def web_download():
    modules_args = 'download'
    conn_mysql_audit('null', 'null', modules_args, 'null')
    #return fsup.download()
    return "web_download"

def conn_mysql_audit(remotes_args, username_args, modules_args, args_args):
    
    with open(dirname + '/ansibleScript/ansible_setting.yaml') as yml:
        load = yaml.load(yml)
    data = load[0]
    connOracleInfo = data['sqlInfo']
    connSqlAudit = cx_Oracle.connect(connOracleInfo)
    #connSqlAudit = cx_Oracle.connect('midmon/midmon@10.6.183.145:1521/open')
    cursor = connSqlAudit.cursor()
    values = {'REMOTES': remotes_args, 'USERNAME': username_args, 'MODULES': modules_args, 'ARGS': args_args}
    sqlInsertExecUrlInfo = 'insert into AUTO_AUDIT_ANSIBLE(REMOTES,USERNAME,MODULES,ARGS) values(:REMOTES,:USERNAME,:MODULES,:ARGS)'
    cursor.execute(sqlInsertExecUrlInfo, values)
    connSqlAudit.commit()
    cursor.close()


if __name__ == '__main__':
    #app.run(host='0.0.0.0',threaded=True, debug=True,ssl_context='adhoc')
    app.run(host='127.0.0.1',threaded=True, debug=True)

