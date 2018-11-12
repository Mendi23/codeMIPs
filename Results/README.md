# Results

All our graphs and data we have produced during our research can be found here.

## Explanation of the directory tree

Each folder here represent one repository that we processed.

For example: `tensorflow` represents the results for the [tensorflow/tensorflow](https://github.com/tensorflow/tensorflow/) repository

In every folder there are sub-folders with name formatted like this:
`0.2_0.6_0.2` those numbers represents respectively the `alpha`, `beta`, `gamma`
that we used on the MIP in order to produce the results inside this sub-folder.

## User graphs

User graphs are named by the user so if the graph is about bob
the name of the file will be bob.png and the graph will look like this:

![user graph here]()

**Explanation:**

This example is taken from ----- repository with 0.2, 0.6, 0.2 as alpha, beta and gamma.
The user ------ is a colaborator in this repository and had in total --X-- commits
as can be seen as x-axis max value.
The commits are ordered and numbered from the first commit the user did to the last one.

In this example we can see that on the --Y-- commit our model accuracy was ---Z---.

The meaning of "model accuracy" is that: <br/>
On each iteration the model gave us a grade (degree of interest - a.k.a. DOI) for each file in the project,
so the file with the highest grade will be most likely edited by the user in the next commit. <br/>
For clarity let's assume the repo has only two files and call them F1 and F2.
And let's say F1 has DOI of 3 and F2 has DOI of 1.
Total DOI is 4.
The user modified only the file F1 so our accuracy will be: F1_DOI / total_DOI
That is - 3/4.

And in general the accuracy will be: `(Sum of DOI of files the user actually modified) / (total DOI of all files)`

//////// yadaddadadyadyad//////////

## MIP Graph

MIP graphs are numbered. Each graph represents a state in the repository.
Actually the number of the graph is the number of commits made to the repo so far.

MIP graph will look like this:

![mip graph here](https://github.com/Mendi23/codeMIPs/raw/master/Results/heapdict/0.2_0.6_0.2/4.png)

**Explanation:**

This example is taken from heapdict repository with 0.2, 0.6, 0.2 as alpha, beta and gamma.

We can see here that 3 commits have been made so far to the repository (the title is zero-based).
In this state The user daniel did the last commit to the file with id 7 (you can see that it has bold border).

The DOI of files 5 and 7 are the highest DOI (can be identified by the color red)
and indeed the user made change to file number 7.

Furthermore, the repository has 4 files so far.


## res.txt

In res.txt there is extra information about the model results.
Each line represents a commit.

The data which can be found:

* The actual score which we have on a specific commit (score := accuracy as explained above)
* Top 3/5 - how much files that were at the top 3/5 in manners of degree of intereset were actually changed in this commit.
* The user name that made the change.
* Which files (only ids) got changed.

And at the and there is a summary for the whole table



