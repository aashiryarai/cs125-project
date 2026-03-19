# Personal News Feed

A personalized news recommendation system that combines article retrieval, TF-IDF search, user preferences, context-aware ranking, and interaction-based learning in a web interface.

---

## Overview

This project builds a full pipeline for personalized news delivery:

- retrieves articles from NewsAPI  
- processes and indexes them using TF-IDF  
- ranks them using a hybrid scoring system  
- adapts recommendations based on user behavior  

The system continuously improves by learning from user interactions such as clicks, saves, and skips.

---

## Features

### Backend
- fetches recent articles using the NewsAPI `/everything` endpoint  
- cleans and stores structured data in `articles.json`  
- builds a TF-IDF index over article title + description  
- supports baseline relevance ranking using cosine similarity  

### Personalization
- user profile system with JSON-based storage  
- explicit preferences:
  - followed topics  
  - avoided topics  
- interaction tracking:
  - click  
  - save  
  - skip  
  - complete  
- learning algorithm that updates preferences over time  
- source preference scoring based on engagement  

### Ranking System
- recency scoring (prioritizes recent content)  
- diversity penalty (avoids repetitive articles)  
- topic preference weighting (strong boost for followed topics)  
- suppression of avoided topics  
- combined ranking formula:

Final Score =
0.50 * Topic Preference +
0.25 * Recency +
0.15 * Diversity +
0.10 * Source Trust

- threshold filtering:
  - strong results (≥ 0.5) preferred  
  - fallback to ≥ 0.3 if needed  
  - final fallback ensures feed is never empty  

- multi-topic balancing:
  - ensures at least one article per followed topic (when possible)

### Search
- TF-IDF based keyword search  
- combines:
  - 70% text relevance  
  - 30% personalization score  
- filters out avoided topics  

### Frontend (Flask UI)
- personalized "For You" feed  
- preferences page for topic selection  
- search page with ranked results  
- short summary for every article  
- direct link to full article  
- score breakdown visualization  
- interaction buttons (Save / Skip)  
- real-time feedback (learning updates)  
- interaction statistics panel  
- reset feature for new users  

## Project Structure

```bash
fetch_news.py              # fetches and stores article data
index.py                   # builds TF-IDF index (testing)
recommendation_engine.py   # ranking + personalization logic
user_model.py              # user preferences + learning
app_working.py             # Flask web app
test_system.py             # system tests
articles.json              # stored dataset
```

## How to Run
1. Fetch Articles
```python fetch_news.py```
3. Start the Web App
```python app_working.py```
4. Open in Browser
http://127.0.0.1:5001

### System Behavior
- recommendations adapt based on user interactions
- followed topics are prioritized
- avoided topics are strongly filtered out
- multiple selected topics are balanced in the feed
- weak recommendations are filtered unless fallback is needed
- search combines keyword matching with personalization

### Notes

- each article must include a valid url field for full article links
- user profiles are stored locally in JSON, so behavior evolves over time
- resetting the user clears learned preferences and interactions
