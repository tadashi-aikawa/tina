import json

r"""Dict and Json parsing mixin.

For example::

    class Human(JsonMixin):
        def __init__(self, id, name, favorite):
            self.id = id
            self.name = name
            self.favorite = Food.from_dicts(favorite)


    class Food(JsonMixin):
        def __init__(self, id, name, color=None):
            self.id = id
            self.name = name
            if color:
                self.color = color

    j = '''
    {
        "id": 10,
        "name": "tadashi",
        "favorite": [
            {"id": 1, "name": "apple"},
            {"id": 2, "name": "orange", "color": "white"}
        ]
    }
    '''

    d = {
        "id": 10,
        "name": "tadashi",
        "favorite": [
            {"id": 1, "name": "apple"},
            {"id": 2, "name": "orange", "color": "white"}
        ]
    }

    >>> y1 = Human.from_json(j)
    >>> y2 = Human.from_dict(d)
    >>> y1.to_json() == y2.to_json()
    True
"""

__version__ = '0.1.0'
__all__ = ['JsonMixin']
__author__ = 'Tadashi Aikawa <syou.maman@gmail.com>'


class DictMixin(object):
    @classmethod
    def from_dict(cls, d):
        return cls(**d)

    @classmethod
    def from_dicts(cls, ds):
        return [cls(**d) for d in ds]

    def to_dict(self):
        return self._traverse_dict(self.__dict__)

    def _traverse_dict(self, instance_dict):
        output = {}
        for key, value in instance_dict.items():
            output[key] = self._traverse(key, value)
        return output

    def _traverse(self, key, value):
        if isinstance(value, DictMixin):
            return value.to_dict()
        elif isinstance(value, dict):
            return self._traverse_dict(value)
        elif isinstance(value, list):
            return [self._traverse(key, i) for i in value]
        elif hasattr(value, '__dict__'):
            return self._traverse_dict(value.__dict__)
        else:
            return value


class JsonMixin(DictMixin):
    @classmethod
    def from_json(cls, data):
        return cls.from_dict(json.loads(data))

    def to_json(self, indent=0):
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def to_pretty_json(self):
        return self.to_json(4)
