#%% GOAL Demo tool that converts ICD10 to SNOMED

# * Points to communicate



#%%
import pandas as pd
import numpy as np
import networkx as nx


#%% get ICD codes that one might want to convert
icd10_parkinsons = 'G20'

#Find more codes...
#"/home/selah/Data/Whitney_Guthrie_Autism_2018_06/raw_data/CP_DeID_visitdiagnoses.csv"
#/home/selah/Data/Whitney_Guthrie_Autism_2018_06/raw_data/CP_DeID_problemlist.csv
#df = pd.read_csv("/home/selah/Data/Whitney_Guthrie_Autism_2018_06/raw_data/CP_DeID_problemlist.csv")
#chop_codes = df[df.CODE_TYPE=='ICD10']['CODE']

#%% Define class!

def uconcepts_from_edges(dfedges): 
    c0 = dfedges.columns[0]
    c1 = dfedges.columns[1] 
    concepts = dfedges[c0].append(dfedges[c1])
    return concepts.drop_duplicates()


class ICD10_to_weighted_SNOMEDCT:


    def __init__(self, init_graph=nx.DiGraph()):
        self.G = init_graph
        self.loaded_snomedct_concepts = pd.Series() 
        self.snomed_labels = None
        self.icd_edges = None
        pass
    
    
    #TODO - make this so it can be generated from a graph directly!
    
    def load_SNOMEDCT(self, snopath):

        print("Loading relationships...")
        dfrel = pd.read_csv(snopath + "/Terminology/sct2_Relationship_Snapshot_INT_20180731.txt", sep='\t')
        relationship_isA_id = 116680003
        dfrel_graph = dfrel[dfrel.typeId == relationship_isA_id] #The "Is a" relationship

        print("Loading descriptions...")
        dfdesc = pd.read_csv(snopath + "Terminology/sct2_Description_Snapshot-en_INT_20180731.txt", sep='\t')
        attribute_conceptName_id = 900000000000003001
        dfdesc_graph = dfdesc[dfdesc.typeId == attribute_conceptName_id]

        edges_to_load = dfrel_graph[['destinationId','sourceId']]
        self.loaded_snomedct_concepts = uconcepts_from_edges(edges_to_load)
        labels_to_load = dfdesc_graph[['conceptId', 'term']].set_index('conceptId').loc[self.loaded_snomedct_concepts]
        self.snomed_labels = labels_to_load
        self.G.add_edges_from(edges_to_load.values)
        self.G.edges
        
        print("Processing labels...")
        #add labels to nodes
        for (nid, label) in labels_to_load.iterrows():    
            if nid in self.G:
                self.G.nodes[nid]['label'] = label.term
        print ("Done...")

    def get_graph(self):
        return self.G

    #For now this shoudl be run after load_SNOMEDCT or strange behavior may happen
    def load_ICD10_map(self, icdpath):

        print("Loading UMLS map...")
        dficd10map = pd.read_csv(icdpath + 'tls_Icd10cmHumanReadableMap_US1000124_20180301.tsv', sep='\t')

        #TODO - decouple the two load functions?  get rid of self.loaded_snomedct_concepts
        #OR document the shit out of it
        
        maps_of_loaded_concepts = dficd10map.merge(self.loaded_snomedct_concepts.to_frame('poop'), left_on='referencedComponentId', right_on='poop')

        edges_to_load = maps_of_loaded_concepts[['referencedComponentId','mapTarget']].dropna()
        self.icd_edges = edges_to_load #saving so I can play with is
        
        icd_labels = dficd10map[['mapTarget', 'mapTargetName']].dropna().drop_duplicates().set_index('mapTarget')
        icds_to_label = edges_to_load['mapTarget'].drop_duplicates()
        labels_to_load = icd_labels.loc[icds_to_label]
        
        self.G.add_edges_from(edges_to_load.values)
        self.G.edges
        
        print("Processing labels...")
        #add labels to nodes
        for (nid, label) in labels_to_load.iterrows():    
            if nid in self.G:
                self.G.nodes[nid]['label'] = label.mapTargetName

        print("Done...")

    def get_ancestor_stats(self, icd):
        root_node = 138875005
        ancestors = nx.ancestors(self.G, icd)
        
        ancestor_stats = []
        for ancestor in ancestors:
            label = self.G.nodes[ancestor]['label']
            depth = nx.shortest_path_length(self.G, root_node, ancestor)
            height = nx.shortest_path_length(self.G, ancestor, icd)
            in_degree = self.G.in_degree(ancestor)
            out_degree = self.G.out_degree(ancestor)
            row = (ancestor, depth, height, in_degree, out_degree, label) 
#            print(row)
            ancestor_stats.append(row)
        return pd.DataFrame(ancestor_stats, columns=['ancestor', 'depth', 'height', 'in_degree', 'out_degree', 'label']).set_index('ancestor').sort_values(['height','depth'])


    def get_ancestor_weights(self, icd):
        self.ancestor_stats = self.get_ancestor_stats(icd)
        self.ancestor_stats['weights'] = 0
        self.get_ancestor_weights_recr(icd)
        return self.ancestor_stats

    
    def get_ancestor_weights_recr(self, nid, weight=1, max_rcr_depth=10, rcr_depth=0):
        if nid in self.ancestor_stats.index:
            self.ancestor_stats.loc[nid,'weights'] += weight
        else:
            print("Index {} not in ancestor set".format(nid))
        parents = list(self.G.predecessors(nid))
        num_parents = len(parents)
        stop_nodes = [52645000]
        if num_parents>0 and rcr_depth<max_rcr_depth and not (nid in stop_nodes):
            new_weight = weight/num_parents
            for parent in parents:
                self.get_ancestor_weights_recr(parent, new_weight, max_rcr_depth, rcr_depth+1)

    def get_snomeds(self, icd10):
        #TO IMPLEMENT
        pass


#%%

datadir = "/home/selah/Data/SnomedCT/"

mapper = ICD10_to_weighted_SNOMEDCT()

mapper.load_SNOMEDCT(datadir +  "SnomedCT_InternationalRF2_PRODUCTION_20180731T120000Z/Snapshot/") #MANY assumptions about format

mapper.load_ICD10_map(datadir + "SnomedCT_UStoICD10CM_20180301T120000Z/") #MANY assumptions about format

#%% TEST IT

testmapper = ICD10_to_weighted_SNOMEDCT(mapper.G)

#parkinson_ancestors = testmapper.get_ancestor_stats('G20')

parkinson_weights = testmapper.get_ancestor_weights('G20')

parkinson_weights

weights_f84 = testmapper.get_ancestor_weights('F84.0')

sarc_ancestors = testmapper.get_ancestor_weights('D86.9')

ancestors_I07_1 = testmapper.get_ancestor_weights('I07.1')



 
#parkinson_ancestors = testmapper.get_ancestor_stats(49049000)

#%% Investigate parents
mapper.G.nodes[191690004]
p = list(mapper.G.predecessors(191690004))
mapper.snomed_labels.loc[p]

get_node = lambda s: mapper.G.nodes[s]
get_node(254206003)

get_parents = lambda s: mapper.snomed_labels.loc[mapper.G.predecessors(s)]
get_parents(254206003)


#%% Find how many SNOMED codes each ICD code has
import matplotlib.pyplot as plt

icd_map_count = mapper.icd_edges.groupby('mapTarget').count().sort_values('referencedComponentId')
plt.hist(icd_map_count.referencedComponentId, log=True, bins=50)

#%% Test where weight gets lost

weights_f84.groupby('depth').sum()
weights_f84.groupby('height').sum()


#%%   Test dispersion

nx.dispersion(testmapper.G, 110359009, 'G20')
nx.dispersion(testmapper.G, 'G20', 110359009)














































