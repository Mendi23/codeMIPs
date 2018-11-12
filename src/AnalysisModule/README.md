# AnalysisModule

This module has several different scripts for analyze the data

## DataRetrieval.py

## optimization.py

This script is responsible of the alpha, beta, gamma optimization.

We run the MIP on each repository for the first 80% commits and then test our score for the rest 20% commits.

Using `scipy.optimize` module we try to maximize the score we get for all the repositories.

## plotPerUser.py

For each repo, running the MIP on each commit one by one.

Saving how much commits done per user and for each commits what was the accuracy of the model.

At the end, saving a summarize plot.

## repositoriesData.py

For each repo, prints how much commits it has.

## VisualizeGraph.py

---

## MISC:

### repos_by_commits.txt
The output from `repositoriesData.py`.

### repositories.txt
The repositories list.
Comments are supported here.

The file is processed by `Factory.py`
