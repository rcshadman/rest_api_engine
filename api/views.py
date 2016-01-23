
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import View

import json
from api.inject import Inject


class Table(View):
	
	tables_info = {}
	tables_all = {}
	table_map = []
	table_name = ""
	level = 0

	def get(self, request, *args, **kwargs):
		tables = Inject.Query().get_all_tables()
		json_data = {"tables":tables}
		self.tables_all.update(json_data)
		return HttpResponse(json.dumps(json_data),content_type='application/json')

	def post(self,request, *args, **kwargs):
		body = json.loads(request.body)
		table_name = body['table']
		if table_name and table_name in Inject.Query().get_all_tables():
			explode_data = Inject.Query().get_table_info(table_name)
			json_data = Inject.Json_structure().table(explode_data)
			self.tables_info.update({table_name:json_data})
			self.populate_tables(explode_data[4]);self.level = 0
			# print self.table_map
			print self.tables_info
			print "tables populated : %d"%len(self.tables_info.keys())
			print "levels:",len(self.table_map)
			return HttpResponse(json.dumps(json_data),content_type='application/json')
		elif table_name == 'linked_tables':
			return HttpResponse(json.dumps(self.tables_info),content_type='application/json')
		else:
			return HttpResponse("<p>NOTHING TO SHOW</p>")
	def populate_tables(self,foreign_key_tables):
		new_foreign_kt = {}
		
		self.table_map.append({})
		
		for each_table in foreign_key_tables.values():
			explode_data = Inject.Query().get_table_info(each_table)
			json_data = Inject.Json_structure().table(explode_data)
			self.tables_info.update({explode_data[6]:json_data})
			
			self.table_map[self.level].update({explode_data[6]:explode_data[4]})

			if len(explode_data[1]) is not 0:
				for table_in_explode in explode_data[4].values():
					if self.tables_info.has_key(table_in_explode):
						key_for_table = [k for k, v in explode_data[4].iteritems() if v == table_in_explode][0]
						explode_data[4].pop(key_for_table)
				new_foreign_kt.update(explode_data[4])
		
		if len(new_foreign_kt.keys()) is not 0:
			self.level+=1
			self.populate_tables(new_foreign_kt)

	# def map_db(self,table):


	
	
	@method_decorator(csrf_exempt)
	def dispatch(self, *args, **kwargs):
		return super(Table, self).dispatch(*args, **kwargs)



class Data(View):
	def get(self, request, *args, **kwargs):
		pass


	def post(self, request, *args, **kwargs):	
		body = json.loads(request.body)
		json_data = Inject.Json_structure().data(Inject.Query().get_object_info(body))
		return HttpResponse(json.dumps(json_data),content_type='application/json')

	@method_decorator(csrf_exempt)
	def dispatch(self, *args, **kwargs):
		return super(Data, self).dispatch(*args, **kwargs)

	
		