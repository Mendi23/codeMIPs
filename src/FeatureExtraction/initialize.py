from DataModule.DataQuery import Query
from Entities import Session, Action
from MIP import Mip


def main(repo_path):
    git = Query()
    graph = Mip()
    for commit in git.repo_iterate_commits(repo_path):
        actions = []
        for modif in commit.iterate_changes():
            if modif.type == 'rename':
                pass


            # here should calculate acion incWeight
            actions.append(Action(modif.segment, modif.type))
        graph.updateMIP(Session(commit.committer, actions,commit.date))




if __name__ == '__main__':
    main("urielha/log4stash")
