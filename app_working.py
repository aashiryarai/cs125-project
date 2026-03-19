"""
CS125 Final Project - Personal News Feed
Enhanced version with visible learning and context awareness
"""

import os
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify
from user_model import UserModel
from recommendation_engine import PersonalizedNewsRecommender

app = Flask(__name__)

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARTICLES_PATH = os.path.join(BASE_DIR, 'articles.json')

# Initialize
USER_ID = 'demo_user'
user = UserModel(USER_ID)
recommender = PersonalizedNewsRecommender(user, ARTICLES_PATH)

# Track shown articles for diversity
shown_articles = []

# ============================================================================
# INDEX TEMPLATE
# ============================================================================

INDEX_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Personal News Feed - CS125</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      background: #f8fafc;
      color: #0f172a;
      min-height: 100vh;
      padding: 2rem 1.5rem;
    }

    .container { max-width: 900px; margin: 0 auto; }

    header {
      background: #0f172a;
      border-radius: 16px;
      padding: 2rem;
      margin-bottom: 2rem;
      border: 1px solid #1e3a5f;
      box-shadow: 0 10px 30px rgba(15, 23, 42, 0.12);
    }

    h1 {
      font-size: 2rem;
      color: #ffffff;
      margin-bottom: 0.5rem;
    }

    .subtitle { color: #cbd5e1; }

    .nav-tabs {
      display: flex;
      gap: 1rem;
      margin: 2rem 0;
      flex-wrap: wrap;
    }

    .nav-tab {
      padding: 0.75rem 1.5rem;
      border-radius: 10px;
      background: #ffffff;
      border: 1px solid #cbd5e1;
      color: #0f172a;
      cursor: pointer;
      transition: all 0.2s;
      font-weight: 500;
      text-decoration: none;
      display: inline-block;
    }

    .nav-tab:hover {
      background: #eff6ff;
      border-color: #1d4ed8;
      color: #1e3a8a;
    }

    .nav-button {
      font-family: inherit;
      font-size: inherit;
    }

    .search-box {
      background: #ffffff;
      border-radius: 16px;
      padding: 1.5rem;
      margin-bottom: 2rem;
      border: 1px solid #dbeafe;
      box-shadow: 0 6px 20px rgba(15, 23, 42, 0.06);
    }

    .search-box form {
      display: flex;
      gap: 0.75rem;
    }

    .search-box input {
      flex: 1;
      padding: 0.875rem 1.25rem;
      border-radius: 10px;
      border: 1px solid #cbd5e1;
      background: #ffffff;
      color: #0f172a;
      font-size: 1rem;
    }

    .search-box input::placeholder { color: #64748b; }

    .search-box input:focus {
      outline: none;
      border-color: #1d4ed8;
      box-shadow: 0 0 0 3px rgba(29, 78, 216, 0.12);
    }

    .search-box button {
      padding: 0.875rem 2rem;
      border-radius: 10px;
      border: none;
      background: #1e3a8a;
      color: white;
      font-weight: 600;
      cursor: pointer;
    }

    .search-box button:hover {
      background: #1d4ed8;
    }

    .context-panel {
      background: #eff6ff;
      border: 1px solid #bfdbfe;
      border-radius: 16px;
      padding: 1.5rem;
      margin-bottom: 2rem;
    }

    .context-panel h3 {
      color: #1e3a8a;
      font-size: 1.1rem;
      margin-bottom: 1rem;
    }

    .context-item {
      display: flex;
      justify-content: space-between;
      padding: 0.5rem 0;
      border-bottom: 1px solid #dbeafe;
    }

    .context-item:last-child { border-bottom: none; }
    .context-label { color: #475569; }
    .context-value { color: #1e3a8a; font-weight: 600; }

    .prefs-panel {
      background: #ffffff;
      border-radius: 16px;
      padding: 1.5rem;
      margin-bottom: 2rem;
      border: 1px solid #dbeafe;
      box-shadow: 0 6px 20px rgba(15, 23, 42, 0.06);
    }

    .prefs-panel h3 {
      font-size: 1.1rem;
      margin-bottom: 1rem;
      color: #0f172a;
    }

    .pref-row {
      margin-bottom: 0.75rem;
      font-size: 0.95rem;
    }

    .pref-label {
      color: #475569;
      display: inline-block;
      width: 100px;
    }

    .pref-tags {
      display: inline-flex;
      flex-wrap: wrap;
      gap: 0.5rem;
    }

    .pref-tag {
      background: #eff6ff;
      color: #1e3a8a;
      padding: 0.25rem 0.75rem;
      border-radius: 6px;
      font-size: 0.85rem;
      border: 1px solid #dbeafe;
    }

    .pref-tag.followed {
      background: #dbeafe;
      color: #1e3a8a;
      border: 1px solid #93c5fd;
    }

    .pref-tag.avoided {
      background: #e2e8f0;
      color: #334155;
      border: 1px solid #cbd5e1;
    }

    .learning-panel {
      background: #eff6ff;
      border: 1px solid #bfdbfe;
      border-radius: 16px;
      padding: 1.5rem;
      margin-bottom: 2rem;
    }

    .learning-panel h3 {
      color: #1e3a8a;
      font-size: 1.1rem;
      margin-bottom: 1rem;
    }

    .stat-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
      gap: 1rem;
    }

    .stat-box {
      text-align: center;
      padding: 1rem;
      background: #ffffff;
      border-radius: 8px;
      border: 1px solid #dbeafe;
    }

    .stat-number {
      font-size: 2rem;
      font-weight: 700;
      color: #1e3a8a;
    }

    .stat-label {
      font-size: 0.85rem;
      color: #475569;
      margin-top: 0.25rem;
    }

    .article-card {
      background: #ffffff;
      border: 1px solid #dbeafe;
      border-radius: 16px;
      padding: 1.75rem;
      margin-bottom: 1.5rem;
      transition: all 0.3s;
      position: relative;
      box-shadow: 0 6px 20px rgba(15, 23, 42, 0.06);
    }

    .article-card:hover {
      transform: translateY(-4px);
      border-color: #93c5fd;
      box-shadow: 0 12px 28px rgba(15, 23, 42, 0.12);
    }

    .article-card.saved {
      border-left: 4px solid #1d4ed8;
      background: #f8fbff;
    }

    .article-card.skipped {
      opacity: 0.55;
      transform: scale(0.98);
    }

    .article-card h3 {
      font-size: 1.3rem;
      margin-bottom: 0.75rem;
      color: #0f172a;
      line-height: 1.4;
    }

    .article-title-link {
      color: #0f172a;
      text-decoration: none;
    }

    .article-title-link:hover {
      color: #1e3a8a;
      text-decoration: underline;
    }

    .article-summary {
      margin-bottom: 1rem;
    }

    .article-summary strong {
      display: block;
      margin-bottom: 0.35rem;
      color: #1e3a8a;
      font-size: 0.95rem;
    }

    .article-summary p {
      color: #475569;
      line-height: 1.6;
      margin-bottom: 0;
    }

    .article-link {
      display: inline-block;
      margin-top: 0.25rem;
      margin-bottom: 1rem;
      color: #1e3a8a;
      font-weight: 600;
      text-decoration: none;
    }

    .article-link:hover {
      text-decoration: underline;
    }

    .article-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 0.75rem;
      margin-bottom: 1rem;
      font-size: 0.875rem;
    }

    .meta-badge {
      background: #f1f5f9;
      padding: 0.35rem 0.75rem;
      border-radius: 6px;
      color: #334155;
      border: 1px solid #e2e8f0;
    }

    .meta-badge.keyword {
      background: #dbeafe;
      color: #1e3a8a;
      border: 1px solid #93c5fd;
    }

    .score-details {
      background: #f8fafc;
      padding: 0.75rem 1rem;
      border-radius: 8px;
      margin: 1rem 0;
      font-size: 0.85rem;
      border: 1px solid #e2e8f0;
    }

    .score-row {
      display: flex;
      justify-content: space-between;
      padding: 0.25rem 0;
    }

    .score-row span:first-child { color: #475569; }
    .score-row span:last-child {
      color: #1e3a8a;
      font-weight: 600;
    }

    .actions {
      display: flex;
      gap: 0.75rem;
      margin-top: 1rem;
    }

    .btn {
      padding: 0.625rem 1.25rem;
      border-radius: 8px;
      border: 1px solid #cbd5e1;
      background: #ffffff;
      color: #0f172a;
      cursor: pointer;
      transition: all 0.2s;
      font-weight: 500;
      font-size: 0.9rem;
    }

    .btn:hover {
      background: #eff6ff;
      border-color: #93c5fd;
      transform: translateY(-2px);
    }

    .btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .btn-save {
      background: #1e3a8a;
      border-color: #1e3a8a;
      color: #ffffff;
    }

    .btn-save:hover {
      background: #1d4ed8;
      border-color: #1d4ed8;
    }

    .btn-save.active {
      background: #1d4ed8;
    }

    .btn-skip {
      background: #e2e8f0;
      border-color: #cbd5e1;
      color: #334155;
    }

    .toast {
      position: fixed;
      bottom: 2rem;
      right: 2rem;
      background: #1e3a8a;
      color: white;
      padding: 1rem 1.5rem;
      border-radius: 10px;
      box-shadow: 0 8px 32px rgba(15, 23, 42, 0.18);
      animation: slideIn 0.3s ease-out;
      z-index: 1000;
    }

    @keyframes slideIn {
      from { transform: translateX(400px); opacity: 0; }
      to { transform: translateX(0); opacity: 1; }
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>Personal News Feed</h1>
      <p class="subtitle">Personalized, context-aware news recommendations</p>
    </header>

    <div class="nav-tabs">
      <a href="/" class="nav-tab">For You Page</a>
      <a href="/preferences" class="nav-tab">Preferences</a>
      <a href="javascript:location.reload()" class="nav-tab">Refresh Feed</a>
      <button type="button" class="nav-tab nav-button" onclick="resetUser()">New User Reset</button>
    </div>

    <div class="search-box">
      <form action="/search" method="get">
        <input type="text" name="q" placeholder="Search articles (e.g., artificial intelligence)..." required>
        <button type="submit">Search</button>
      </form>
    </div>

    <div class="context-panel">
      <h3>Current Context</h3>
      <div class="context-item">
        <span class="context-label">Time of Day:</span>
        <span class="context-value">{{ context.time_of_day }}</span>
      </div>
      <div class="context-item">
        <span class="context-label">Session Length:</span>
        <span class="context-value">{{ user_prefs.preferred_session_length|capitalize }} ({{ recommendations|length }} articles)</span>
      </div>
      <div class="context-item">
        <span class="context-label">Recency Priority:</span>
        <span class="context-value">Last 48 hours prioritized</span>
      </div>
      <div class="context-item">
        <span class="context-label">Diversity Mode:</span>
        <span class="context-value">Avoiding repetitive topics</span>
      </div>
    </div>

    <div class="learning-panel">
      <h3>System Learning (Adaptive Personalization)</h3>
      <div class="stat-grid">
        <div class="stat-box">
          <div class="stat-number">{{ stats.total_interactions }}</div>
          <div class="stat-label">Interactions</div>
        </div>
        <div class="stat-box">
          <div class="stat-number">{{ stats.saves }}</div>
          <div class="stat-label">Saved</div>
        </div>
        <div class="stat-box">
          <div class="stat-number">{{ stats.clicks }}</div>
          <div class="stat-label">Clicked</div>
        </div>
        <div class="stat-box">
          <div class="stat-number">{{ stats.skips }}</div>
          <div class="stat-label">Skipped</div>
        </div>
      </div>
      <p style="margin-top: 1rem; font-size: 0.9rem; color: #475569; text-align: center;">
        The system learns from your interactions to improve future recommendations.
      </p>
    </div>

    <div class="prefs-panel">
      <h3>Your Preferences</h3>
      <div class="pref-row">
        <span class="pref-label">Following:</span>
        <div class="pref-tags">
          {% if user_prefs.followed_keywords %}
            {% for keyword in user_prefs.followed_keywords %}
              <span class="pref-tag followed">{{ keyword }}</span>
            {% endfor %}
          {% else %}
            <span style="color: #64748b;">None</span>
          {% endif %}
        </div>
      </div>
      <div class="pref-row">
        <span class="pref-label">Avoiding:</span>
        <div class="pref-tags">
          {% if user_prefs.avoided_keywords %}
            {% for keyword in user_prefs.avoided_keywords %}
              <span class="pref-tag avoided">{{ keyword }}</span>
            {% endfor %}
          {% else %}
            <span style="color: #64748b;">None</span>
          {% endif %}
        </div>
      </div>
    </div>

    {% if recommendations %}
      {% for rec in recommendations %}
      <div class="article-card" data-id="{{ rec.article.id }}" data-keyword="{{ rec.article.keyword }}">
        <h3>
          <a
            href="{{ rec.article.url }}"
            target="_blank"
            rel="noopener noreferrer"
            class="article-title-link"
            onclick='recordInteraction({{ rec.article.id }}, "click", {{ rec.article.keyword|tojson }})'
          >
            {{ rec.article.title }}
          </a>
        </h3>

        <div class="article-summary">
          <strong>Summary:</strong>
          <p>{{ rec.article.description or 'No summary available for this article.' }}</p>
        </div>

        <a
          href="{{ rec.article.url }}"
          target="_blank"
          rel="noopener noreferrer"
          class="article-link"
          onclick='recordInteraction({{ rec.article.id }}, "click", {{ rec.article.keyword|tojson }})'
        >
          Read full article
        </a>

        <div class="article-meta">
          <span class="meta-badge keyword">{{ rec.article.keyword }}</span>
          <span class="meta-badge">{{ rec.article.source }}</span>
          <span class="meta-badge">Final Score: {{ "%.3f"|format(rec.final_score) }}</span>
        </div>

        <div class="score-details">
          <div class="score-row">
            <span>Topic Match (35%):</span>
            <span>{{ "%.3f"|format(rec.score_breakdown.keyword_score) }}</span>
          </div>
          <div class="score-row">
            <span>Recency (30%):</span>
            <span>{{ "%.3f"|format(rec.score_breakdown.recency_score) }}</span>
          </div>
          <div class="score-row">
            <span>Diversity (20%):</span>
            <span>{{ "%.3f"|format(rec.score_breakdown.diversity_score) }}</span>
          </div>
          <div class="score-row">
            <span>Source Trust (15%):</span>
            <span>{{ "%.3f"|format(rec.score_breakdown.source_score) }}</span>
          </div>
        </div>

        <div class="actions">
          <button class="btn btn-save" onclick='saveArticle({{ rec.article.id }}, {{ rec.article.keyword|tojson }})'>Save</button>
          <button class="btn btn-skip" onclick='skipArticle({{ rec.article.id }}, {{ rec.article.keyword|tojson }})'>Skip</button>
        </div>
      </div>
      {% endfor %}
    {% else %}
      <div style="text-align: center; padding: 3rem; color: #64748b;">
        <p>No recommendations available. Try adjusting your preferences.</p>
      </div>
    {% endif %}
  </div>

  <script>
    function showToast(message) {
      const toast = document.createElement('div');
      toast.className = 'toast';
      toast.textContent = message;
      document.body.appendChild(toast);
      setTimeout(() => toast.remove(), 3000);
    }

    function recordInteraction(articleId, type, keyword) {
      fetch('/api/interact', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ article_id: articleId, action: type, keyword: keyword })
      })
      .then((res) => res.json())
      .then((data) => {
        if (data.learned) {
          showToast(`Learning updated for "${keyword}".`);
        }
      })
      .catch((err) => console.error('Error:', err));
    }

    function saveArticle(id, keyword) {
      recordInteraction(id, 'save', keyword);
      const card = document.querySelector(`[data-id="${id}"]`);
      if (card) {
        card.classList.add('saved');
        const btn = card.querySelector('.btn-save');
        if (btn) {
          btn.textContent = 'Saved';
          btn.classList.add('active');
          btn.disabled = true;
        }
        showToast(`Saved. You will see more ${keyword} content.`);
      }
    }

    function skipArticle(id, keyword) {
      recordInteraction(id, 'skip', keyword);
      const card = document.querySelector(`[data-id="${id}"]`);
      if (card) {
        card.classList.add('skipped');
        const btns = card.querySelectorAll('.btn');
        btns.forEach((btn) => btn.disabled = true);
        showToast(`Skipped. You will see less ${keyword} content.`);
      }
    }

    function resetUser() {
      const userId = prompt('Enter a user ID for a fresh profile:', 'new_user');
      if (!userId) return;

      fetch('/api/reset-user', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ user_id: userId })
      })
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          showToast(`Profile reset for ${data.user_id}.`);
          setTimeout(() => {
            window.location.href = '/preferences';
          }, 500);
        } else {
          throw new Error(data.error || 'Reset failed');
        }
      })
      .catch((err) => {
        alert('Error: ' + err.message);
      });
    }
  </script>
</body>
</html>'''

# ============================================================================
# PREFERENCES TEMPLATE
# ============================================================================

PREFERENCES_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Preferences</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: 'Inter', sans-serif;
      background: #f8fafc;
      color: #0f172a;
      min-height: 100vh;
      padding: 2rem 1.5rem;
    }

    .container { max-width: 800px; margin: 0 auto; }

    .back-link {
      display: inline-block;
      color: #1e3a8a;
      text-decoration: none;
      margin-bottom: 2rem;
      font-weight: 500;
    }

    .card {
      background: #ffffff;
      border: 1px solid #dbeafe;
      border-radius: 16px;
      padding: 2.5rem;
      box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
    }

    h1 {
      font-size: 2rem;
      color: #0f172a;
      margin-bottom: 0.5rem;
    }

    .subtitle {
      color: #475569;
      margin-bottom: 2rem;
    }

    h2 {
      font-size: 1.3rem;
      color: #0f172a;
      margin: 2rem 0 1rem;
    }

    .checkbox-group {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
      gap: 1rem;
      margin-bottom: 2rem;
    }

    .checkbox-item {
      background: #ffffff;
      border: 2px solid #dbeafe;
      padding: 1rem;
      border-radius: 10px;
      cursor: pointer;
      transition: all 0.2s;
      display: flex;
      align-items: center;
      color: #0f172a;
    }

    .checkbox-item:hover {
      background: #eff6ff;
    }

    .checkbox-item input {
      margin-right: 0.75rem;
      width: 18px;
      height: 18px;
      cursor: pointer;
    }

    .checkbox-item.followed {
      border-color: #93c5fd;
      background: #dbeafe;
    }

    .checkbox-item.avoided {
      border-color: #cbd5e1;
      background: #f1f5f9;
    }

    select {
      width: 100%;
      padding: 1rem 1.25rem;
      border-radius: 10px;
      border: 1px solid #cbd5e1;
      background: #ffffff;
      color: #0f172a;
      font-size: 1rem;
      margin-bottom: 2rem;
    }

    option {
      background: #ffffff;
      color: #0f172a;
    }

    .btn {
      padding: 1rem 2rem;
      border-radius: 10px;
      border: none;
      font-weight: 600;
      font-size: 1rem;
      cursor: pointer;
      transition: all 0.2s;
    }

    .btn-primary {
      background: #1e3a8a;
      color: white;
    }

    .btn-primary:hover {
      background: #1d4ed8;
      transform: translateY(-2px);
    }

    .btn-secondary {
      background: #ffffff;
      border: 1px solid #cbd5e1;
      color: #0f172a;
      margin-left: 1rem;
      text-decoration: none;
      display: inline-block;
      text-align: center;
    }
  </style>
</head>
<body>
  <div class="container">
    <a href="/" class="back-link">← Back to Feed</a>

    <div class="card">
      <h1>Preferences</h1>
      <p class="subtitle">Customize your news feed</p>

      <form id="prefsForm">
        <h2>Topics to Follow</h2>
        <div class="checkbox-group">
          {% for topic in ['technology', 'science', 'business', 'health', 'sports', 'entertainment'] %}
          <label class="checkbox-item {% if topic in user_prefs.followed_keywords %}followed{% endif %}">
            <input type="checkbox" name="followed_keywords" value="{{ topic }}"
              {% if topic in user_prefs.followed_keywords %}checked{% endif %}>
            <span>{{ topic|capitalize }}</span>
          </label>
          {% endfor %}
        </div>

        <h2>Topics to Avoid</h2>
        <div class="checkbox-group">
          {% for topic in ['sports', 'entertainment', 'technology', 'business', 'health', 'science'] %}
          <label class="checkbox-item {% if topic in user_prefs.avoided_keywords %}avoided{% endif %}">
            <input type="checkbox" name="avoided_keywords" value="{{ topic }}"
              {% if topic in user_prefs.avoided_keywords %}checked{% endif %}>
            <span>{{ topic|capitalize }}</span>
          </label>
          {% endfor %}
        </div>

        <h2>Session Length (Context)</h2>
        <select name="session_length">
          <option value="short" {% if user_prefs.preferred_session_length == 'short' %}selected{% endif %}>
            Short (3 articles, ~5 minutes)
          </option>
          <option value="medium" {% if user_prefs.preferred_session_length == 'medium' %}selected{% endif %}>
            Medium (5 articles, ~10 minutes)
          </option>
          <option value="long" {% if user_prefs.preferred_session_length == 'long' %}selected{% endif %}>
            Long (8 articles, ~15 minutes)
          </option>
        </select>

        <button type="submit" class="btn btn-primary">Save & Update Feed</button>
        <a href="/" class="btn btn-secondary">Cancel</a>
      </form>
    </div>
  </div>

  <script>
    document.querySelectorAll('.checkbox-item input').forEach((cb) => {
      cb.addEventListener('change', function() {
        const label = this.closest('.checkbox-item');
        const isFollowed = this.name === 'followed_keywords';
        if (this.checked) {
          label.classList.add(isFollowed ? 'followed' : 'avoided');
        } else {
          label.classList.remove('followed', 'avoided');
        }
      });
    });

    document.getElementById('prefsForm').addEventListener('submit', function(e) {
      e.preventDefault();

      const formData = new FormData(this);
      const prefs = {
        followed_keywords: formData.getAll('followed_keywords'),
        avoided_keywords: formData.getAll('avoided_keywords'),
        session_length: formData.get('session_length')
      };

      const btn = this.querySelector('.btn-primary');
      btn.textContent = 'Saving and rebuilding...';
      btn.disabled = true;

      fetch('/api/preferences', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(prefs)
      })
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          btn.textContent = 'Saved. Redirecting...';
          setTimeout(() => {
            window.location.href = '/';
          }, 500);
        } else {
          throw new Error(data.error || 'Save failed');
        }
      })
      .catch((err) => {
        alert('Error: ' + err.message);
        btn.textContent = 'Save & Update Feed';
        btn.disabled = false;
      });
    });
  </script>
</body>
</html>'''

# ============================================================================
# SEARCH TEMPLATE
# ============================================================================

SEARCH_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Search</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: 'Inter', sans-serif;
      background: #f8fafc;
      color: #0f172a;
      min-height: 100vh;
      padding: 2rem 1.5rem;
    }

    .container { max-width: 900px; margin: 0 auto; }

    .back-link {
      display: inline-block;
      color: #1e3a8a;
      text-decoration: none;
      margin-bottom: 2rem;
      font-weight: 500;
    }

    header {
      background: #0f172a;
      border-radius: 16px;
      padding: 2rem;
      margin-bottom: 2rem;
      border: 1px solid #1e3a5f;
      box-shadow: 0 10px 30px rgba(15, 23, 42, 0.12);
    }

    h1 {
      font-size: 2rem;
      color: #ffffff;
      margin-bottom: 1rem;
    }

    .search-info { color: #cbd5e1; }
    .search-info strong { color: #ffffff; }

    .search-box {
      background: #ffffff;
      border-radius: 16px;
      padding: 1.5rem;
      margin-bottom: 2rem;
      border: 1px solid #dbeafe;
      box-shadow: 0 6px 20px rgba(15, 23, 42, 0.06);
    }

    .search-box form {
      display: flex;
      gap: 0.75rem;
    }

    .search-box input {
      flex: 1;
      padding: 0.875rem 1.25rem;
      border-radius: 10px;
      border: 1px solid #cbd5e1;
      background: #ffffff;
      color: #0f172a;
      font-size: 1rem;
    }

    .search-box button {
      padding: 0.875rem 2rem;
      border-radius: 10px;
      border: none;
      background: #1e3a8a;
      color: white;
      font-weight: 600;
      cursor: pointer;
    }

    .search-box button:hover {
      background: #1d4ed8;
    }

    .article-card {
      background: #ffffff;
      border: 1px solid #dbeafe;
      border-radius: 16px;
      padding: 1.75rem;
      margin-bottom: 1.5rem;
      box-shadow: 0 6px 20px rgba(15, 23, 42, 0.06);
    }

    .article-card h3 {
      font-size: 1.3rem;
      margin-bottom: 0.75rem;
      color: #0f172a;
    }

    .article-title-link {
      color: #0f172a;
      text-decoration: none;
    }

    .article-title-link:hover {
      color: #1e3a8a;
      text-decoration: underline;
    }

    .article-summary {
      margin-bottom: 1rem;
    }

    .article-summary strong {
      display: block;
      margin-bottom: 0.35rem;
      color: #1e3a8a;
      font-size: 0.95rem;
    }

    .article-summary p {
      color: #475569;
      line-height: 1.6;
      margin-bottom: 0;
    }

    .article-link {
      display: inline-block;
      margin-top: 0.25rem;
      margin-bottom: 1rem;
      color: #1e3a8a;
      font-weight: 600;
      text-decoration: none;
    }

    .article-link:hover {
      text-decoration: underline;
    }

    .article-meta {
      display: flex;
      gap: 0.75rem;
      margin-bottom: 1rem;
      font-size: 0.875rem;
      flex-wrap: wrap;
    }

    .meta-badge {
      background: #f1f5f9;
      padding: 0.35rem 0.75rem;
      border-radius: 6px;
      color: #334155;
      border: 1px solid #e2e8f0;
    }

    .meta-badge.keyword {
      background: #dbeafe;
      color: #1e3a8a;
      border: 1px solid #93c5fd;
    }

    .score-breakdown {
      background: #eff6ff;
      border: 1px solid #bfdbfe;
      padding: 1rem;
      border-radius: 8px;
      font-size: 0.9rem;
      margin-top: 1rem;
      color: #1e3a8a;
    }

    .score-breakdown strong { color: #1e3a8a; }

    .empty {
      text-align: center;
      padding: 3rem;
      color: #64748b;
    }
  </style>
</head>
<body>
  <div class="container">
    <a href="/" class="back-link">← Back to Feed</a>

    <header>
      <h1>Search Results</h1>
      {% if query %}
        <p class="search-info">Found <strong>{{ results|length }} results</strong> for "<strong>{{ query }}</strong>"</p>
      {% endif %}
    </header>

    <div class="search-box">
      <form action="/search" method="get">
        <input type="text" name="q" value="{{ query }}" placeholder="Search articles..." required>
        <button type="submit">Search</button>
      </form>
    </div>

    {% if query %}
      {% if results %}
        {% for result in results %}
        <div class="article-card">
          <h3>
            <a
              href="{{ result.article.url }}"
              target="_blank"
              rel="noopener noreferrer"
              class="article-title-link"
            >
              {{ result.article.title }}
            </a>
          </h3>

          <div class="article-summary">
            <strong>Summary:</strong>
            <p>{{ result.article.description or 'No summary available for this article.' }}</p>
          </div>

          <a
            href="{{ result.article.url }}"
            target="_blank"
            rel="noopener noreferrer"
            class="article-link"
          >
            Read full article
          </a>

          <div class="article-meta">
            <span class="meta-badge keyword">{{ result.article.keyword }}</span>
            <span class="meta-badge">{{ result.article.source }}</span>
          </div>

          <div class="score-breakdown">
            <strong>Ranking Breakdown:</strong><br>
            TF-IDF Relevance: {{ "%.3f"|format(result.tfidf_score) }} (text match)<br>
            Personalization: {{ "%.3f"|format(result.personalization_score) }} (your interests)<br>
            Combined Score: {{ "%.3f"|format(result.combined_score) }} <strong>(70% text + 30% personal)</strong>
          </div>
        </div>
        {% endfor %}
      {% else %}
        <div class="empty">
          <h2 style="color: #64748b;">No results found</h2>
          <p>Try different keywords</p>
        </div>
      {% endif %}
    {% else %}
      <div class="empty">
        <h2 style="color: #64748b;">Enter a search term</h2>
      </div>
    {% endif %}
  </div>
</body>
</html>'''

# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def index():
    global shown_articles
    try:
        recommendations = recommender.generate_recommendations(recent_articles=shown_articles)

        shown_articles = [rec['article'] for rec in recommendations]
        if len(shown_articles) > 20:
            shown_articles = shown_articles[-20:]

        current_hour = datetime.now().hour
        if 5 <= current_hour < 12:
            time_of_day = "Morning (shorter summaries)"
        elif 12 <= current_hour < 17:
            time_of_day = "Afternoon"
        elif 17 <= current_hour < 21:
            time_of_day = "Evening (in-depth content)"
        else:
            time_of_day = "Night"

        context = {
            'time_of_day': time_of_day,
            'current_hour': current_hour
        }

        user_prefs = user.profile['preferences']
        stats = user.get_interaction_stats()

        return render_template_string(
            INDEX_TEMPLATE,
            recommendations=recommendations,
            user_prefs=user_prefs,
            stats=stats,
            context=context
        )
    except Exception as e:
        return f"Error: {str(e)}<br><a href='/'>Retry</a>", 500


@app.route('/preferences')
def preferences_page():
    try:
        user_prefs = user.profile['preferences']
        return render_template_string(
            PREFERENCES_TEMPLATE,
            user_prefs=user_prefs
        )
    except Exception as e:
        return f"Error: {str(e)}<br><a href='/'>Back</a>", 500


@app.route('/search')
def search_page():
    try:
        query = request.args.get('q', '').strip()
        results = []
        if query:
            results = recommender.search_with_personalization(query, top_k=10)

        return render_template_string(
            SEARCH_TEMPLATE,
            query=query,
            results=results
        )
    except Exception as e:
        return f"Search error: {str(e)}<br><a href='/'>Back</a>", 500


@app.route('/api/preferences', methods=['GET', 'POST'])
def api_preferences():
    global user, recommender, shown_articles

    if request.method == 'GET':
        return jsonify(user.profile['preferences'])

    try:
        data = request.get_json() or {}
        user.update_preferences(
            followed_keywords=data.get('followed_keywords'),
            avoided_keywords=data.get('avoided_keywords'),
            session_length=data.get('session_length')
        )

        recommender = PersonalizedNewsRecommender(user, ARTICLES_PATH)
        shown_articles = []

        return jsonify({
            'success': True,
            'preferences': user.profile['preferences']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/interact', methods=['POST'])
def record_interaction():
    global recommender
    try:
        data = request.get_json() or {}
        article_id = data.get('article_id')
        action = data.get('action', 'click')

        if article_id is not None and action:
            user.record_interaction(article_id, action)

            interactions_count = len(user.profile['interaction_history'])
            learned = False

            if interactions_count % 3 == 0:
                user.learn_from_interactions(recommender.articles)
                learned = True

            return jsonify({
                'success': True,
                'learned': learned,
                'total_interactions': interactions_count
            })

        return jsonify({'error': 'Missing data'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/reset-user', methods=['POST'])
def reset_user():
    global user, recommender, shown_articles

    try:
        data = request.get_json() or {}
        new_user_id = (data.get('user_id') or 'demo_user').strip()

        user = UserModel(new_user_id)
        recommender = PersonalizedNewsRecommender(user, ARTICLES_PATH)
        shown_articles = []

        return jsonify({
            'success': True,
            'user_id': new_user_id,
            'preferences': user.profile['preferences']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("\\n" + "=" * 70)
    print("CS125 PERSONAL NEWS FEED - ENHANCED DEMO")
    print("=" * 70)

    if not os.path.exists(ARTICLES_PATH):
        print(f"\\nERROR: Articles not found at {ARTICLES_PATH}")
        raise SystemExit(1)

    print("\\nSystem Status:")
    print(f"   Articles: {len(recommender.articles)}")
    print(f"   User: {user.user_id}")
    print(f"   Preferences: {user.profile['preferences']['followed_keywords']}")
    print("\\nFeatures:")
    print("   Visible context awareness (time, recency, diversity)")
    print("   Interactive learning (save/skip updates preferences)")
    print("   Real-time feedback (toasts show learning)")
    print("   Score breakdowns for every article")
    print("\\nServer: http://localhost:5001")
    print("Press CTRL+C to stop\\n")
    print("=" * 70 + "\\n")

    app.run(debug=True, port=5001, host='127.0.0.1')