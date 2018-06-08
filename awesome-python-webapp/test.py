
import orm, asyncio, sys
from model import User, Blog, Comment
# @asyncio.coroutine
# def destory_pool():
#     global __pool
#     if __pool is not None :
#         __pool.close()
#         yield from __pool.wait_closed()


async def test(loop,):
    await orm.create_pool(loop=loop,user='www-data',password='www-data', db='awesome')
    u = User(name='test',email='test@example.com', passwd='123456',image='blank')
    await u.save()
    # await destory_pool()
# 获取EventLoop:
loop = asyncio.get_event_loop()
#把协程丢到EventLoop中执行
loop.run_until_complete(test(loop))
#关闭EventLoop
loop.close()
if loop.is_closed():
    sys.exit(0)
    
import mysql.connector

conn = mysql.connector.connect(user='roop',password='www-data', database='awesome')
cursor = conn.cursor()
cursor.execute('select * from users')
data=cursor.fetchall()
print(data)
