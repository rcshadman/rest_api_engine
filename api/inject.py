from api.service import Query
from api.structure import Json_structure

class Inject():
	@classmethod
	def Query(klass):
		return Query
	@classmethod
	def Json_structure(klass):
		return Json_structure