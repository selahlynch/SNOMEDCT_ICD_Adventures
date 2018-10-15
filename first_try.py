# GOAL - read relevent SNOMED/ICD data into various graph structures

import pandas as pd
import numpy as np
import networkx as nx

#%% get relevant SNOMEDCT/ICD data into dataframes

#datadir = "/Users/selah/Data/SnomedCT/SnomedCT_InternationalRF2_PRODUCTION_20180731T120000Z/Snapshot/"
datadir = "/home/selah/Data/SnomedCT/"

snomedctdir = datadir + "SnomedCT_InternationalRF2_PRODUCTION_20180731T120000Z/Snapshot/"

dfrel = pd.read_csv(snomedctdir + "/Terminology/sct2_Relationship_Snapshot_INT_20180731.txt", sep='\t')
relationship_isA_id = 116680003
dfrel_graph = dfrel[dfrel.typeId == relationship_isA_id] #The "Is a" relationship

dfdesc = pd.read_csv(snomedctdir + "Terminology/sct2_Description_Snapshot-en_INT_20180731.txt", sep='\t')
attribute_conceptName_id = 900000000000003001
dfdesc_graph = dfdesc[dfdesc.typeId == attribute_conceptName_id]

icdmapdir = datadir + "SnomedCT_UStoICD10CM_20180301T120000Z/"

dficd10map = pd.read_csv(icdmapdir + 'tls_Icd10cmHumanReadableMap_US1000124_20180301.tsv', sep='\t')


#%% load SNOMEDCT data into NetworkX graph structure

def uconcepts_from_edges(dfedges): 
    c0 = dfedges.columns[0]
    c1 = dfedges.columns[1] 
    concepts = dfedges[c0].append(dfedges[c1])
    return concepts.drop_duplicates()

#%%

G = nx.DiGraph()

edges_to_load = dfrel_graph[['sourceId', 'destinationId']]
concepts_to_label = uconcepts_from_edges(edges_to_load)
labels_to_load = dfdesc_graph[['conceptId', 'term']].set_index('conceptId').loc[concepts_to_label]

G.add_edges_from(edges_to_load.values)
G.edges

#add labels to nodes
for (nid, label) in labels_to_load.iterrows():    
    if nid in G:
        G.nodes[nid]['label'] = label

#test some nodes to see that they exist and have labels
G.node[10002003]
G.node[19130008]
G.node[100012001]

#%% load SNOMEDCT_to_ICD10 map into NetworkX graph structure


maps_of_loaded_concepts = dficd10map.merge(concepts_to_label.to_frame('poop'), left_on='referencedComponentId', right_on='poop')

edges_to_load = maps_of_loaded_concepts[['referencedComponentId','mapTarget']].dropna()

icd_labels = dficd10map[['mapTarget', 'mapTargetName']].dropna().drop_duplicates().set_index('mapTarget')
icds_to_label = edges_to_load['mapTarget'].drop_duplicates()
labels_to_load = icd_labels.loc[icds_to_label]

G.add_edges_from(edges_to_load.values)
G.edges

#add labels to nodes
for (nid, label) in labels_to_load.iterrows():    
    if nid in G:
        G.nodes[nid]['label'] = label

G.node['R52']
G.node['A41.9']
G.node['R07.9']

#%% load SNOMEDCT into RDF graph structure

# Great docs here: 
# https://rdflib.readthedocs.io/en/stable/index.html

# If Spyder throws error, don't close it, just put in background and ignore

import rdflib  #pip install rdflib

rdfG = rdflib.Graph()

#%%
from rdflib import Graph
from rdflib import URIRef
from rdflib import Literal

r_isa = URIRef("relationship/isA")
r_map = URIRef("relationship/map")
r_lab = URIRef("relationship/label")


#%% Load SNOMED CT to rdflib

edges_to_load = dfrel_graph[['sourceId', 'destinationId']]
concepts_to_label = uconcepts_from_edges(edges_to_load)
labels_to_load = dfdesc_graph[['conceptId', 'term']].set_index('conceptId').loc[concepts_to_label]

g = Graph()

for (idx, (s,o)) in edges_to_load.iterrows():
    g.add((Literal(s), r_isa, Literal(o)))


for (s, vals) in labels_to_load.iterrows():
    o=vals[0]
    g.add((Literal(s), r_lab, Literal(o)))

#%%
for (s, p, o) in g:
    print ((s, p, o))
#%%
print( g.serialize(format='turtle').decode("utf-8"))


#%% Find root node

labels = dfdesc_graph[['conceptId', 'term']].set_index('conceptId')

rand_id = labels.sample().iloc[0].name
rand_id
rnode = G.node[rand_id]
rnode

list(nx.neighbors(G, rand_id))
list(G.predecessors(rand_id))
list(G.successors(rand_id))

#%%

def print_node(nid):
    n = G.node[nid]
    print((nid, n['label'].term))
    parents = list(G.successors(nid))
    if len(parents)>0:
        print_node(parents[0])

#%%    
rand_id = labels.sample().iloc[0].name
print_node(rand_id)


#%%  Establish a Horizon of SNOMEDCT codes

snomed_root = 138875005
G.node[snomed_root]  # doesn't exist :/

list(G.predecessors(snomed_root))






