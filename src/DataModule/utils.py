import json, os, re

import typing

import DataModule.models as Models

class _CustomJsonEncoder(json.JSONEncoder):
    def default(self, o):
        if hasattr(o, "serialize"):
            return o.serialize()
        return json.JSONEncoder.default(self, o)


def _decode_stacked(document, pos=0, decoder=json.JSONDecoder()):
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
        if not os.path.exists(savedir):
            os.mkdir(savedir)
        elif not os.path.isdir(savedir):
            raise NotADirectoryError(f"{savedir} must be a directory")
        return savedir

    @staticmethod
    def get_valid_filename(orig):
        s = str(orig).strip().replace(" ", "_")
        s = re.sub(r"[\\/]", "_", s)
        return re.sub(r"(?u)[^-\w.]", "", s)

    @staticmethod
    def export_object_to_file(obj, fo, encoder=_CustomJsonEncoder):
        data = json.dumps(obj, indent=2, cls=encoder)
        fo.write(os.linesep)
        fo.write(data)
        fo.flush()

    @staticmethod
    def import_objects_from_file(fo, decoder=_decode_commit_list):
        data = fo.read()
        return [
            decoder(obj)
            for obj in _decode_stacked(data)
            if any(obj)
        ]

    # def __init__(self, savedir, repouri):
    #     repouri_valid = self.get_valid_filename(repouri)
    #     repo_dir = os.path.join(savedir, repouri_valid)
    #     if not os.path.isdir(repo_dir):
    #         os.mkdir(repo_dir)
    #
    #     self.file_name = os.path.join(repo_dir, "data.jsons")
    #     self.head_name = os.path.join(repo_dir, "commits_num.txt")
    #     self.conf = {}
    #     self.load()
    #
    # def load(self):
    #     exists = os.path.exists
    #     if not exists(self.file_name):
    #         open(self.file_name, "w").close()
    #     if not exists(self.head_name):
    #         open(self.head_name, "w").close()
    #
    #     with open(self.head_name) as head:
    #         data = head.read()
    #         if len(data) > 0:
    #             self.conf[self.SEC_HEAD] = data
    #
    #     self.file = open(self.file_name, "r+")
    #     data = self.file.read()
    #     self.conf[self.SEC_COMMITS] = {
    #         int(page): _decode_commit_list(commits)
    #         for page, commits in _decode_stacked(data)
    #         if any(commits)
    #     }
    #
    # @property
    # def commits_len(self):
    #     if self.SEC_HEAD in self.conf:
    #         return int(self.conf[self.SEC_HEAD])
    #     else:
    #         return -1
    #
    # @commits_len.setter
    # def commits_len(self, length):
    #     self.conf[self.SEC_HEAD] = str(length)
    #     with open(self.head_name, "w") as head:
    #         head.write(self.conf[self.SEC_HEAD])
    #
    # def get_pages(self) -> typing.Dict[int, typing.List[Models.Commit]]:
    #     return self.conf[self.SEC_COMMITS]
    #
    # def add_page(self, page, commits):
    #     key = self.SEC_COMMITS
    #     page_num = int(page)
    #     if page_num in self.conf[key]:
    #         print(f"Warning: overwriting a page num: {page}")
    #     self.conf[key][page_num] = commits
    #
    #     self.export_object_to_file([page_num, commits], self.file)
    #
    # def dispose(self):
    #     self.file.close()


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
