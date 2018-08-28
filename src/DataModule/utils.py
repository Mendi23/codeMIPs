import json, os, configparser, re
import DataModule.models as Models


class _CustomJsonEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Models.Base):
            return o.serialize()
        return json.JSONEncoder.default(self, o)


def _CustomJsonDecode(o):
    return [Models.Commit.create(c, True) for c in o]


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
        self.savedir = savedir
        repouri_valid = self.get_valid_filename(repouri)
        repo_file = os.path.join(self.savedir, repouri_valid)
        self.repo_file = f"{repo_file}.ini"
        self.conf = configparser.ConfigParser()
        self.conf.add_section(self.SEC_HEAD)
        self.conf.add_section(self.SEC_COMMITS)
        self.load()

    def get_valid_filename(self, orig):
        s = str(orig).strip().replace(" ", "_")
        s = re.sub(r"[\\/]", "_", s)
        return re.sub(r"(?u)[^-\w.]", "", s)

    def load(self):
        if not os.path.exists(self.repo_file):
            self.save()
        else:
            self.conf.read(self.repo_file)

    def save(self):
        self.conf.write(open(self.repo_file, "w"))

    @property
    def commits_len(self):
        key = "commits"
        if key in self.conf[self.SEC_HEAD]:
            return int(self.conf[self.SEC_HEAD][key])
        else:
            return -1

    @commits_len.setter
    def commits_len(self, length):
        self.conf[self.SEC_HEAD]["commits"] = str(length)
        self.save()

    def get_pages(self):
        key = self.SEC_COMMITS
        return {int(page): _CustomJsonDecode(json.loads(val))
            for page, val in self.conf[key].items()}

    def add_page(self, page, commits):
        key = self.SEC_COMMITS
        page_num = str(page)
        if page_num in self.conf[key]:
            print(f"Warning: overwriting a page num: {page}")
        self.conf[key][page_num] = json.dumps(commits, indent=2, cls=_CustomJsonEncoder)
        self.save()


class Gen:
    def __init__(self, stop, gen):
        self.stop = stop
        self._gen = gen
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
