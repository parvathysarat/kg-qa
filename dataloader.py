# -*- coding: utf-8 -*-
"""dataloader.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1NozFSlF7WBx5IXc4BpukLVFsi0NDJW6W
"""

import json
import numpy as np

from scipy.sparse import coo_matrix, csr_matrix
from tqdm import tqdm

def load_dict(filename):
    word2id = dict()
    with open(filename) as f_in:
        for line in f_in:
            word = line.strip().decode('UTF-8')
            word2id[word] = len(word2id)
    return word2id

class DataLoader():
  def __init__(self, documents,data, doc_entity_index, all_doc_texts, vocab_ids, relation_ids, entity_ids):
    self.documents = documents
    self.doc_entity_index = doc_entity_index 
    self.all_doc_texts = all_doc_texts 
    self.vocab_ids = vocab_ids
    self.relation_ids = relation_ids
    self.entity_ids = entity_ids
    self.ids_entity = {id:entity for entity, id in entity_ids.items()}
    self.data = []
    self.max_rel_doc, self.max_facts = 0,0
    with open(data) as f:
      for line in f:
        line = json.loads(line)
        self.data.append(line)
        self.max_rel_doc = max(self.max_rel_doc, len(line['passages']))
        self.max_facts = max(self.max_facts, 2*len(line['docs']['tuples']))
        # print(2*len(line['docs']['tuples']))
    self.num_data = len(self.data)
    self.batches = np.arange(self.num_data)
    # build entity maps
    self.max_local_entity = 0
    self.max_document_word = 40
    self.entity_maps = self.build_entity_maps()

    self.num_kb_relation = len(relation_ids)
    assert self.num_kb_relation==9
    print("Max facts",self.max_facts)
    print("KB relation",self.num_kb_relation)    
    self.max_query_word = 10
    self.local_entities = np.full((self.num_data, self.max_local_entity), len(self.entity_ids), dtype=int)
    self.kb_adj_mats = np.empty(self.num_data, dtype=object)
    self.kb_fact_rels = np.full((self.num_data, self.max_facts), self.num_kb_relation, dtype=int)
    self.q2e_adj_mats = np.zeros((self.num_data, self.max_local_entity, 1), dtype=float)
    self.query_texts = np.full((self.num_data, self.max_query_word), len(self.vocab_ids), dtype=int)
    self.rel_document_ids = np.full((self.num_data, self.max_rel_doc), -1, dtype=int) # the last document is empty
    self.entity_poses = np.empty(self.num_data, dtype=object)
    self.answer_dists = np.zeros((self.num_data, self.max_local_entity), dtype=float)
    
    self.prepare_data()

  def prepare_data(self):
    print("KB fact rels size",self.kb_fact_rels.shape)
    self.use_inverse_relation = False
    next_id = 0
    count_query_length = [0] * 50
    total_num_answerable_question = 0
    for sample in tqdm(self.data):
        if next_id%1000==0:print(next_id)
        # get a list of local entities
        global_to_local = self.entity_maps[next_id]
        
        # print((list(global_to_local.keys())))
        for global_entity, local_entity in global_to_local.items():
            if local_entity != 0: # skip question node
                self.local_entities[next_id, local_entity] = global_entity

        entity2fact_e, entity2fact_f = [], []
        fact2entity_f, fact2entity_e = [], []

        entity_pos_local_entity_id = []
        entity_pos_word_id = []
        entity_pos_word_weights = []

        # relations in local KB
        
        for i, tpl in enumerate(sample['docs']['tuples']):
            sbj, rel, obj = tpl
            if not self.use_inverse_relation:
                entity2fact_e += [global_to_local[self.entity_ids[sbj['text']]]]
                entity2fact_f += [i]
                fact2entity_f += [i]
                fact2entity_e += [global_to_local[self.entity_ids[obj['text']]]]
                self.kb_fact_rels[next_id, i] = self.relation_ids[rel['text']]
                
        # build connection between question and entities in it
        for j, entity in enumerate(sample['entities']):
            self.q2e_adj_mats[next_id, global_to_local[self.entity_ids[str(entity['text'])]], 0] = 1.0

        # connect documents to entities occurred in it
        
        for j, passage in enumerate(sample['passages']):
            document_id = passage['document_id']                
            if document_id not in self.doc_entity_index:
                continue
            (global_entity_ids, word_ids, word_weights) = self.doc_entity_index[document_id]
            entity_pos_local_entity_id += [global_to_local[global_entity_id] for global_entity_id in global_entity_ids]
            # print(global_entity_ids, type(global_entity_ids[0]))
            entity_pos_word_id += [word_id + j * self.max_document_word for word_id in word_ids]
            entity_pos_word_weights += word_weights

        # tokenize question
        count_query_length[len(sample['question'].split())] += 1
        for j, word in enumerate(sample['question'].split()):
            if j < self.max_query_word:
                if word in self.vocab_ids:
                    self.query_texts[next_id, j] = self.vocab_ids[word]
                else: 
                    self.query_texts[next_id, j] = self.vocab_ids['__unk__']

        # tokenize document
        for pid, passage in enumerate(sample['passages']):
            self.rel_document_ids[next_id, pid] = passage['document_id']

        # construct distribution for answers
        for answer in sample['answers']:
            keyword = 'text' if type(answer['kb_id']) == int else 'kb_id'
            if self.entity_ids[answer[keyword]] in global_to_local:
                self.answer_dists[next_id, global_to_local[self.entity_ids[answer[keyword]]]] = 1.0

        self.kb_adj_mats[next_id] = (np.array(entity2fact_f, dtype=int), np.array(entity2fact_e, dtype=int), np.array([1.0] * len(entity2fact_f))), (np.array(fact2entity_e, dtype=int), np.array(fact2entity_f, dtype=int), np.array([1.0] * len(fact2entity_e)))
        self.entity_poses[next_id] = (entity_pos_local_entity_id, entity_pos_word_id, entity_pos_word_weights)
        
        next_id += 1    



  def add_entity_to_map(self,entity_ids, entities, global_to_local):
    for ent in entities:
      ent_text = ent['text']
      ent_g_id = entity_ids[ent_text]
      if ent_g_id not in global_to_local:
        global_to_local[entity_ids[ent_text]] = len(global_to_local)

  def build_entity_maps(self):
    print(self.num_data)
    entity_maps = [None]*self.num_data
    total_local_entity =0.0
    next_id = 0
    print("Data ",len(self.data))
    
    for data in self.data:
      # print("id ",next_id)
      global_to_local = {}
      self.add_entity_to_map(self.entity_ids, data['entities'],global_to_local)
      self.add_entity_to_map(self.entity_ids, data['docs']['entities'], global_to_local)
      for doc in data['passages']:
        if doc['document_id'] not in self.documents:
          print(doc['document_id'], "not in docs")
          continue
        document = self.documents[int(doc['document_id'])]
        self.add_entity_to_map(self.entity_ids, document['document']['entities'], global_to_local)
        if 'title' in document: self.add_entity_to_map(self.entity_ids, document['title']['entities'], global_to_local)

      entity_maps[next_id] = global_to_local
      total_local_entity += len(global_to_local)
      self.max_local_entity = max(self.max_local_entity, len(global_to_local))
      next_id += 1

    return entity_maps
          
  def build_entity_pos(self, sample_ids):
      """Index the position of each entity in documents"""
      entity_pos_batch = np.array([], dtype=int)
      entity_pos_entity_id = np.array([], dtype=int)
      entity_pos_word_id = np.array([], dtype=int)
      vals = np.array([], dtype=float)

      for i, sample_id in enumerate(sample_ids):
          (entity_id, word_id, val) = self.entity_poses[sample_id]
          num_nonzero = len(val)
          entity_pos_batch = np.append(entity_pos_batch, np.full(num_nonzero, i, dtype=int))
          entity_pos_entity_id = np.append(entity_pos_entity_id, entity_id)
          entity_pos_word_id = np.append(entity_pos_word_id, word_id)
          vals = np.append(vals, val)
      return (entity_pos_batch.astype(int), entity_pos_entity_id.astype(int), entity_pos_word_id.astype(int), vals)
  
  def reset_batches(self, is_sequential=True):
      if is_sequential:
          self.batches = np.arange(self.num_data)
      else:
          self.batches = np.random.permutation(self.num_data)

  def build_kb_adj_mat(self, sample_ids, fact_dropout):

      mats0_batch = np.array([], dtype=int)
      mats0_0 = np.array([], dtype=int)
      mats0_1 = np.array([], dtype=int)
      vals0 = np.array([], dtype=float)

      mats1_batch = np.array([], dtype=int)
      mats1_0 = np.array([], dtype=int)
      mats1_1 = np.array([], dtype=int)
      vals1 = np.array([], dtype=float)

      for i, sample_id in enumerate(sample_ids):
          (mat0_0, mat0_1, val0), (mat1_0, mat1_1, val1) = self.kb_adj_mats[sample_id]
          assert len(val0) == len(val1)
          num_fact = len(val0)
          num_keep_fact = int(np.floor(num_fact * (1 - fact_dropout)))
          mask_index = np.random.permutation(num_fact)[ : num_keep_fact]
          # mat0
          mats0_batch = np.append(mats0_batch, np.full(len(mask_index), i, dtype=int))
          mats0_0 = np.append(mats0_0, mat0_0[mask_index])
          mats0_1 = np.append(mats0_1, mat0_1[mask_index])
          vals0 = np.append(vals0, val0[mask_index])
          # mat1
          mats1_batch = np.append(mats1_batch, np.full(len(mask_index), i, dtype=int))
          mats1_0 = np.append(mats1_0, mat1_0[mask_index])
          mats1_1 = np.append(mats1_1, mat1_1[mask_index])
          vals1 = np.append(vals1, val1[mask_index])

      return (mats0_batch, mats0_0, mats0_1, vals0), (mats1_batch, mats1_0, mats1_1, vals1)



  def get_batch(self, iteration, batch_size, fact_dropout):

      sample_ids = self.batches[batch_size * iteration: batch_size * (iteration + 1)]
      
      return self.local_entities[sample_ids], \
              self.q2e_adj_mats[sample_ids], \
              (self.build_kb_adj_mat(sample_ids, fact_dropout=fact_dropout)), \
              self.kb_fact_rels[sample_ids], \
              self.query_texts[sample_ids], \
              self.build_document_text(sample_ids), \
              (self.build_entity_pos(sample_ids)), \
              self.answer_dists[sample_ids]


  def build_document_text(self, sample_ids):
      """Index tokenized documents for each sample"""
      document_text = np.full((len(sample_ids), self.max_rel_doc, self.max_document_word), len(self.vocab_ids), dtype=int)
      for i, sample_id in enumerate(sample_ids):
          for j, rel_doc_id in enumerate(self.rel_document_ids[sample_id]):
              if rel_doc_id not in self.all_doc_texts:
                  continue
              document_text[i, j] = self.all_doc_texts[rel_doc_id]
      return document_text

