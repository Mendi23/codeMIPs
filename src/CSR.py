"""
Created on Aug 17, 2018

@authors: Uriel, Mendi
"""
import functools

import networkx as nx
from pyutils import hashing
from Entities import Action, Session

import DataModule.models as Models


class CsrFiles:
    def __init__(self):
        self.csr = nx.Graph()
        self.mapping = hashing.MagicHash()

    def commit_to_session(self, commit: Models.Commit):
        session = Session(commit.author.email, commit.date_str)

        file: Models.FileChangeset = None  # for autocorrect
        for file in commit.files:
            if file.changetype == Models.ChangeEnum.ADDED:
                status = "added"
                objId = self.mapping[file.target]

            elif file.changetype == Models.ChangeEnum.MODIFIED:
                status = "modified"
                objId = self.mapping[file.target]

            elif file.changetype == Models.ChangeEnum.RENAMED:
                self.mapping.rename(file.source, file.target)
                status = "renamed"
                objId = self.mapping[file.target]

            elif file.changetype == Models.ChangeEnum.DELETED:
                status = "removed"
                #TODO: Not good if re-instated
                objId = self.mapping.pop(file.source)

            else:
                raise ValueError(f"Unknown file status: {str(file)}")

            session.addAction(Action(objId, status))

        return session

class CsrCode:
    def __init__(self):
        self.csr = nx.Graph()
        self.filesMapping = hashing.MagicHash()
        self.functionMapping = hashing.MagicHash()
        self.functionsSet = set()

    def _func_fullname(self, file, func):
        return f"{file}_->_{func}"

    def apply_changes_from_commit(self, commit: Models.Commit):
        file: Models.FileChangeset = None  # for autocorrect
        for file in commit.files:
            if file.changetype == Models.ChangeEnum.ADDED:
                status = "added"
                file_id = self.filesMapping[file.target]

            elif file.changetype == Models.ChangeEnum.MODIFIED:
                status = "modified"
                file_id = self.filesMapping[file.target]

            elif file.changetype == Models.ChangeEnum.RENAMED:
                self.filesMapping.rename(file.source, file.target)
                status = "renamed"
                file_id = self.filesMapping[file.target]

            elif file.changetype == Models.ChangeEnum.DELETED:
                status = "removed"
                file_id = self.filesMapping.pop(file.source)

            else:
                raise ValueError(f"Unknown file status: {str(file)}")

            functions = set()
            for patch in file.patches:
                func_full_name = self._func_fullname(file_id, patch.section_header)
                self.functionsSet.add(func_full_name)

                func_id = self.functionMapping[func_full_name]
                functions.add(Action(func_id, status))

                yield from self.batch_get_functions(file_id, "removed", patch.source_lines)
                yield from self.batch_get_functions(file_id, "added", patch.target_lines)

            yield from functions

    def batch_get_functions(self, file_id, status, lines):
        fullname = functools.partial(self._func_fullname, file=file_id)
        for f in self.functionsSet.intersection(set(map(fullname, lines))):
            yield Action(f, status)

