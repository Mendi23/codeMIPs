from DataModule.DataQuery import Query


def main(repo_path):
    g = Query()
    for commit in g.repo_iterate_commits(repo_path):
        for file in commit.iterate_files():
            for



if __name__ == '__main__':
    main("urielha/log4stash")
