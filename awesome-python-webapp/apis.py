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

