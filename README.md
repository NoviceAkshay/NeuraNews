# 📰 News Pulse: Global News Trend Analyzer using AI

## Overview 🌍
**News Pulse** is a full-stack news application that leverages **AI** to deliver real-time global news trends!  
The backend is built with **FastAPI**, and the frontend uses **Streamlit** for an interactive and clean user experience.  

Features include:  
- ✅ Real-time news fetching via **NewsAPI**  
- 🔐 Simple in-app login system using session state  
- 🔍 Search and filter articles by keyword  
- 📰 User-friendly display of articles (title, description, source, date, links)  
- ⚡ Modular structure for easy extension (e.g., user registration, database integration, data export)

---

## 🛠 Tech Stack
- **Backend:** FastAPI (Python)  
- **Frontend:** Streamlit (Python)  
- **Data Source:** [NewsAPI.org](https://newsapi.org/)  
- **Database:** PostgreSQL (pgAdmin4)  
- **IDE:** PyCharm  
- **Environment:** Virtual env with `uv`  

---

## 📰 News Data Collection Module
**Purpose:** Collect news from global sources (APIs, RSS feeds, or scraping)  
**Output:** Structured news data including title, source, and summary for AI analysis  

---

## 🏗 Architecture Overview

### 1. User Interaction
- Users open the **Streamlit** app  
- Can **register** or **login**  

### 2. API Communication
- Streamlit sends requests to **FastAPI endpoints** (`register`, `login`)  
- FastAPI validates input, interacts with **PostgreSQL**, and returns JSON  

### 3. Database Operations
- Users table stores username, password, email  
- News can be stored in a separate table for analysis  

### 4. Session Management
- **Streamlit session state** temporarily stores login info  

### 5. News Fetching
- After login, users can search news  
- FastAPI fetches news using **NewsAPI**, with preprocessing using **SpaCy + NLTK**

---

## ⚡ Backend (FastAPI)
- **main.py** → FastAPI entry point, defines routes (`news`, `login`, `register`)  
- **database.py** → PostgreSQL connection via SQLAlchemy  
- **models.py** → SQLAlchemy models for users and news  
- **auth.py** → Password hashing and authentication  
- **text_cleaning.py** → NLP preprocessing (SpaCy + NLTK)  

---

## 🌐 Frontend (Streamlit)
**app.py**: Main Streamlit app  
- **Register** → Collect username, email, password  
- **Login** → Authenticate users  
- After login:  
  - Personalized dashboard  
  - News search feature  
- Users can:  
  - Log in with simple authentication  
  - Enter search term and number of articles  
  - Fetch and display articles with images, descriptions, and source links  

---

## 💾 Database Design

### Tables
**1. users**
| Column | Type | Description |
|--------|------|-------------|
| id | PK | Unique ID |
| username | Unique | Username |
| email | Unique | User email |
| created_at | Timestamp | Account creation |

**2. news**
| Column | Type | Description |
|--------|------|-------------|
| id | PK | Unique ID |
| title | Text | News title |
| description | Text | Article summary |
| url | Text | Article link |
| published_at | Timestamp | Publication date |
| source | Text | Source name |
| query_term | Text | Search keyword |

---

## 🔄 End-to-End Flow
1. User opens Streamlit app:  
   ```bash
   streamlit run frontend/app.py
User logs in with username/password

User enters search term

Streamlit sends GET request to FastAPI:


http://127.0.0.1:8000/news
FastAPI fetches results from NewsAPI.org and returns JSON

Streamlit displays formatted articles

📚 References (YouTube)
Complete Streamlit Course for Python Developers

Streamlit Mini Course - Make Websites With ONLY Python

Python FastAPI Tutorial
