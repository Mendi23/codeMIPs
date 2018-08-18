from DataModule.DataQuery import Query
from Entities import Session, Action
from MIP import Mip


def main(repo_path):
    git = Query()
    graph = Mip()
    for commit in git.repo_iterate_commits(repo_path):
        actions = [Action(modif.segment, modif.type) for modif in commit.iterate_changes()]
        graph.updateMIP(Session(commit.committer, actions, commit.date))


if __name__ == '__main__':
    main("Mendi23/Dummy")
