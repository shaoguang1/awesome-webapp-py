#! /usr/bin/env python3
# -*- coding:utf-8 -*-

import asyncio, os, inspect, logging, functools

from urllib import parse
from aiohttp import web
from apis import APIError

def get(path):
    '''
    Define decorator @get('/path')
    '''
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)
        wrapper.__method__ = 'GET'
        wrapper.__route__ = path
        return wrapper
    return decorator

def post(path):
    '''
    Define decorator @post('/path')
    '''
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)
        wrapper.__method__ = 'POST'
        wrapper.__route__ = path
        return wrapper
    return decorator
#运用inspect模块，创建几个函数用以获取URL处理函数与request参数之间的关系
def get_required_kw_args(fn):#收集没有默认值的命名关键字参数
    args = []
    params = inspect.signature(fn).parameters#inspect模块是用来分析模块，函数
    for name, param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY and param.default == inspect.Parameter.empty:
            args.append(name)
    return tuple(args)

def get_name_kw_args(fn):#获取命名关键字参数
    args = []
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY :
            args.append(name)
    return tuple(args)

def has_name_kw_args(fn):#判断有没有命名关键字参数
    
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY :
            return True

def has_var_kw_args(fn): #判断有没有关键字参数
    
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY :
            return True
 
def has_request_arg(fn):#判断是否含有名叫'request'参数，且该参数是否为最后一个参数
    sig = inspect.signature(fn)
    params = sig.parameters
    found = False
    for name, param in params.items():
        if name == 'request':
            found = True
            continue
        if found and (param.kind != inspect.Parameter.VAR_POSITIONAL and param.kind != inspect.Parameter.KEYWORD_ONLY and param.kind != inspect.Parameter.VAR_KEYWORD):
            raise ValueError('request parameter must be the last named parameter in function:%s%s ' % (fn.__name__, str(sig)))
    return found
#定义RequestHandler,正式向request参数获取URL处理函数所需的参数
class RequestHandler(object):
    def __init__(self, app, fn, *args, **kwargs):#接受app参数
        self._app = app
        self._func = fn
        self._has_request_arg = has_request_arg(fn)
        self._has_var_kw_arg = has_var_kw_args(fn)
        self._has_named_kw_arg = has_name_kw_args(fn)
        self._named_kw_args = get_name_kw_args(fn)
        self._required_kw_args = get_required_kw_args(fn)

    async def __call__(self, request):#__call__这里要构造协程
        kw= None
        if self._has_var_kw_arg or self._named_kw_args or self._required_kw_args:
            if request.method == 'POST':
                if not request.content_type: #查询有没提交数据的格式（EncType）
                    return web.HTTPBadRequest('Missing content-type')#这里被廖大坑了，要有text
                ct = request.content_type.lower()#小写
                if ct.startswith('application/json'):
                    params = await request.json() #Read request body decoded as json.
                    if not isinstance(params, dict):
                        return web.HTTPBadRequest('json body must be object.')
                    kw = params
                elif ct.startswith('application/x-www-from-urlencoded') or ct.startswith('multipart/form-data'):
                    params = await request.post()
                    kw = dict(**params)
                else:
                    return web.HTTPBadRequest('unsupported content-type:%s' % request.content_type)
            if request.method == 'GET':
                qs = request.query_string
                if qs:
                    kw = dict()
                    for k, v in parse.parse_qs(qs,True).items():
                        kw[k] = v[0]
        if kw is None:
            kw = dict(**request.match_info)
        else:#当函数参数没有关键字参数时，移去request除命名关键字参数所有的参数信息
            if not self._has_var_kw_arg and self._named_kw_args:
                copy = dict()
                for name in  self._named_kw_args:
                    if name in kw:
                        copy[name] = kw[name]
                kw = copy
            for k, v in request.match_info.items():#检查命名关键参数
                if k in kw:
                    logging.warning('duplicate arg name in named arg and kw args: %s ' % k)
                kw[k] = v
        if self._has_request_arg:
            kw['request'] = request
        if self._required_kw_args:#假如命名关键字参数(没有附加默认值)，request没有提供相应的数值，报错
            for name in self._required_kw_args:
                if not name in kw:
                    return web.HTTPBadRequest('missing argument:%s' % name)
        logging.info('call with args:%s' % str(kw))
        try:
            r = await self._func(**kw)
            return r
        except APIError as e:
            return dict(error=e.error, data=e.data, message=e.message)
#添加静态文件夹的路径：
def add_static(app):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    app.router.add_static('/static/', path)
    logging.info('add static %s => %s' % ('/static/', path))
#由于我们现在要建立的的Web框架基于aiohttp框架，所以需要再编写一个add_route函数，用来注册一个URL处理函数，主要用来验证函数是否有包含URL的响应方法与路径信息，以及将函数变为协程。
def add_route(app,fn):
    method = getattr(fn, '__method__', None)
    path = getattr(fn, '__route__',None)
    if path is None or method is None:
        raise ValueError('@get or @post not defined in %s .' % str(fn))
    if not asyncio.iscoroutinefunction(fn) and not inspect.isgeneratorfunction(fn):
        fn = asyncio.coroutine(fn)
    logging.info('add route %s %s => %s(%s) ' % (method, path, fn.__name__, ','.join(inspect.signature(fn).parameters.keys())))
    app.router.add_route(method, path, RequestHandler(app, fn))
#可以批量注册的函数，预期效果是：只需向这个函数提供要批量注册函数的文件路径，新编写的函数就会筛选，注册文件内所有符合注册条件的函数。
def add_routes(app, module_name):
    n = module_name.rfind('.')
    if n == (-1):
        mod = __import__(module_name, globals(), locals())
    else:
        name = module_name[n+1:]
        mod = getattr(__import__(module_name[:n], globals(), locals(), [name]), name)
    for attr in dir(mod):
        if attr.startswith('_'):
            continue
        fn = getattr(mod, attr)
        if callable(fn):
            method = getattr(fn, '__method__', None)
            path = getattr(fn, '__route__', None)
            if method and path:
                add_route(app,fn)