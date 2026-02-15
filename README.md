
# Personal News Feed

## Backend Component (Completed So Far)

- fetches recent articles using the NewsAPI `/everything` endpoint  
- cleans and stores structured data in `articles.json`  
- builds a TF-IDF index over article text  
- supports baseline relevance ranking using cosine similarity 

# Added:
- recency scoring 
- diversity penalty
- combined ranking formula
- user profile system with JSON storage
- interaction tracking (click, save, skip, complete)
- learning algorithm
- preference scoring
- stats + analysis


## How to Run

```bash
python fetch_news.py
python index.py
