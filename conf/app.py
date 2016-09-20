import logging; logging.basicConfig(level=logging.INFO)
import asyncio, os, json, time
from datetime import datetime

from aiohttp import web

def index(request):
    return web.Response(body=b'<h1> html can only contain info in binary</h1>')

@asyncio.coroutine
def init(loop):
    app = web.Application(loop=loop)
    app.router.add_route('GET','/',index)
    srv = yield from loop.create_server(app.make_handler(),'127.0.0.1',9000)
    logging.info('server started at http://127.0.0.1:9000...')
    return srv

#create the connection pool

#can be reused, so will be used for many times. Thus, should be a coroutine
async def create_pool(loop, **kw):
	logging.info('creating a new connection??? or create a connection pool??')
	global __pool
	# aiomysql.create_pool always has the parameters **kw
	__pool = await aiomysql.create_pool(
		#**kw can be a dict but written in each item
		#thus, kw is a dict
		#get method let you get the value, if the key is not defined, return the default value
		host = kw.get('host','localhost'),
		port = kw.get('port', 3306),
		#directly looking for user, if user is not defined, this method will raise an exception??
		user = kw['user'],
		password = kw['password'],
		db = kw['db'],
		charset = kw.get('charset', 'utf-8'),
		autocommit = kw.get('autocommity', True),
		maxszie = kw.get('maxsize', 10),
		minszie = kw.get('minsize',1),
		loop = loop
	)

#any function that will be used for many times should be coroutine
# parameters defined in the beginning of function definition is not kw. it defined a default value
async def select(sql, args, size = None):
	#should be something like logging.info, but which level is this??
	#logging.info can only accept string
	log(sql, args)
	#use the pool defined in create_pool
	#__pool = await is only defined after the (cancel???) of the function of await and is None???
	global __pool
	# with will close the connection after the end of indention
	with (await __pool) as conn:
		#mysql's functions
		# to use mysql in python, you should have connection first then cursor
		cur = await conn.cursor(aiomysql.DictCursor)
		#args should be an arguments, but empty () will be defined as tuple
		await cur.execute(sql.replace('?', '%s'), args or ())
		if size:
			rs = await cur.fetchmany(size)
		else:
			rs = await cur.fetchall()
		#thus, ra will return a object that can be called by len()?
		logging.info('rows returned: %s'% len(rs))
		return rs

#only coroutine could use coroutine?
async def execute(sql, args):
	#why not log args???
	log(sql)
	#why not globalize __pool??
	global __pool
	with (await __pool) as conn:
		try:
		# why not use aiomysql.DictCursor??
		cur = await conn.cursor(aiomysql.DictCursor)
		await cur.execute(sql.replace('?','%s'), args)
		affected = cur.rowcount
		# why in select function, close step was not used
		# with function should contain the function to close the connection (__pool) but not cur
		await cur.close()
		except BaseException as e:
			raise
		return affected





loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()


