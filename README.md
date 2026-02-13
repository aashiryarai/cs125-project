
# Personal News Feed

## Backend Component (Completed So Far)

- fetches recent articles using the NewsAPI `/everything` endpoint  
- cleans and stores structured data in `articles.json`  
- builds a TF-IDF index over article text  
- supports baseline relevance ranking using cosine similarity  

## How to Run

```bash
python fetch_news.py
python index.py
