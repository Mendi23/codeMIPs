import itertools
import json, os, re

from typing import IO, Iterable, Callable

import DataModule.models as Models

class CustomJsonEncoder(json.JSONEncoder):
    def default(self, o):
        if hasattr(o, "serialize"):
            return o.serialize()
        return json.JSONEncoder.default(self, o)


def decode_json_stacked(document, pos=0, decoder=json.JSONDecoder()):
    NOT_WHITESPACE = re.compile(r'[^\s]')
    while True:
        match = NOT_WHITESPACE.search(document, pos)
        if not match:
            return
        pos = match.start()

        obj, pos = decoder.raw_decode(document, pos)
        yield obj


def _decode_commit_list(o):
    return [Models.Commit.create(c) for c in o]


class Storage:
    @staticmethod
    def init_save_dir(savedir):
        """
        Check existence of given dir path, create if not exists.
        Raise NotADirectoryError if `savedir` exists but not valid path to dir.
        :param savedir: directory name
        :return: the given path
        """
        if not os.path.exists(savedir):
            os.mkdir(savedir)
        elif not os.path.isdir(savedir):
            raise NotADirectoryError(f"{savedir} must be a directory")
        return savedir

    @staticmethod
    def get_valid_filename(orig):
        """
        Convert given `orig` path to a valid one by removing invalid chars
        :return: the valid path
        """
        s = str(orig).strip().replace(" ", "_")
        s = re.sub(r"[\\/]", "_", s)
        return re.sub(r"(?u)[^-\w.]", "", s)

    @staticmethod
    def export_object_to_json_file(obj, fo, encoder):
        data = json.dumps(obj, indent=2, cls=encoder)
        fo.write(os.linesep)
        fo.write(data)
        fo.flush()

    @staticmethod
    def import_objects_from_json_file(fo, decoder, decode_stacked):
        """
        :param fo: file object
        :param decoder: decoder for one object
        :param decode_stacked: decoder which know how to read the data from the file
                               and extract sections of one encoded object each time.
        :return: list of objects
        """
        data = fo.read()
        return [
            decoder(obj)
            for obj in decode_stacked(data)
            if any(obj)
        ]

    def __init__(self, filename, page_size,
                 export_obj_to_file: Callable[[object, IO], None],
                 import_multiply_from_file: Callable[[IO], Iterable[object]]):
        """
        :param filename: general filename or filepath for the data
        :param page_size: when reached `page_size` objects in one file
                          rolling to a new file.
        :param export_obj_to_file: function - get object and IO and write the
                                   object to the file
        :param import_multiply_from_file: function - get IO and return objects
        """
        self.import_multiply_from_file = import_multiply_from_file
        self.export_obj_to_file = export_obj_to_file
        self.page_size = page_size
        self.filename = filename + ".{:03}.jsons"
        self.fo = None
        self.objects_count = 0

    def dispose(self):
        if self.fo is not None:
            self.fo.close()

    def load_all(self):
        for i in itertools.count():
            fname = self.filename.format(i)
            if not os.path.exists(fname): return
            with open(fname, "r") as fo:
                for o in self.import_multiply_from_file(fo):
                    yield o
                    self.objects_count += 1

    def save_obj(self, obj):
        if self.fo is None:
            self.fo = self._open_file(self.objects_count)

        self.export_obj_to_file(obj, self.fo)
        self.objects_count += 1
        i = self.objects_count
        if i > 0 and i % self.page_size == 0:
            self.fo.close()
            self.fo = self._open_file(i)

    def _open_file(self, i):
        return open(self.filename.format(i // self.page_size), "a+")


class Gen:
    def __init__(self, stop, gen):
        self.stop = stop
        self._gen = iter(gen)
        self.i = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.i == self.stop:
            self.i += 1
            raise StopIteration()
        res = next(self._gen)
        self.i += 1
        return res

    def __repr__(self):
        cls = self.__class__
        s1 = f"<{cls.__module__}.{cls.__name__} iter"
        s2 = f"i:{self.i}, stop:{self.stop}"
        return ", ".join([s1, s2, f"{str(self._gen)}>"])
