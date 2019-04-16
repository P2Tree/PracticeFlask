## 原始的babel命令

- 提取代码中的需要翻译的字段并写入messages.pot，写入babel.cfg当前路径

`$ pybabel extract -F babel.cfg -k _l -o messages.pot .`

- 通过messages.pot生成语言目录和对应.po文件，这里是中文

`pybabel init -i messages.pot -d app/translations -l zh_CN`

- 需要修改.po文件，进行人工翻译

- 编译.po文件

`pybabel compile -d app/translations`

- 当重新修改代码，需要进一步翻译时，
第一条命令是更新.pot文件:
`pybabel extract -F babel.cfg -k  _l -o messages.pot .`
第二条是智能合并，生产新的.po文件:
`pybabel update -i messages.pot -d app/translations`
第三条是重新编译.po文件，生成.mo文件：
`pybabel compile -d app/translations`

## 另外，app/cli.py中编写了以上命令的简化命令，并通过click融合到flask命令中
- 初始化语言目录和.po文件，添加新语言时调用

`flask translate init LANG`

`LANG`为对应的语言
每次调用init命令时会同步调用extract命令

- 更新语言库，生成新的.po文件

`flask translate update`

- 编译语言库，生成.mo文件

`flask translate compile`

