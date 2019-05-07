# 关于站内搜索的说明

## 概述
使用了elasticsearch工具用来实现站内Post搜索的功能,故而需要在程序启动之前先部署好该工具

## 安装
操作系统环境需要事先安装elasticsearch工具，可以通过下载二进制包进行安装，在MacOS上，输入：
```bash
$ brew install elasticsearch
```
进行安装

## 搜索环境构建
1. 独立启动elasticsearch到后台静默运行
```bash
$ elasticsearch &
```

2. 构建当前数据库中Post表的索引到elasticsearch中
```bash
$ flask shell
>>> Post.reindex()
>>> exit()
```

## 测试环境
- 以上两步就建立了搜索环境，索引更新是与数据库构建同步触发的，不需要手动调用

- 在测试环境中，如果退出来elasticsearch工具，则下次启动仍需要按步骤重新建立搜索环境

- 在测试环境中，如果需要删除索引
```bash
# flask shell
>>> Post.remove_all()
>>> exit()
```
