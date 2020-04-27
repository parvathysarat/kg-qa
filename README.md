# kg-qa
Question Answering using KG embeddings augmented by Text corpus

```qa_task_metaqa.ipynb``` notebook can be run to train on MetaQA dataset.

Folders :
- ```data``` contains training files:
  - processed MetaQA inputs
  - TransG embeddings & pickle file for MetaQA
  - processed dataset for OpenKE training
- ```embeddings``` : code to generate embeddings (openKE, transG)
- ```preprocessing output``` : entity to document mapping and processed WikiMovies corpus from which training files are extracted
- ```preprocessing``` : code for preprocessing Complex Web Questions and MetaQA

