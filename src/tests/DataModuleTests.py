"""
Created on Sep 7, 2018

@authors: Uriel, Mendi
"""
import io
import os
import shutil
import unittest
from os import path

import DataModule.models as Models
import DataModule.DataQuery as DQ
from DataModule.utils import Storage, Gen
import itertools
import functools

from pyutils.file_paths import STORAGE_DIR

class GenTests(unittest.TestCase):
    def test_generator(self):
        gen = Gen(10, range(100))
        c = functools.partial(next, itertools.count(0))
        for i in gen:
            self.assertEqual(i, c())

        for i in gen:
            self.assertEqual(i, c())

        for _ in gen:
            self.fail("should not reach here")

        self.assertEqual(100, c())


class StorageTests(unittest.TestCase):
    DIR = path.join(STORAGE_DIR, "test_storage_dir")

    def setUp(self):
        self.fo = None
        self.obj = None
        self.objects = [1, 2, 3, 4]
        self.storage = Storage(self.DIR, 1, self.export_obj_to_file, self.import_from_file)

    def tearDown(self):
        self.storage.dispose()

    def export_obj_to_file(self, obj, fo):
        self.assertEquals(obj, self.obj)
        self.assertIsInstance(fo, io.IOBase)
        self.assertNotEqual(self.fo, fo)
        self.fo = fo

    def import_from_file(self, fo):
        self.assertIsInstance(fo, io.IOBase)
        return self.objects

    def test_save(self):
        self.obj = 1
        self.storage.save_obj(self.obj)
        self.storage.save_obj(self.obj)
        self.storage.save_obj(self.obj)
        self.assertEqual(self.storage.objects_count, 3)

    def test_load(self):
        objects = list(self.storage.load_all())
        self.assertEqual(len(objects), len(self.objects))
        self.assertEqual(self.storage.objects_count, len(self.objects))


if __name__ == '__main__':
    unittest.main()
