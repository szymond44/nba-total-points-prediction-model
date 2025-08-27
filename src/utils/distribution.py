from scipy import stats
import numpy as np
def distribution_calculating(df, team):
    if not all(col in df.columns for col in ['home_team_id', 'away_team_id', 'home_pts', 'away_pts']):
        raise ValueError("DataFrame must contain 'home_team_id' and 'away_team_id' columns.")
    
    data = df[(df['home_team_id'] == team) | (df['away_team_id'] == team)]

    classical_distribution = {}
    home_distribution = {}
    away_distribution = {}

    for row in data.itertuples():
        home_or_away = 'home' if row.home_team_id == team else 'away'
        points = getattr(row, f'{home_or_away}_pts')

        classical_distribution[points] = classical_distribution.get(points, 0) + 1
        if home_or_away == 'home':
            home_distribution[points] = home_distribution.get(points, 0) + 1
        else:
            away_distribution[points] = away_distribution.get(points, 0) + 1
    
    return classical_distribution, home_distribution, away_distribution

def _is_normal_distribution(distribution_dict):
    """Checks if distribution is normal using statistical tests."""
    if not distribution_dict:
        return False
    
    # Convert to data sample
    data_sample = np.array([
        point for point, count in distribution_dict.items() 
        for _ in range(count)
    ])
    
    if len(data_sample) < 8:  # Minimum for tests
        return False
    
    # Normality tests
    tests = [
        stats.normaltest(data_sample)[1] > 0.05,  # D'Agostino-Pearson
        stats.kstest(data_sample, 'norm', 
                    args=(np.mean(data_sample), np.std(data_sample)))[1] > 0.05
    ]
    
    # Shapiro only for smaller samples
    if len(data_sample) < 5000:
        tests.append(stats.shapiro(data_sample)[1] > 0.05)
    
    return any(tests)

def check_distribution(df):
    """Checks normality of distributions for all teams."""
    team_ids = df['home_team_id'].unique()
    
    results = [
        _is_normal_distribution(dist)
        for team in team_ids
        for dist in distribution_calculating(df, team)
    ]
    
    true_count = sum(results)
    false_count = len(results) - true_count
    return true_count, false_count