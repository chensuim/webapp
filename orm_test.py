import pymysql
import logging; logging.basicConfig(level=logging.INFO)
conn = pymysql.connect(host = 'localhost', port =3306, user = 'root', password='', database = 'test')

def sql_var(var):
	return "'%s'"%var if isinstance(var,str) else "%s"%var


class ModelMetaclass(type):

	def __new__(cls, name, bases, attrs):
		if name=='Model':
			return type.__new__(cls, name, bases, attrs)
		logging.info('new model: %s '%(name))
		# colletall fields into mappings, those field are not seperated attrs anymore
		mappings = dict()
		not_primary = []
		primary_key = None
		for k,v in attrs.items():
			if isinstance(v, Field):
				logging.info('found a field, %s:%s'%(k,v))
				mappings[k] = v
				if v.primary_key:
					if primary_key:
						raise RuntimeError('Duplicated primary key')
					primary_key = k
				else:
					not_primary.append(k)

		if not primary_key:
			raise RuntimeError('no primary key')

		for k in mappings.keys():
			attrs.pop(k)

		attrs['__mappings__'] = mappings
		attrs['__tableName__'] = name
		attrs['__primaryKey__'] = primary_key
		attrs['__notPrimary__'] = not_primary
		not_primary = ','.join(list(map(lambda f:'`%s`'%f,not_primary)))
		attrs['__select__'] = 'SELECT `%s`, %s  FROM `%s` WHERE ?'%(primary_key, not_primary,name)
		attrs['__get__'] = 'SELECT `%s`, %s  FROM `%s` WHERE `%s` = ?'%(primary_key, not_primary,name, primary_key)
		attrs['__insert__'] = 'INSERT INTO `%s` (?) VALUES (?)'%name
		attrs['__update__'] = 'UPDATE `%s` SET ? WHERE ?'%name
		attrs['__deletesql__'] = 'DELETE FROM `%s` WHERE ?'%name 
		attrs['__create__'] = 'CREATE TABLE %s (?)'%name
		attrs['__drop__'] = 'DROP TABLE %s'%name
		return type.__new__(cls, name, bases, attrs)

class Field:
	def __init__(self, name, column_type, primary_key, default):
		self.name = name
		self.column_type = column_type
		self.primary_key = primary_key
		self.default = default

	def __str__(self):
		return '<%s, %s:%s>'%(self.__class__.__name__, self.column_type, self.name)

class StringField(Field):
	def __init__(self, name = None, primary_key = False, default = None, ddl = 100):
		super().__init__(name, 'varchar(%s)'%(str(ddl)),primary_key,default)

class IntegerField(Field):
	def __init__(self, name = None, primary_key = False, default = None, ddl = 100):
		super().__init__(name, 'int(%s)'%(str(ddl)), primary_key, default)



# instance of User class
# how to avoid an instance to contain a non-exist attr????


# after establishing, insert

#insert, delete
# 实例方法
def execute(sql):
	#log(sql, args)
	global conn
	cur = conn.cursor()
	cur.execute(sql)
	affected = cur.rowcount
	cur.close()
	logging.info('executed %s'%sql)
	return affected

#updating, based on primary key
#实例方法
#user.update(name = '????')
def update(sql, args, values, posargs, posvalues):
	log(sql, args, posargs)
	global conn
	cur = conn.cursor()
	cur.execute(sql.replace('?','%s'),(args, values, posargs, posvalues))
	affected = cur.rowcount
	cur.close()
	logging.info('updated %s'%args)
	return affected

# get User based on primary key
#class方法
#User.get('???')
def create_instance(sql, size = None):
	#log(sql,value)
	global conn
	cur = conn.cursor()
	cur.execute(sql)
	if not size:
		rs = cur.fetchall()
	else:
		rs = cur.fetchmany(size)
	cur.close()
	return rs


# find some User based on key


# create table
def execute_table(sql):
	#logging.info ('%s'%(sql, args))sql.replace('?', '%s'),(args)
	global conn
	cur = conn.cursor()
	cur.execute(sql)
	cur.close()
	return True

class Model(dict, metaclass = ModelMetaclass):

	def __init__(self, **kw):
		#established a dict
		super().__init__(**kw)


	def getValueOrDefault(self, key):
		value = self.get(key,None)
		if value is None:
			# __mappings__ will be defined later
			field = self.__mappings__[key]
			if field.default is not None:
				value = field.default() if callable(field.default) else field.default
				logging.debug('using default value for %s:%s'%(key, str(value)))
				self[key] = value
		return value

	@classmethod
	def create(cls):
		args = []
		args.append('%s %s primary key'%(cls.__primaryKey__, cls.__mappings__[cls.__primaryKey__].column_type))
		for i in cls.__notPrimary__:
			args.append('%s %s'%(i, cls.__mappings__[i].column_type))
		args = ','.join(args)
		sql = cls.__create__.replace('?','%s')
		sql = sql%args
		if (execute_table(sql)):
			logging.info('created table: %s'%cls.__tableName__)
			return True


	@classmethod
	def drop(cls):
		sql = cls.__drop__
		if (execute_table(sql)):
			logging.info('dropped table: %s'%cls.__tableName__)
			return True

	@classmethod
	def to_get(cls, value):
		sql = cls.__get__.replace('?','%s')
		sql = sql%value
		rs = create_instance(sql)
		if len(rs)==0:
			logging.info('cannot find instance by primary key : %s'%value)
			return None
		rs = rs[0]
		result = cls()
		result[cls.__primaryKey__] = rs[0]
		for i in range(len(cls.__notPrimary__)):
			result[cls.__notPrimary__[i]] = rs[i+1] 
		logging.info('got instance id:%s'%value)
		return result

	@classmethod
	def find(cls, size = None, **args):
		sql = cls.__select__.replace('?','%s')
		values = []
		for k,v in args.items():
			values.append("`%s` = %s"%(k,sql_var(v)))
		sql = sql%('AND'.join(values))
		rs = create_instance(sql, size)
		if len(rs)==0:
			logging.info('cannot find instance by sql : %s'%sql)
			return None
		rows = len(rs)
		all_results = []
		for j in range(rows):
			result = cls()
			result[cls.__primaryKey__] = rs[j][0]
			for i in range(len(cls.__notPrimary__)):
				result[cls.__notPrimary__[i]] = rs[j][i+1]
			all_results.append(result)
		logging.info('got %s instances by sql:%s'%(rows,sql))
		return all_results

	@classmethod
	def classupdate(cls, chandict, posdict):
		chan = ""
		for k,v in chandict.items():
			chan += k + '=' + sql_var(v)
		pos = ""
		for k,v in posdict.items():
			pos += k + '=' + sql_var(v)
		sql = cls.__update__.replace('?','%s')%(chan,pos)
		rows = execute(sql)
		if rows == 0:
			logging.warn('0 row affected by %s'%sql)
		return rows
	@classmethod
	def classdelete(cls, **posdict):
		pos = ""
		for k,v in posdict.items():
			pos += k + '=' + sql_var(v)
		sql = cls.__deletesql__.replace('?','%s')%(pos)
		rows = execute(sql)
		if rows == 0:
			logging.warn('0 row affected by %s'%sql)
		return rows	

	@classmethod
	def delete_by_prim(cls, value):
		pos = cls.__primaryKey__ + '=' + sql_var(value)
		sql = cls.__deletesql__.replace('?','%s')%(pos)
		row = execute(sql)
		if row != 1:
			logging.warn('failed to delete record: affected rows:%s'%row)
		return row

	def insert(self):
		values = list(map(self.getValueOrDefault, self.__notPrimary__))
		values.append(self.getValueOrDefault(self.__primaryKey__))
		#因为在sql语句里字符串还需要被引号框住
		values = list(map(lambda f: sql_var, values))
		args = self.__notPrimary__
		args.append(self.__primaryKey__)
		args, values = map(lambda x:(','.join(x)),(args,values))
		sql = self.__insert__.replace('?','%s')%(args,values)
		row = execute(sql)
		if row != 1:
			logging.warn('failed to insert record: affected rows: %s'%(rows))
		return row

	def merge(self):
		rs = self.to_get(self[self.__primaryKey__])
		if (rs):
			values = []
			for k,v in self.items():
				if  (k != self.__primaryKey__):
					values.append("`%s` = %s"%(k,sql_var(v)))
			if not values:
				logging.warn('nothing changed by merge')
				return False
			posdict = self.__primaryKey__ + '=' + sql_var(rs[self.__primaryKey__])
			sql = self.__update__.replace('?','%s')%(','.join(values),posdict)
		else:
			return self.insert()
		print (sql)
		row = execute(sql)
		if row != 1:
			logging.warn('failed to insert record: affected rows: %s'%(row))
		return row

	def delete(self):
		row = self.delete_by_prim(self[self.__primaryKey__])
		if row != 1:
			logging.warn('failed to delete record: affected rows:%s'%row)
		return row


		
class bUser(Model):
	# table name should be the name of class which could be set in metaclass

	# contents of table
	# primary key definition
	# data kinds definition
	# length definition

	id = IntegerField(primary_key = True, ddl=20)
	name = StringField(ddl=14)
	age = IntegerField(ddl=2)
#bUser.create()
#print (bUser.to_get(7))
u = bUser(id =10)
u.merge()
u.delete()



	#aUser.create()
#except:
#	pass



conn.commit()
conn.close()







