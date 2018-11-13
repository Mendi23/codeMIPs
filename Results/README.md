# Results

All our graphs and data we have produced during our research can be found here.

## Explanation of the directory tree

Each folder here represent one repository that we processed.

For example: `tensorflow` represents the results for the [tensorflow/tensorflow](/tensorflow/tensorflow/) repository

In every folder there are sub-folders with name formatted like this:
`0.2_0.6_0.2` those numbers represents respectively the `alpha`, `beta`, `gamma`
that we used on the MIP in order to produce the results inside this sub-folder.

## User graphs (created by VisualizeGraph.py)

User graphs are named by the user so if the graph is about bob
the name of the file will be bob.png and the graph will look like this:

![user graph here](https://github.com/Mendi23/codeMIPs/raw/master/Results/heapdict/0.2_0.6_0.2/User%20graphs/shane.png)

**Explanation:**

This example is taken from heapdict repository with 0.2, 0.6, 0.2 as alpha, beta and gamma.

The user shane is a colaborator in this repository and had in total around 11 commits
as can be seen as x-axis max value (the line is slightly overlapping 10).
The commits are ordered and numbered from the first commit the user did to the last one.

In this example graph we can see that **on the 6th commit**:

 * our model accuracy is around 0.5.
 * the top_3 accuracy is around 0.5 as well.
 * the top_5 accuracy is 1 which means 100%. **Pay attention** that this repository has hardly 4 python files so we will always get 100% on top_5.

Note that the plot for user is only for users who did more than 10 commits.

#### The meaning of "model accuracy" is:
On each iteration the model gave us a grade (degree of interest - a.k.a. DOI) for each file in the project,
so the file with the highest grade will be most likely edited by the user in the next commit. <br/>
For clarity let's assume the repo has only two files and call them F1 and F2.
And let's say F1 has DOI of 3 and F2 has DOI of 1.
Total DOI is 4.

Let's say the user modified only the file F1 so our accuracy will be: F1_DOI / total_DOI
That is - 3/4.

And in general the accuracy will be: `(Sum of DOI of files the user actually modified) / (total DOI of all files)`

#### The meaning of top3/top5:
On each commit we asking the model (MIP) to give as all the files in the
repository ranked by DOI (degree of interest) of the current user.

Let's declare:
 * top3_files - Means the 3 files that got the highest DOI score at a specific moment out of all the files in the repo.
 * top5_files - Means the same but for the 5 highest scores.

Now, what we are doing next is to check how much files out of top3_files/top5_files
where actually got changed by this user in the specific commit.

The actual value of top_3 will be a number between 0 to 3 which represents
the actual number of files that got changed out of the top3_files. <br />
The actual value of top_5 will be a number between 0 to 5 respectively.

Before we got to the end, pay attention that if only one file has been changed
the maximum value of top_3 or top_5 can be 1.

At the end, the value you see in the graph is the value of top_3
divided by `min(3, number of files that changed)`
and the value of top5 divided by `min(5, number of files that changed)`

So in our case that we have only 4 files, <br/>
The number of files that changed is less than 5
and top5_files will contains all the files in the repo.<br/>
In conclusion => `top_5/total` will always be 1.

## MIP Graph (created by VisualizeGraph.py)

MIP graphs are numbered. Each graph represents a state in the repository.
Actually the number of the graph is the number of commits made to the repo so far.

MIP graph will look like this:

![mip graph here](https://github.com/Mendi23/codeMIPs/raw/master/Results/heapdict/0.2_0.6_0.2/MIP%20graphs/4.png)

**Explanation:**

This example is taken from heapdict repository with 0.2, 0.6, 0.2 as alpha, beta and gamma.

We can see here that 3 commits have been made so far to the repository (the title is zero-based).
In this state The user daniel did the last commit to the file with id 7 (you can see that it has bold border).

The DOI of files 5 and 7 are the highest DOI (can be identified by the color red)
and indeed the user made change to file number 7.

Furthermore, the repository has 4 files so far.


## res.txt (created by VisualizeGraph.py)

In res.txt there is extra information about the model results.
Each line represents a commit.

The data which can be found:

* The actual score which we have on a specific commit (score := accuracy as explained above)
* Top 3/5 - how much files that were at the top 3/5 in manners of degree of intereset were actually changed in this commit.
* The user name that made the change.
* Which files (only ids) got changed.

And at the and there is a summary for the whole table. <br />
In addition, there is a summary for each user.


## data.txt (created by DataRetrieval.py)

Summarize for each commit in the repository.

This is not depend on the alpha/beta/gamma so the file can be found right under the repository folder
