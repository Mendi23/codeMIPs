import prettytable
from DataModule.DataQuery import GithubQuery
from pyutils.file_paths import REPOSITORIES_LIST_FILE, STORAGE_DIR

if __name__ == '__main__':
    gen = (line.strip().split("#", 1)[0]
           for line in open(REPOSITORIES_LIST_FILE))
    repos = [repo for repo in gen if repo]
    table = prettytable.PrettyTable(["name", "commits"], sortby="commits")
    for repo in repos:
        q = GithubQuery.create(STORAGE_DIR, repo)
        commits = q.num_of_commits()
        table.add_row([repo, commits])

    print(table)
