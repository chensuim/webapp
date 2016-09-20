class ModelMetaclass(type):
	# 任何类的诞生都是启动了一个__new__函数
	def __new__(cls, name, bases, attrs):
	#排除model本身，只是为了让继承model的类能够按这个metaclass设定
	#不能在model类里定义是因为，在父类里的定义不能删除子类里的定义
		if name == 'Model':
			return type.__new__(cls, name, bases, attrs)
	#获取table名称，这个应该在新的类里定义:
	#attrs包含所有在定义类时定义的attrs，是一个dict，keys是字符串，values可以是函数
		table_name = attrs.get('__table__', None) or name
		#为每一个table创建一个类，logging记录，便于排查
		logging.info('found model: %S (table: %s)'% (name, table_name))
		#在定义一个新的table的类的时候，会把所有变量都定义进field，如同 name char（23）
		#这里把所有定义成field类的attrs放进一个dict里面，便于传入sql函数里
		mappings = dict()
		# ???
		fields = []
		primary_key = None
		for k,v in attrs.items():
			#需要定义Field类,或则由orm这个module提供
			if isinstance(v, Field):
				logging.info('found field %s => %s'%(k,v))
				mappings[k] = v
				#
				if v.prv是一个field类imary_key:
					#只能有一个primary key
					if primary_key:
						raise RuntimeError('found a new primary key : %s, the first one is %s'%(k,primary_key))
					primary_key = k
				else:
					#把fields的名字都装起来？？这事一个字符串的list
					#实际上在mysql里，储存也是按照名字加内容储存的，类似于dict
					#引用fields这个list只是为了方便，省得用mappings。keys（）？？？
					#又或者只是为了区分primary key和others？
					fields.append(k)
		if not primary_key:
			raise RuntimeError('Primaet key not found')
				#把所有field类都从attrs里去掉放进一个叫mappings的dict里
				#因为这一步必须要用元类
		for k in mappings.keys():
			attrs.pop(k)
				#fields 是一个包含所有field类（不含primary key）的keys的list，
				#用这个函数将其加上反单引号，不知道为何？？？
				#反单引可能只是mysql语句的要求
		escaped_fields = list(map(lambda x:'`%s`'%x, fields))
				#把mappings保存到attr里
		attrs['__mappings__'] = mappings
		attrs['__table__'] = table_name
		attrs['__primary_key__'] = primary_key
		attrs['__fields__'] = fields
				#因为escaped fields已经加了反单引了
		attrs['__select__'] = 'SELECT `%s`, %s FROM `%s`'% (primary_key, ','.join(escaped_fields),table_name)

				#完全不懂了，create_args_string是一个什么时候会定义的函数啊，在那里面会给变量加反单引号吗？是一个字符串吧,为什么只要一个int作为变量啊
				#定义一个对应新的表的新的类时，要插入的变量还没定。。。。
		attrs['__insert__'] = 'INSERT INTO`%s` (%s, `%s`) VALUES (%s)'%(tabel_name, ','.join(escaped_fields),primary_key, create_args_string(len(escaped_fields)+1))
		attrs['__update__'] = 'UPDATE `%s` SET %s WHERE `%s` = ?'%(table_name, ','.join(map(lambda x:'`%s`=?'%(mappings.get(x).name or x),fileds)), primary_key)
		attrs['__delete__'] = 'DELETE FROM ｀％s｀ WHERE `%s` = ?'%(table_name, primary_key)
		return type.__new__(cls, name, bases, attrs)

class Field(object):
	def __init__(self, name, column_type, primary_key, default):
		self.name = name
		self.column_type = column_type
		self.primary_key = primary_key
		self.default = default

	def __str__(self):
		return '<%s, %s:%s>'% (self.__class__.__name__, self.column_type, self.name)


class String_Field(Field):
	def __init__(self, name = None, primary_key = False, default = None):
		#super()调用父类函数，在这里等同于super(String_Field,self)
		#self会自行传入
		super().__init__(name, 'varchar(100)',primary_key, default)


class Integer_Field(Field):
	def __init__(self, name = None, primary_key = False, default = None):
		#super()调用父类函数，在这里等同于super(String_Field,self)
		#self会自行传入
		super().__init__(name, 'bigint',primary_key, default)



class Model(dict, metaclass = ModelMetaclass):
	#a=3这种表达式叫做keyswords pairs（kw）
	#**表示无线接收keyswords pairs
	def __init__(self,**kw):
		super().__init__(kw)
		#一些特定函数python把他们命名为前后都有__的函数
		#没看出来这个getattr函数有什么用？？？？？
	def __getattr__(self, key):
		try:
			return self[key]
		except KeyError:
			#这个r是什么？？？？？？
			raise AttributeError(r"'Model' object has no attribute '%s'"%key)


	def __setattr__(self, key, value):
		self[key] = value

	#就为了省少写一个default＝None?????
	def get_value(self, key):
		return getattr(self, key, None)

	def get_value_or_default(self, key):
		value = getattr(self, key, None)
		if value is None:
			#field应该是一个Field类
			field = self.__mappings__[key]
			#这个default在field类设定的时候设定，default值是none
			if field.default is not None:
				value = field.default() if callabel(field.default) else field.default
				#这里变成debug类的logging了
				logging.debug('using default value for %s:%s'%(key, str(value)))
				#setattr是不是指向__setattr__函数？？？？
				setattr(self, key, value)
		return value






















