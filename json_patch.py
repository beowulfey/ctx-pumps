""" Module that monkey-patches json module when it's imported so
JSONEncoder.default() automatically checks for a special "to_json()"
method and uses it to encode the object if found.
"""
from json import JSONEncoder
import pickle

def _default(self, obj):
	return {'_python_object': pickle.dumps(obj)}

JSONEncoder.default = _default # Replace it.
