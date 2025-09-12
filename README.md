<h1 align="center">
<a href="https://github.com/szymond44/model/" style="text-decoration: none; color:white; font-weight: 900">🏀 NBA Team Points Prediction Model</a>
</h1>

<div align="center">
🙋 <span style="font-weight:1000;">authors:</span> <a href="https://github.com/szymond44/" style="text-decoration: none; color:white; font-weight: 500; letter-spacing:0.5px">szymond44</a>, <a href="https://github.com/gwiazdan" style="text-decoration: none; color:white; font-weight: 500; letter-spacing:0.5px">gwiazdan</a>  <br/>
📆 <span style="font-weight:1000;">date:</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <span style="letter-spacing:2px; font-weight:500">21-07-2025</span>
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
- [Team data](notebooks/nba-team-data-exploration.ipynb)

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
    │   └── utils/             # helper functions
    ├── cache/                 # cached API responses
    ├── README.md
    └── requirements.txt
```

## 🏗️ Architecture

The project uses a **middle-tier API server** that:
- Handles complex NBA API endpoints with caching
- Provides clean interface for notebooks
- Manages rate limiting and error handling
- Stores processed data persistently