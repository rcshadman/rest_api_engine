from django.db import connection

class Query():
	
	
	""" ../table related methods""" 
	@classmethod
	def get_table_id(klass,table_name):
		cursor = connection.cursor()
		cursor.execute('SELECT c.oid,n.nspname,c.relname FROM pg_catalog.pg_class c LEFT JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace WHERE c.relname = %s AND pg_catalog.pg_table_is_visible(c.oid) ORDER BY 2, 3;',[table_name])
		table_id = cursor.fetchall()[0][0]
		return table_id

	@classmethod
	def get_all_tables(klass):
		tables=[]
		cursor = connection.cursor()
		cursor.execute("SELECT table_name FROM information_schema.tables where table_schema = 'public' ORDER BY table_name;")
		data = cursor.fetchall()
		for each in data:
			tables.append(each[0])
		return tables
		
	@classmethod
	def get_table_info(klass,table_name):
		cursor = connection.cursor()
		cursor.execute('SELECT column_name, data_type, is_nullable FROM information_schema.columns where table_name =%s;',[table_name])
		raw_data = cursor.fetchall()
		foreign_tables=klass.get_foreign_key_tables(table_name)
		table_id = klass.get_table_id(table_name)
		return klass.to_readable(raw_data,foreign_tables,table_id,table_name)
		
	@classmethod
	def to_readable(klass,raw_data,foreign_tables,table_id,table_name):
		primary_key=''
		foreign_keys=[]
		fields=[]
		fields_info={}
		
		for each in raw_data:
			fields.append(each[0])
			f_data = {each[0]:{'data_type':each[1],
							'is_nullable':each[2]
							}
					}
			fields_info.update(f_data)
			if '_id' in each[0]:
				foreign_keys.append(each[0])
			if 'id' == each[0]:
				primary_key = each[0]

		return	[primary_key,foreign_keys,fields,fields_info,foreign_tables,table_id,table_name]

	@classmethod
	def get_foreign_tables(klass,table_name):
		table_id = klass.get_table_id(table_name)
		foreign_tables = []
		cursor=connection.cursor()
		cursor.execute('SELECT confrelid::regclass AS foreign_table_name FROM pg_catalog.pg_constraint r WHERE r.conrelid = %s AND r.contype = %s ORDER BY 1;',[table_id,'f'])
		raw_data = cursor.fetchall()
		for each in raw_data:
			foreign_tables.append(each[0])
		return foreign_tables	
	
	@classmethod
	def get_foreign_key_tables(klass,table_name):
		foreign_key_table = {}
		cursor=connection.cursor()
		cursor.execute('SELECT tc.constraint_name, tc.table_name, kcu.column_name, ccu.table_name AS foreign_table_name, ccu.column_name AS foreign_column_name FROM information_schema.table_constraints AS tc JOIN information_schema.key_column_usage AS kcu ON tc.constraint_name = kcu.constraint_name JOIN information_schema.constraint_column_usage AS ccu ON ccu.constraint_name = tc.constraint_name WHERE constraint_type = %s AND tc.table_name = %s;',['FOREIGN KEY',table_name])
		raw_data = cursor.fetchall()
		for each in raw_data:
			foreign_key_table.update({each[2]:each[3]})
		return foreign_key_table

	""" ../data related methods"""
	@classmethod
	def get_object_info(klass,body):
		dict_result = []
		cursor=connection.cursor()
		Query_String = Generator.select_query(body)
		print Query_String
		# Query_String = 'SELECT id, name FROM nd_resident WHERE name IN (anu,devin,madhu);'
		cursor.execute(Query_String)
		dict_result = klass.dictfetchall(cursor)
		print dict_result
		return dict_result
	
	@classmethod
	def dictfetchall(klass,cursor):
		columns = [col[0] for col in cursor.description]
		return [dict(zip(columns, row)) for row in cursor.fetchall()]
    


class Generator(Query):
	
	@classmethod
	def select_query(klass,body):
		
		wheres={}
		columns=[]
		limit=""
		offset=""
		groupby=[]
		having={}
		
		table_name = body['table']
		columns = body['columns']
		if body.has_key('distinct'):
			distinct = body['distinct']
		if body.has_key('where'):
			wheres = body['where']
		if body.has_key('limit'):
			limit = body['limit']
		if body.has_key('offset'):
			offset = body['offset']
		if body.has_key('groupby'):
			groupby = body['groupby']
		if body.has_key('having'):
			having = body['having']

		Query_String = 'SELECT '
		if distinct == 'true':
			Query_String +='DISTINCT '
		
		Query_String +=klass.column(columns,table_name)[0]
		aggregation = klass.column(columns,table_name)[1]
		
		Query_String += ' FROM '
		Query_String += table_name
		
		if wheres:
			print wheres
			Query_String+=klass.where_clause(wheres)
		
		if aggregation:
			Query_String+=" "
			Query_String+=klass.groupby_clause(groupby)

		if groupby and having:
			Query_String+=" "
			Query_String+=klass.having_clause(having)
			""" having here"""

		if limit and limit != "''":
			Query_String+=" "
			Query_String+=klass.limit_clause(limit)

		if offset and offset != "''":
			Query_String+=" "
			Query_String+=klass.offset_clause(offset)



		Query_String += ';'	
		return Query_String
	
	@classmethod
	def column(klass,columns,table_name):
		aggregation = False
		fields = klass.get_table_info(table_name)[2]
		column_string = ''
		for column in columns:
			if type(column)==type(list()):
				aggregation = True
				function = klass.function_map(column[0])
				if function == any(["MOD","POWER"]):
					column_string+= klass.function_map(column[0])+'('+column[1]+','+column[2]+')'	
				else:
					column_string+= klass.function_map(column[0])+'('+column[1]+')'
			else:
				column_string += column
			column_string += ', '
		column_string = column_string[:-2]
		return column_string,aggregation

	@classmethod
	def where_clause(klass,wheres):
		Query_String = ' WHERE '
		where_string = ''
		for param_position in range(len(wheres)):
			filter_expression = ''
			params_array = wheres.get(str(param_position))
			if len(params_array) is 1 and len(wheres)%2 is 1 and len(wheres) > 1:
				bool_condition = params_array[0]
				filter_expression+=' '+bool_condition+' '
			elif len(params_array) == 3:
				column_name = params_array[0]
				operator = params_array[1]
				value = params_array[2]
				filter_expression += column_name+' '+operator+' '+str(value)
			elif len(params_array) > 3:
				column_name = params_array[0]
				operator = params_array[1]
				values=params_array[2:]
				if operator == 'IN' or operator == 'NOT IN':
					filter_expression += column_name+' '+operator+' '+'('
					for each_value in values:
						filter_expression+=str(each_value)
						filter_expression+=','
					filter_expression=filter_expression[:-1]+')'
				elif operator == 'BETWEEN':
					print operator
					value1 = values[0]
					value2 = values[1]
					filter_expression += column_name+' '+operator+' '+value1+' AND '+value2
					
				
			where_string+=filter_expression
			print where_string
			
		Query_String+= where_string
		return Query_String	
	
	@classmethod 
	def limit_clause(klass,limit):
		 return "LIMIT "+limit

	@classmethod 
	def offset_clause(klass,offset):
		return "OFFSET "+offset


	@classmethod
	def groupby_clause(klass,groupby):
		groupby_string = "GROUP BY "
		for column in groupby:
			groupby_string+=column
			groupby_string+=","
		return groupby_string[:-1]

	@classmethod
	def having_clause(klass,having):
		having_string = "HAVING "
		string = ''
		for param_position in range(len(having)):
			filter_expression = ''
			params_array = having.get(str(param_position))
			if len(params_array) is 1 and len(having)%2 is 1 and len(having) > 1:
				bool_condition = params_array[0]
				filter_expression+=' '+bool_condition+' '
			elif len(params_array) == 3:
				column_name = params_array[0]
				operator = params_array[1]
				value = params_array[2]
				if type(column_name)==type(list()):
					filter_expression+= klass.function_map(column_name[0])+'('+column_name[1]+')'+operator+value
				else:
					filter_expression += column_name+' '+operator+' '+str(value)
			string+=filter_expression
			
		having_string+= string
		return having_string

	@classmethod
	def function_map(klass,function_string):
		
		functions={
				"minimum":"MIN",
				"maximum":"MAX",
				"average":"AVG",
				"addition":"SUM",
				"count":"COUNT",
				"absolute":"ABS",
				"sign":"SIGN",
				"smallest":"CEILING",
				"largest":"FLOOR",
				"CEIL":"CEIL",
				"roundoff":"ROUND",
				"squareroot":"SQRT",
				"modules":"MOD",
				"power":"POWER",
		}
		return functions.get(function_string)
	