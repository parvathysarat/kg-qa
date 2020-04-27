# kg-qa
Question Answering using KG embeddings augmented by Text corpus

Run qa_task_metaqa.ipynb notebook to train on MetaQA dataset.

Folders :
- ./data/ contains training files:
  - preprocessed MetaQA corpus, TransG embeddings for MetaQA and processed dataset for OpenKE training.
- ./embeddings/ contains code to generate embeddings (openKE, transG)
- ./preprocessing output/ contains entity to document mapping and processed WikiMovies corpus (json) from which training files are extracted
- ./preprocessing/ : code for preprocessing Complex Web Questions and MetaQA

