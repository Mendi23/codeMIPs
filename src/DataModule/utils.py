import json, os, re

import typing

import DataModule.models as Models


def _get_valid_filename(orig):
    s = str(orig).strip().replace(" ", "_")
    s = re.sub(r"[\\/]", "_", s)
    return re.sub(r"(?u)[^-\w.]", "", s)


class _CustomJsonEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Models.Base):
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
    return [Models.CommitPatch.create(c, True) for c in o]


class Storage:
    SEC_HEAD = "head"
    SEC_COMMITS = "commits"

    @staticmethod
    def init_save_dir(savedir):
        if not os.path.exists(savedir):
            os.mkdir(savedir)
        elif not os.path.isdir(savedir):
            raise NotADirectoryError(f"{savedir} must be a directory")
        return savedir

    def __init__(self, savedir, repouri):
        repouri_valid = _get_valid_filename(repouri)
        repo_dir = os.path.join(savedir, repouri_valid)
        if not os.path.isdir(repo_dir):
            os.mkdir(repo_dir)

        self.file_name = os.path.join(repo_dir, "data.jsons")
        self.head_name = os.path.join(repo_dir, "commits_num.txt")
        self.conf = {}
        self.load()

    def load(self):
        exists = os.path.exists
        if not exists(self.file_name):
            open(self.file_name, "w").close()
        if not exists(self.head_name):
            open(self.head_name, "w").close()

        with open(self.head_name) as head:
            data = head.read()
            if len(data) > 0:
                self.conf[self.SEC_HEAD] = data

        self.file = open(self.file_name, "r+")
        data = self.file.read()
        self.conf[self.SEC_COMMITS] = {
            int(page): _decode_commit_list(commits)
            for page, commits in _decode_stacked(data)
            if any(commits)
        }

    @property
    def commits_len(self):
        if self.SEC_HEAD in self.conf:
            return int(self.conf[self.SEC_HEAD])
        else:
            return -1

    @commits_len.setter
    def commits_len(self, length):
        self.conf[self.SEC_HEAD] = str(length)
        with open(self.head_name, "w") as head:
            head.write(self.conf[self.SEC_HEAD])

    def get_pages(self) -> typing.Dict[int, typing.List[Models.CommitPatch]]:
        return self.conf[self.SEC_COMMITS]

    def add_page(self, page, commits):
        key = self.SEC_COMMITS
        page_num = int(page)
        if page_num in self.conf[key]:
            print(f"Warning: overwriting a page num: {page}")
        self.conf[key][page_num] = commits

        self.export_object_to_file([page_num, commits], self.file)

    def dispose(self):
        self.file.close()

    @staticmethod
    def export_object_to_file(obj, fo):
        data = json.dumps(obj, indent=2, cls=_CustomJsonEncoder)
        fo.write(os.linesep)
        fo.write(data)
        fo.flush()

class Storage_new:
    @staticmethod
    def init_save_dir(savedir):
        if not os.path.exists(savedir):
            os.mkdir(savedir)
        elif not os.path.isdir(savedir):
            raise NotADirectoryError(f"{savedir} must be a directory")
        return savedir

    def __init__(self, savedir, repouri):
        repouri_valid = _get_valid_filename(repouri)
        repo_dir = os.path.join(savedir, repouri_valid)
        if not os.path.isdir(repo_dir):
            os.mkdir(repo_dir)

        self.file_name = os.path.join(repo_dir, "data.jsons")
        self.conf = {}
        self.load()

    def load(self):
        exists = os.path.exists
        if not exists(self.file_name):
            open(self.file_name, "w").close()

        self.file = open(self.file_name, "r+")
        data = self.file.read()
        self.conf = {
            key: value
            for key, value in _decode_stacked(data)
            if any(value)
        }

    def get_pages(self) -> typing.Dict[str, object]:
        return self.conf

    def add_page(self, key, value):
        if key in self.conf:
            print(f"Warning: overwriting a key: {key}")
        self.conf[key] = value

        data = json.dumps([key, value], indent=2, cls=_CustomJsonEncoder)
        self.file.write(os.linesep)
        self.file.write(data)
        self.file.flush()

    def dispose(self):
        self.file.close()


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
