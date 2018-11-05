"""
Created on Aug 17, 2018

@authors: Uriel, Mendi
"""
import functools

import networkx as nx
from pyutils import hashing
from Entities import Action, Session

import DataModule.models as Models

SUPPORTED_FILE_TYPES = {"c", "h", "cpp", "hpp", "py", "cs"}


class CsrFiles:
    def __init__(self):
        self.csr = nx.Graph()
        self.filesMapping = hashing.MagicHash()

    def _supported_type(self, filename):
        return filename.rsplit(".")[-1] in SUPPORTED_FILE_TYPES

    def commit_to_session(self, commit: Models.Commit):
        session = Session(commit.author.email, commit.date_str)

        for file in commit.files:
            if file.changetype == Models.ChangeEnum.RENAMED:
                try:
                    self.filesMapping.rename(file.source, file.target)
                except KeyError:
                    print(f"! WARNING ! rename file source not found. "
                          f"{commit.sha}: {file.source}->{file.target}")
                    raise

            elif file.changetype not in Models.ChangeEnum:
                raise ValueError(f"Unknown file status: {str(file)}")

            else:
                objId = self.filesMapping[file.target]
                if self._supported_type(file.target):
                    self._inner_process(objId, file, session)

        return session

    def _inner_process(self, objId: int, file: Models.FileChangeset, session: Session):
        """
        just so derived classes can override behavior
        """
        session.addAction(Action(objId, file.changetype))


class CsrCode(CsrFiles):
    def __init__(self):
        super().__init__()
        self.functionMapping = hashing.MagicHash()
        self.functionsSet = set()

    def _func_fullname(self, file, func):
        return f"{file}_->_{func}"

    def _inner_process(self, objId: int, file: Models.FileChangeset, session: Session):
        functions = set()
        for patch in file.patches:
            func_full_name = self._func_fullname(objId, patch.section_header)
            self.functionsSet.add(func_full_name)

            func_id = self.functionMapping[func_full_name]
            functions.add(Action(func_id, file.changetype))

            # TODO: fix here - not yield but session.add()
            yield from self.batch_get_functions(objId, Models.ChangeEnum.DELETED,
                                                patch.source_lines)
            yield from self.batch_get_functions(objId, Models.ChangeEnum.ADDED,
                                                patch.target_lines)

        yield from functions

    def batch_get_functions(self, file_id, status, lines):
        fullname = functools.partial(self._func_fullname, file=file_id)
        for f in self.functionsSet.intersection(set(map(fullname, lines))):
            yield Action(f, status)
