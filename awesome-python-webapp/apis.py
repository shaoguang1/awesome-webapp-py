#! /usr/bin/ python3 
# -*- coding:utf-8 -*-

"""
json api definition
"""

import json, logging, inspect, functools

class APIError(Exception):
    '''
    the base apierror which contains error(required), data(optional) and message(optional).
    '''
    def __init__(self, error, data='', message='', *args, **kwargs):
        super(APIError, self).__init__(message)
        self.error = error
        self.data = data
        self.message = message

class APIValueError(APIError):
    '''
    indicate the input value has error or invalid . the data specifies the error field of input form.. 
    '''
    def __init__(self,field, message='', *args, **kwargs):
        super(APIValueError,self).__init__('value:invalid', field,message)

class APIResourceNotFoundError(APIError):
    '''
    indicate the resource was not found . the data specifies the resource name.
    '''
    def __init__(self,field, message='', *args, **kwargs):
        super(APIResourceNotFoundError,self).__init__('value:notfount', field,message)


class APIPermissionError(APIError):
    '''
    indicate the api has no permission.
    '''
    def __init__(self, message='', *args, **kwargs):
        super(APIPermissionError,self).__init__('permission:forbidden', 'permission',message)

class Page(object):
    def __init__(self, item_count, page_index=1, page_size=10, *args, **kwargs):#参数依次是：数据库博客总数，初始页，一页显示博客数
        self.item_count = item_count
        self.page_size = page_size
        self.page_count = item_count // page_size + (1 if item_count % page_size > 0 else 0)
        if (item_count == 0) or (page_index>self.page_count):
            self.offset = 0
            self.limit = 0
            self.page_index = 1
        else:
            self.page_index = page_index
            self.offset = self.page_size * (page_index - 1)#当前页数，应从数据库的那个序列博客开始显示
            self.limit = self.page_size#当前页数，应从数据库的那个序列博客结束像素
        self.has_next  = self.page_index < self.page_count #有否下一页
        self.has_previous = self.page_index >1#有否上一页

    def __str__(self):
        return 'item_count:%s, page_count:%s, page_index:%s, page_size:%s,offset:%s, limit:%s' % (self.item_count, self.page_count, self.page_index, self.page_size, self.offset, self.limit)

        __repr__ = __str__