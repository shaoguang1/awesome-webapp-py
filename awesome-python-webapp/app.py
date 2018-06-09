#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging; logging.basicConfig(level=logging.INFO)
#设置日志等级，默认是WARNING.只有指定级别或更高级的才会被追踪记录
import asyncio, os, json, time
from datetime import datetime
from aiohttp import web
from jinja2 import Environment, FileSystemLoader

from coroweb import add_routes, add_static
import orm
from config import configs
from handlers import cookie2user, COOKIE_NAME
# def index(request):
#     #返回web的请求
#     return web.Response(body=b'<h1>Awesome</h1>')

def init_jinja2(app, **kw):
    logging.info('init jinja2 ...')
    options = dict(
        autoescape = kw.get('autoescape', True),
        block_start_string = kw.get('block_start_string', '{%'),
        block_end_string = kw.get('block_end_string', '%}'),
        variable_start_string = kw.get('variable_start_string', '{{'),
        variable_end_string = kw.get('variable_end_string', '}}'),
        auto_reload = kw.get('auto_reload', True)
    )
    path = kw.get('path', None)
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates') #返回的是.py文件的绝对路径
    logging.info('set jinja2 template Path:%s' % path)
    env = Environment(loader=FileSystemLoader(path), **options)
    filters = kw.get('filters', None)
    if filters is not None:
        for name, f in filters.items():
            env.filters[name] =f
    app['__templating__'] = env

'''
middleware

前面的RequestHandler对于URL做了一系列的处理，但是aiohttp框架最终需要的是返回web.Response对象，
实现这一步，这里引入aiohttp框架的web.Application()中的middleware参数。
简介：middleware是一种拦截器，一个URL在被某个函数处理前，可以经过一系列的middleware的处理。
一个middleware可以改变URL的输入、输出，甚至可以决定不继续处理而直接返回。
middleware的用处就在于把通用的功能从每个URL处理函数中拿出来，集中放到一个地方。
当创建web.appliction的时候，可以设置middleware参数，而middleware的设置是通过创建一些middleware factory(协程函数)。
这些middleware factory接受一个app实例，一个handler两个参数，并返回一个新的handler。
'''
#记录URL日志的logger
async def logger_factory(app, handler):
    async def logger (request):
        logging.info('Request:%s %s' % (request.method, request.path))
        return (await handler(request))
    return logger

async def data_factory(app, handler):
    async def parse_data(request):
        if request.method == 'POST':
            if request.content_type.startswith('application/json'):
                request.__data__ = await request.json()
                logging.info('request json:%s' % str(request.__data__))
            elif request.content_type.startswith('application/x-www-form-urlencoded'):
                request.__data__ = await request.post()
                logging.info('request form:%s' % str(request.__data__))
        return (await handler(request))
    return parse_data
#response这个middleware把返回值转换为web.Response对象再返回，以保证满足aiohttp的要求：
async def response_factory(app, handler):
    async def response(request):
        logging.info('Response handler...')
        r = await handler(request)
        if isinstance(r, web.StreamResponse):
            return r
        if isinstance(r, bytes):
            resp = web.Response(body=r)
            resp.content_type = 'application/octet-stream'
            return resp
        if isinstance(r, str):
            if r.startswith('redirect:'):
                return HTTPFound(r[9:])
            resp = web.Response(body=r.encode('utf-8'))
            resp.content_type = 'text/html;charset=utf-8'
            return resp
        if isinstance(r, dict):
            template = r.get('__template__')
            if template is None:
                resp = web.Response(body=json.dumps(r, ensure_ascii=False, default=lambda o: o.__dict__).encode('utf-8'))
                resp.content_type = 'application/json;charset=utf-8'
                return resp
            else:
                resp = web.Response(body=app['__templating__'].get_template(template).render(**r).encode('utf-8'))
                resp.content_type = 'text/html;charset=utf-8'
                return resp
        if isinstance(r, int) and r >= 100 and r < 600:
            return web.Response(r)
        if isinstance(r, tuple) and len(r) == 2:
            t, m = r
            if isinstance(t, int) and t >= 100 and t < 600:
                return web.Response(t, str(m))
        #default
        resp = web.Response(body=str(r).encode('utf-8'))
        resp.content_type = 'text/plain;cherset=utf-8'
        return resp
    return response
#datetime_filter()函数实质是一个拦截器,把一个浮点数转换成日期字符串。
def datetime_filter(t):
    delta = int(time.time()-t)
    if delta < 60 :
        return u'一分钟前'
    if delta < 3600 :
        return u'%s分钟前' % (delta // 60)
    if delta < 86400 :
        return u'%s小时前' % (delta // 3600)
    if delta < 604800 :
        return u'%s天前' % (delta // 86400)
    dt = datetime.fromtimestamp(t)
    return u'%s年%s月%s日' % (dt.year, dt.month, dt.day)

# @asyncio.coroutine
async def init(loop):
    await orm.create_pool(loop=loop, host='127.0.0.1', port=3306, user='www-data', password='www-data', db='awesome')
    #创建web应用    创建一个循环类型是消息循环的web应用对象
    # app = web.Application(loop=loop)
    # app.router.add_route('GET','/',index)

    #添加middleware、jinja2模板和自注册的支持
    app = web.Application(loop=loop, middlewares=[
        logger_factory, response_factory
    ])
    init_jinja2(app, filters=dict(datetime=datetime_filter))
    add_routes(app, 'handlers')
    add_static(app)
     #调用子协程：创建一个TCP服务器，绑定到“0.0.0.0：9000”socket，并返回一个服务器对象
    srv = await loop.create_server(app.make_handler(),'127.0.0.1',9000)
    logging.info('server started at http://127.0.0.1:9000...')
    return srv

loop = asyncio.get_event_loop()  #loop收一个消息循环
loop.run_until_complete(init(loop))  #在消息循环中执行协程
loop.run_forever()

