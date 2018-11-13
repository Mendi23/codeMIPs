# AnalysisModule

This module has several different scripts for analyze the data.

## DataRetrieval.py

Extracting the `data.txt` for each repo.

In that file can be found a table with line for each commit in the repository
and details about the commit such as:

 * Which files (ids) got modified or added
 * User name for this commit
 * centrality score for modified/added files
 * Proximity score for modified/added files
 * changeExtent score for modified/added files

## optimization.py

This script is responsible of the alpha, beta, gamma optimization.

We run the MIP on each repository for the first 80% commits and then test our score for the rest 20% commits.

Using `scipy.optimize` module we try to maximize the score we get for all the repositories.


## repositoriesData.py

For each repo, prints how much commits it has.

## VisualizeGraph.py

For each repo, running the MIP on each commit one by one.

Saving several things on the way:

* Per User:
  * Commits (number of commits)
  * Total objects the user changed (across all commits)
  * Total score - *score of one commit is the sum of the DOI of the files user changed divided by total DOI of all files in repo in that moment*.
    Total score is the sum of all that scores per user.
  * Total Top3 and Top5: `top3` or `top5` are the number of files that have the highest DOI (top 3 or top5). <br/>
    We count how much out of these files the user actually did change in a specific commit and this is the top3 or top5 value. <br/>
    At the end we sum all top3/top5 across all user commits. <br />
    More explanation on score and top3/top5 can be found at [Results/README.md](../Results/README.md).
* Per Commit:
  * Commit number
  * The committer (user)
  * top5/top3 hits as described (but not per user this time)
  * Score

We save summarize plot for each user and for each state of the MIP graph.
Pay attention that the plot for user is only for users who did more than 10 commits.

In addition, we write a data.txt file.

More on this results can be found under `Results` directory (in the README.md there)


---

## MISC:

### repos_by_commits.txt
The output from `repositoriesData.py`.

### repositories.txt
The repositories list.
Comments are supported here.

The file is processed by `Factory.py`
