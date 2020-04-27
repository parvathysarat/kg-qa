import json
import pandas as pd
from pprint import pprint

files = ["ComplexWebQuestions_train.json", "ComplexWebQuestions_dev.json"]


for file in files:
	file = "ComplexWebQues/"+file
	with open(file) as f:
		data = json.loads(f.read())
	# pprint(data)
	print(file)
	compositionality_types = [each['compositionality_type'] for each in data]
	questions = [each['question'] for each in data]
	webqsp_ids = [each['webqsp_ID'] for each in data]
	answers = [each['answers'][0]['answer'] for each in data]
	answer_ids = [each['answers'][0]['answer_id'] for each in data]
	ids = [each['ID'] for each in data]
	df = pd.DataFrame({'ID':ids, 'question':questions, 'answer':answers,'compositionality_type':compositionality_types, 'webqsp_ID' : webqsp_ids, 'answer_id':answer_ids})
	filename = file.split(".json")[0] + "_df.csv"
	df.to_csv(filename,index=None)
