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