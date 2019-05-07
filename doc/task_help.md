#关于后台任务的说明

现在的后台任务基于Redis和rq工具，所以需要在系统上安装并运行。

## 安装Redis
- Mac: 
```bash
$ brew install redis-server
```
- Linux: 
```bash
$ sudo apt-get install redis-server
```

## 安装rq
```bash
$ pip install rq
```

## 需要先启动Redis和rq
```bash
$ redis-server &
$ rq worker microblog-tasks
```

## 最后启动服务器就可以了
```bash
$ flask run
```