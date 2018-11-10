# CodeMips root source directory

## CSR.py

Translating commits into sessions for sending to the MIP graph.

The CSR is responsible for translating file paths into ids and keep tracking on renames, deletes and more..

Params:
 * **SUPPORTED_FILE_TYPES** - supported file types which we will send actions on them to the MIP.
 * **ACTIONS_THRESHOLD** - if we end up with too much actions in one session, the CSR will throw an exception (because it will probably lead to memory error on the MIP graph)

### CsrFiles

The used CSR.

Keep track on files changes like rename and etc.

### CsrCode

Not in use.

Originally was created to extend CsrFiles and create actions for code segments.

## Entities.py

The entities which the MIP is familliar with.

**Session** contains several **Action** s

In addition, **Action** is hashable and comparable.

## Factory.py

The factory contains one main class: **Provider**.

The provider reads the *repositories.txt* list and ignore comments.
Each repository is loaded using the `DataExtractor` module and can be used later for tarin and test.

Usage:

```python
p = Provider(0.8) # default repositories.txt is used
# or
p = Provider(0.8, repo="vim/vim") # load only one repo
# or
p = Provider(0.8, repos_file="other.txt") # use other file to load the repositories list

p.X # is the train data
p.Y # is the test data

# p.X and p.Y are being accessed like this:
for repo in p.X:
    print(repo.name)
    for commit in repo:
        # commit is of type DataQuery/models/Commit
        # process commit..
        session = csr.commit_to_session(commit)
        # ...
```

## MIP.py

The MIP implementation