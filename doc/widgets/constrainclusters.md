Constrain Clusters
==================

Calculate the connected-component labels for consensus clustered data.

**Inputs**

- Data: input dataset

**Outputs**

- Data: dataset with cluster added

The **Constrain Clusters** widget is used to calculate the consensus clustering and connected-component labels for some dataset.

**Image and Components**


Consensus Clustering
--------------------

Consensus clustering creates new clusters from the set of existing clusters.

| Cluster 1 | Cluster 2 | Consensus Cluster |
| :-------: | :-------: | :---------------: |
| C1        | C1        | C1                |
| C1        | C2        | C2                |
| C1        | C3        | C3                |
| C2        | C1        | C4                |
| C2        | C2        | C5                |
| C2        | C3        | C6                |

Connected-Component Labeling
----------------------------

Connected-component labeling assigns points in a map (grid) to the same cluster if there is some chain of same-cluster points connecting the two according to the defined connectivity kernel.

![](images/connectivity.png)

Example
-------



Notes
-----
