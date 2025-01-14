# Welcome to RAGnostic!
## This is a reposity that contains a simple out-of-the-box file-type agostic RAG solution, written in python.

#### Stack:
- python, poetry
- aws S3
- pinecone DB
- openai

#### Usecase:
The intended use for this pipeline is to serve any retreival based chatbot with an effecive knowledge base of user uploaded documents. 

#### Opportunities this pipline lends itself to:
**UI/UX**
1. Presentable display of formatted version of uploaded document in Markdown. 
2. Version history to edit origional document in Markdown. (Must be careful to also generate new embeddings)
3. Additionally display JPEG of the document to the user.

**