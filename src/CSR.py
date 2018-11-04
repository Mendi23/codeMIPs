"""
Created on Aug 17, 2018

@authors: Uriel, Mendi
"""
import functools

import networkx as nx
from pyutils import hashing
from Entities import Action, Session

import DataModule.models as Models

SUPPORTED_FILE_TYPES = {".c", ".h", ".cpp", ".hpp", ".py", ".cs"}

class CsrFiles:
    def __init__(self):
        self.csr = nx.Graph()
        self.filesMapping = hashing.MagicHash()

    def getObjectIdByFile(self, file: Models.FileChangeset):
        if file.changetype == Models.ChangeEnum.ADDED:
            objId = self.filesMapping[file.target]

        elif file.changetype == Models.ChangeEnum.MODIFIED:
            objId = self.filesMapping[file.target]

        elif file.changetype == Models.ChangeEnum.RENAMED:
            self.filesMapping.rename(file.source, file.target)
            objId = self.filesMapping[file.target]

        elif file.changetype == Models.ChangeEnum.DELETED:
            objId = self.filesMapping[file.source]

        else:
            raise ValueError(f"Unknown file status: {str(file)}")
        return objId

    def commit_to_session(self, commit: Models.Commit):
        session = Session(commit.author.email, commit.date_str)

        for file in commit.files:
            objId = self.getObjectIdByFile(file)
            if file.source.rsplit(".")[-1] in SUPPORTED_FILE_TYPES:
                session.addAction(Action(objId, file.changetype))

        return session


class CsrCode(CsrFiles):
    def __init__(self):
        super().__init__()
        self.functionMapping = hashing.MagicHash()
        self.functionsSet = set()

    def _func_fullname(self, file, func):
        return f"{file}_->_{func}"

    def apply_changes_from_commit(self, commit: Models.Commit):
        for file in commit.files:
            file_id = self.getObjectIdByFile(file)

            functions = set()
            for patch in file.patches:
                func_full_name = self._func_fullname(file_id, patch.section_header)
                self.functionsSet.add(func_full_name)

                func_id = self.functionMapping[func_full_name]
                functions.add(Action(func_id, file.changetype))

                yield from self.batch_get_functions(file_id, Models.ChangeEnum.DELETED, patch.source_lines)
                yield from self.batch_get_functions(file_id, Models.ChangeEnum.ADDED, patch.target_lines)

            yield from functions

    def batch_get_functions(self, file_id, status, lines):
        fullname = functools.partial(self._func_fullname, file=file_id)
        for f in self.functionsSet.intersection(set(map(fullname, lines))):
            yield Action(f, status)
