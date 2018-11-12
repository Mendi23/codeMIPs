# DataModule

This module is responsible on the data download,
parsing to known common objects, split to train and test and cache.


## DataQuery.py

The main module. Here you can find two classes,
the main class you should use is `DataExtractor`.

File constants parameters:
 * **FETCH_REPO** - Sync the local repo. After downloading a repository, The module won't download it again so if you want to stay sync with remote changes set this const to True
 * **CACHE_THE_DATA** - Cache the extracted data to local directory. **Pay attention** if you change how the data is processed you need to delete the cached data before next run.
 * **PER_PAGE** - if **CACHE_THE_DATA** is True, How much commits save per json file.


### GithubQuery
Responsible for downloading the repository from Github
and store it on the local storage.

Usage:

```python
query = GithubQuery.create(local_dir, repouri)
query.num_of_commits()
query.repo_iterate_commits()
```

Params:
 * **local_dir** - name of the local directory for download repositories
   (the module will create subdirectory for each repo automaticlly so don't need to create directory for each repo)
 * **repouri** - the repository uri e.g. "torvalds/linux"

### DataExtractor
This class is using the `GithubQuery` this class for downloading repos and:
 * Parse each commit to a known object (will be explained below)
 * Split to train/test (by ratio or explicit number)
 * Cache the extracted data for fast using later

Usage:

```python
data_extractor = DataExtractor(local_dir, repouri, ratio=0.8)
# or
data_extractor = DataExtractor(local_dir, repouri, k_commits=10)

X = data_extractor.get_train()
Y = data_extractor.get_test()
```

Params:
 * **local_dir** and **repouri** as explained above
 * **ratio** - the ratio: (# train commits) / (# total commits)
 * **k_commits** - k commits = number of **test** commits.


## models.py

In this file we created the "interface" for the known common objects.
Only necessary data is saved into the objects.

All objects supports serialize and deserialize into a file
in order to create the cache files (currently jsons files).

### Commit
Commit details (contain all below types)

### User
User details (name and email)

### FileChangeset
Details about changes in one file (as part of the commit).
Contains Patches for each file.

### Patch
One file can have several patches.
Patch in one file means block of lines which got changed.

Currently we only processing the metadata of each commit
which means we just processing the files and not the content,
so the content of each commit (i.e. the Patches) are not used.

Contains:
 * section header - header provided by git. Can be empty if the change was in the global scope.
 * source_lines - lines which were before the change and got removed.
 * target_lines - new lines which have been added.

Params:
 * **SERIALIZE_CONTENT** - Set to true in order to save (and load) the content lines.
 Because the content lines are taking memory and currently not in used this param is `False`.

### ChangeEnum
Type of the change:

ADDED = 0
MODIFIED = 1
RENAMED = 2
DELETED = 3


## utils.py

Helper methods and classes for:
 * Creating local files
 * Storing the cache
 * Old generator (not used)

---

## More info about caching

Each repository is downloaded once as described.

The second operation which is time consuming is to create the **Commit** objects.
Parsing and processing the difference between commits is time consuming so there is a "second level cache".

The cache is saved inside `Storage_cache`.

To disable it, set the constant `CACHE_THE_DATA` to False.

### Known Issues (all caused by cache)

#### I can't debug the DataQuery.py (DataExtractor)
*Issue:* Even if I have a breakpoint at DataQuery.py
and I saw that the code **should** pass there - the breakpoint doesn't hit.

*Solution:* Pay attention that **the DataExtractor run only once in a lifetime!**
After one run - all the extracted data are getting cached in `Storage_cache`.
Delete the files under `Storage_cache` and all should be solved

#### All files' content are empty
*Issue:* All Patches objects are empty

*Solution:* It is probaply becaues you ran the DataExtractor once with `Patch.SERIALIZE_CONTENT` set to False
If set it to True doesn't solve the problem you need to erase your cache.
