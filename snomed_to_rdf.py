import pandas as pd
import numpy as np

#GOAL - load simple snomed data into RDF format

datadir = "/home/selah/Data/SnomedCT/"
snopath = datadir +"SnomedCT_InternationalRF2_PRODUCTION_20180731T120000Z/Snapshot/"

icdmappath = datadir +"SnomedCT_UStoICD10CM_20180301T120000Z/" # will use later?

#%% Load SNOMED Data into Dataframe
print("Loading relationships...")
dfrel = pd.read_csv(snopath + "Terminology/sct2_Relationship_Snapshot_INT_20180731.txt", sep='\t')
relationship_isA_id = 116680003
dfrel_graph = dfrel[dfrel.typeId == relationship_isA_id] #The "Is a" relationship

print("Loading descriptions...")
dfdesc = pd.read_csv(snopath + "Terminology/sct2_Description_Snapshot-en_INT_20180731.txt", sep='\t')
attribute_conceptName_id = 900000000000003001
dfdesc_graph = dfdesc[dfdesc.typeId == attribute_conceptName_id]

#%% Load ICD10 Data into Dataframe
print("Loading UMLS map...")
dficd10map = pd.read_csv(icdmappath + 'tls_Icd10cmHumanReadableMap_US1000124_20180301.tsv', sep='\t')


#%%
def uconcepts_from_edges(dfedges): 
    c0 = dfedges.columns[0]
    c1 = dfedges.columns[1] 
    concepts = dfedges[c0].append(dfedges[c1])
    return concepts.drop_duplicates()


#%%
from rdflib import Graph
from rdflib import URIRef
from rdflib import Literal

r_ischild = URIRef("relationship/isChildOf")
r_map = URIRef("relationship/map")
r_lab = URIRef("relationship/label")

concept_uri_snomed = lambda c: URIRef("concept/snomed/" + str(c))
concept_uri_icd = lambda c: URIRef("concept/icd10/" + str(c))


#%% Load SNOMED CT to rdflib

print("Loading SNOMED to RDF...")

edges_to_load_snomed = dfrel_graph[['sourceId', 'destinationId']]#.sample(500)
loaded_concepts_list_snomed = uconcepts_from_edges(edges_to_load_snomed)
labels_to_load_snomed = dfdesc_graph[['conceptId', 'term']].set_index('conceptId').loc[loaded_concepts_list_snomed]

#%%   Load snomed concepts and labels

g = Graph() 

for (idx, (s,o)) in edges_to_load_snomed.iterrows():
    g.add((concept_uri_snomed(s), r_ischild, concept_uri_snomed(o)))

for (s, vals) in labels_to_load_snomed.iterrows():
    o=vals[0]
    g.add((concept_uri_snomed(s), r_lab, Literal(o)))

#%% Load ICD10 concepts, maps and labels
    
print("Loading ICD to RDF...")

maps_of_loaded_concepts = dficd10map.merge(loaded_concepts_list_snomed.to_frame('poop'), left_on='referencedComponentId', right_on='poop')

edges_to_load_icdmap = maps_of_loaded_concepts[['referencedComponentId','mapTarget']].dropna()

icd_labels = dficd10map[['mapTarget', 'mapTargetName']].dropna().drop_duplicates().set_index('mapTarget')
icds_to_label = edges_to_load_icdmap['mapTarget'].drop_duplicates()
labels_to_load_icd10 = icd_labels.loc[icds_to_label]

#%%

for (idx, (sno, icd)) in edges_to_load_icdmap.iterrows():
    g.add((concept_uri_icd(icd), r_map, concept_uri_snomed(sno)))

for (icd, vals) in labels_to_load_icd10.iterrows():
    lab=vals[0]
    g.add((concept_uri_icd(icd), r_lab, Literal(lab)))
    
#%%    
print("Writing to turtle file...")

%time g.serialize(destination=datadir + 'SNOMED_ICD_selah.ttl', format='turtle')
