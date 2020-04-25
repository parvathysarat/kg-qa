import json
import pandas as pd
from pprint import pprint
from transG import *

def complexWebQ(files):	

	all_entities = []

	for file in files:
		file = "ComplexWebQues/"+file
		with open(file) as f:
			data = json.loads(f.read())
		# pprint(data)
		print(file)
		pprint(data[0])
		compositionality_types = [each['compositionality_type'] for each in data]
		questions = [each['question'] for each in data]
		webqsp_ids = [each['webqsp_ID'] for each in data]
		answers = [each['answers'][0]['answer'] for each in data]
		answer_ids = [each['answers'][0]['answer_id'] for each in data]
		ids = [each['ID'] for each in data]
		df = pd.DataFrame({'ID':ids, 'question':questions, 'answer':answers,'compositionality_type':compositionality_types, 'webqsp_ID' : webqsp_ids, 'answer_id':answer_ids})
		filename = file.split(".json")[0] + "_df.csv"
		df.to_csv(filename,index=None)
		all_entities.append(answer_ids)
		print(len(answer_ids))

	print(all_entities)

def preprocess(kb_triple):
	kb_triple = kb_triple.strip("\n").split("|")
	return kb_triple

def metaQA(kb_file):

	data = open(kb_file, encoding = 'utf-8').readlines()
	meta_entities = []
	meta_relations = []
	for entities in list(map(preprocess,data)):
		meta_entities.append(entities[0])
		meta_entities.append(entities[2])
		meta_relations.append(entities[1])
	return set(meta_entities), set(meta_relations)


def main():
	complex_files = ["ComplexWebQuestions_train.json", "ComplexWebQuestions_dev.json"]
	# complex_entities = complexWebQ(complex_files)

	metaqa_file = "kb.txt"
	meta_entities, meta_relations = metaQA(metaqa_file)
	# print(meta_relations,meta_entities)
	ent = open("MetaQA entities.txt","w")
	ent.write("\n".join(meta_entities))
	ent.close()
	rel = open("MetaQA relations.txt","w")
	rel.write("\n".join(meta_relations))	
	rel.close()

if __name__ == "__main__":
	main()