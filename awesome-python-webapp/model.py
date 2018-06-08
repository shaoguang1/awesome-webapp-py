
import time, uuid

from orm import Model, StringField, IntegerField, BooleanField, FloatField, TextField

# @time 2015-02-10 
#     @method next_id() uuid4()  make a random UUID 得到一个随机的UUID 
#     如果没有传入参数根据系统当前时间15位和一个随机得到的UUID 填充3个0 组成一个长度为50的字符串
def next_id():
    return '%015d%s000' % (int(time.time()*1000), uuid.uuid4().hex)

class User(Model):
    __table__ = 'users'

    id = IntegerField(primary_key = True, default=next_id, )
    email = StringField(ddl='varchsr(50)')
    passwd = StringField(ddl='varchsr(50)')
    admin = StringField(ddl='varchar(50)')
    name = StringField(ddl='varchsr(50)')
    image = StringField(ddl='varchsr(50)')
    created_at = FloatField(default=time.time)

class Blog(Model):
    __table__ = 'blogs'

    id = IntegerField(primary_key = True, default=next_id, )
    user_id = StringField(ddl='varchsr(50)')
    user_name = StringField(ddl='varchsr(50)')
    user_image = StringField(ddl='varchar(500)')
    name = StringField(ddl='varchsr(50)')
    summary = StringField(ddl='varchsr(50)')
    content = TextField()
    created_at = FloatField(default=time.time)

class Comment(Model):
    __table__ = 'comments'

    id = IntegerField(primary_key = True, default=next_id, )
    user_id = StringField(ddl='varchsr(50)')
    blog_id = StringField(ddl='varchsr(50)')
    user_name = StringField(ddl='varchar(50)')
    user_image = StringField(ddl='varchsr(500)')
    content = TextField()
    created_at = FloatField(default=time.time)

