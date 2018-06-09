#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'shg'

' url handlers '
from aiohttp import web

import re, time, json, logging, hashlib, base64, asyncio
from coroweb import get, post
from model import User, Comment, Blog, next_id
from apis import APIValueError, APIResourceNotFoundError, APIError
from config import configs

COOKIE_NAME = 'awessession'
_COOKIE_KEY = configs.session.secret

def user2cookie(user, max_age):
    '''
    generate cookie str by user.
    '''
    #build cookie sting by : id-expires-sha1
    expires = str(time.time() +max_age)
    s = '%s-%s-%s-%s' % (user.id, user.passwd, expires, _COOKIE_KEY)
    L = [user.id, expires, hashlib.sha1(s.encode('utf-8')).hexdigest()]
    return '-'.join(L)

@asyncio.coroutine
def cookie2user(cookie_str):
    '''
    parse cookie and load user if cookie is walid
    '''
    if not cookie_str:
        return None
    try:
        L = cookie_str.split('-')
        if len(L) !=3:
            return None
        uid, expires, sha1 = L
        if expires < time.time():
            return None
        user = yield from User.findAll(uid)
        if user is None:
            return None
        s = '%s-%s-%s-%s' % (uid, user.passwd, expires, _COOKIE_KEY)
        if sha1 != hashlib.sha1(s.encode('utf-8')).hexdigest():
            return None
        user.passwd = '******'
        return user
    except Exception as e:
        logging.exception(e)
        return None

@get('/')
def index(request):
    # users = await User.findAll()
    # return {
    #     '__template__' : 'test.html',
    #     'users': users
    # }
    summary = 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'
    blogs = [
        Blog(id='1', name='Test Blog', summary=summary, created_at=time.time()-120),
        Blog(id='2', name='Something New', summary=summary, created_at=time.time()-3600),
        Blog(id='3', name='Learn Swift', summary=summary, created_at=time.time()-7200)
    ]
    return {
        '__template__': 'blogs.html',
        'blogs': blogs
    }

@get('/api/users')
async def api_get_users():
    users = await User.findAll()
    for u in users:
        u.passwd = '888888'
    return dict(users=users)

@get('/register')
def register():
    # users = await User.findAll()
    return {
        '__template__' : 'register.html'
        
    }

_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_RE_PASSWD = re.compile(r'^[0-9a-f]{40}$')

@post('/api/users')
def api_register_user(*,email, name, passwd):
    
    logging.info('%s' % name)
    if not name or not name.strip():
        logging.info('%s' % name)
        # raise APIValueError(name)
    if not email or not  _RE_EMAIL.match(email):
        raise APIValueError('email')
    if not passwd or not _RE_PASSWD.match(passwd):
        raise APIValueError('passwd')
    users = yield from User.findAll('email=?', [email])
    if len(users) > 0:
        raise APIError('register:failed', 'email', 'Email is already in use.')
    uid = next_id()
    shal_passwd = '%s:%s' % (uid, passwd)
    user = User(
        id=uid, 
        name=name.strip(), 
        email=email, 
        passwd=hashlib.sha1(shal_passwd.encode('utf-8')).hexdigest(), 
        image='http://www.gravatar.com/avatar/%s?d=mm&s=120' % hashlib.md5(email.encode('utf-8')).hexdigest()
        )
    yield from user.save()
    #make session cookie
    r = web.Response()
    r.set_cookie(COOKIE_NAME,user2cookie(user,86400), max_age=86400, httponly=True)
    user.passwd = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user,ensure_ascii=False).encode('utf-8')
    return r