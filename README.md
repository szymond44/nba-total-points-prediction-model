<h1 align="center">
🏀 NBA Team Points Prediction Model
</h1>

<div align="center">
🙋 <b>authors:</b> <a href="https://github.com/szymond44/">szymond44</a>, <a href="https://github.com/gwiazdan">gwiazdan</a><br/>
📆 <b>date:</b> 21-07-2025
</div>

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the API Server
```bash
python -m src.api.server
```
The server will start on `http://127.0.0.1:8000`

### 3. Use the API
```python
from src.data import ApiFetcher

api = ApiFetcher(starting_year=2019, ending_year=2025)
df = api.get_dataframe('boxscoreadvanced')
```

---

## 📚 Notebooks

🔬 **Data exploring**
- [Basic featueres + Points distributions](notebooks/nba-team-data-exploration-1.ipynb)
- [Advanced features](notebooks/nba-team-data-exploration-2.ipynb)

🎯 **Model testing**
- [Primary team embedding model](notebooks/nba-embedding-model-testing.ipynb)

---

## 📂 File Structure

```
.
└── model/
    ├── notebooks/
    │   ├── nba-embedding-model-testing.ipynb
    │   └── nba-team-data-exploring.ipynb
    ├── src/
    │   ├── api/               # FastAPI server & NBA endpoints
    │   ├── data/              # data fetching and processing  
    │   ├── model/             # regression models
    │   │   └── team_embeddings
    │   ├── cache/             # caching layer 
    │   └── utils/             # helper functions
    ├── README.md
    └── requirements.txt
```

## 🏗️ Architecture

The project uses a **middle-tier API server** that:
- Handles complex NBA API endpoints with caching
- Provides clean interface for notebooks
- Manages rate limiting and error handling
- Stores processed data persistently