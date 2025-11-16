<h1 align="center">
🏀 NBA Team Points Prediction Model
</h1>

<div align="center">
🙋 <b>authors:</b> <a href="https://github.com/szymond44/">szymond44</a>, <a href="https://github.com/gwiazdan">gwiazdan</a><br/>
📆 <b>date:</b> 21-07-2025
</div>

# Project Architecture

## Overview
This project fetches NBA player statistics season-by-season using the `nba_api` Python library, processes the data through a Machine Learning (ML) layer for insights and predictions, and provides an interactiv
e web interface built with Streamlit to explore, visualize, and interact with the enriched data.

## Components

### 1. Data Fetching Service
- **Library:** `nba_api`
- **Purpose:** Retrieve historical and current season statistics for NBA players, games, and teams.
- **Functionality:**  
  - Fetch player career statistics using endpoints like `PlayerGameLog`.  
  - Schedule periodic updates to keep the data current.  
  - Supports caching of fetched data to reduce API calls and improve responsiveness.

### 2. Data Storage
- **Database:** MongoDB
- **Purpose:** Store fetched API data in a structured format (JSON or compressed JSON lines) for efficient querying and fast loading by downstream components.
- **Notes:**  
  - No relational models are required; data is stored as documents.  
  - Supports incremental updates.

### 3. Machine Learning Layer
- **Purpose:**  
  - Clean, transform, and enrich raw data fetched from NBA API.  
  - Train and serve predictive models (e.g., player performance forecasting, clustering, classification).  
  - Provide APIs or data stores with derived features and ML predictions consumed by the UI or other services.
- **Tools & Frameworks:** Python ecosphere (e.g., scikit-learn, TensorFlow, PyTorch) suitable for experimentation and deployment.

### 4. Web Interface
- **Framework:** Streamlit
- **Purpose:** Provide an interactive dashboard for users to search, filter, and visualize NBA player statistics, including raw stats and ML-generated insights.
- **Features:**  
  - Dynamic filtering by player, season, and statistics type.  
  - Visualization of both historical stats and predicted metrics from ML models.  
  - Real-time data fetching or cached data display.  
  - Responsive and user-friendly UI with minimal setup.

## Workflow

1. **Data Fetching Service** pulls raw NBA data using `nba_api`.
2. Data is stored in NoSQL or local storage as JSON.
3. **Machine Learning Layer** processes stored data for cleaning, feature engineering, and model training. Predictive results are saved back to storage or exposed via API.
4. The **Streamlit App** reads both raw and ML-enriched data to provide comprehensive visualizations and user interaction.