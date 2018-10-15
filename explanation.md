# Points to communicate:
* We are looking for which SNOMED codes associate with X (recommendation of yoga, diagnosis of lyme disease)
* CHALLENGES: 
* In this case we don't have a 1 to 1 map from ICD to SNOMED
* Also, SNOMED is roughly hierarchical
* This OHDSI example explains this issue and a solution... BUT the solution works for querying patients, not for association studies
    * http://www.ohdsi.org/web/wiki/doku.php?id=documentation:vocabulary:mapping
  

# PROPOSAL/HUNCH
* assume complete ignorance about which ICD-SNOMEDCT map is most meaningful
* when we have an instance of a person who has been recommended yoga...
* dole out weights to each snomed code to which the ICD code is mapped 
* then, for each of the snomed codes who were doled out weights, dole out weights to the parents of that code
* continue recursively up the tree
* this is the naiive probability that SNOMED code X applies to this instance

# DEMO


# CHALLENGES/FUTURE WORK










