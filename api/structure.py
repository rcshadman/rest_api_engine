class Json_structure():
	@classmethod
	def table(klass,explode_data):
		json_data = {'table_name':explode_data[6],
					 'fields_name':explode_data[2],
					 'foreign_keys':explode_data[1],
					 'primary_key':explode_data[0],
					 'fields_info':explode_data[3],
					 'table_id':explode_data[5],
					 'foreign_key_tables':explode_data[4]
					  }		
		return json_data
	
	@classmethod
	def data(klass,explode_data):
		return explode_data
		
