# -*- coding: utf-8 -*-

# success status
SUCCESS = { "status": "success", "description":"操作成功!","errorcode": 0}
LOGIN_SUCCESS = { "status": "success", "description":"登陆成功!","errorcode": 1}
FIND_NOTHING = { "status": "success", "description":"空空的欸!","errorcode": 2, "result_list":{}}

# error status
USER_EXIST = { "status": "error", "description":"该用户已存在!","errorcode": 101}
UNKNOW_ERROR = { "status": "error", "description":"未知错误!","errorcode": 102}
USER_PASSWORD_ERROR = { "status": "error", "description":"用户名或密码错误!","errorcode": 103}
