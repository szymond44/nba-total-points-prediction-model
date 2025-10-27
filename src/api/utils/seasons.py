import os
from datetime import datetime

from dotenv import load_dotenv


def get_current_season() -> str:
    """Return the current NBA season string in the format "YYYY-YY".
    The NBA season is considered to start in October. This function uses the
    current local date/time (datetime.now()) to determine the appropriate season:
    - If the current month is October (10) or later, the season is the current
        calendar year followed by the next year (e.g. in October 2024 -> "2024-25").
    - If the current month is before October, the season is the previous calendar
        year followed by the current year (e.g. in June 2025 -> "2024-25").
    Returns:
            str: Season string formatted as "YYYY-YY" (four-digit start year, two-digit
                     end year).
    Notes:
            - The function uses the local system clock (naive datetime.now()). If your
                application requires timezone-aware behavior, supply a timezone-aware
                datetime or adjust the system time accordingly.
            - For years crossing the century (e.g. 1999->2000), the end-year portion
                is the last two digits of the end year (e.g. "1999-00").
    Examples:
            >>> get_current_season()  # assuming current date is 2024-11-01
            '2024-25'
            >>> get_current_season()  # assuming current date is 2025-06-15
            '2024-25'
    """
    now = datetime.now()
    year = now.year

    if now.month >= 10:  # NBA season starts in October
        return f"{year}-{str(year + 1)[2:]}"
    else:
        return f"{year - 1}-{str(year)[2:]}"


def get_season_range() -> list[str]:
    """
    Return a list of season identifiers from the configured start year up to the current season.
    This function:
    - Calls load_dotenv() to (re)load environment variables.
    - Reads the start year from the SEASON_START environment variable (defaults to 1996).
    - Calls get_current_season() and uses the first component before "-" as the current start year.
    - Builds a list of season strings in the form "YYYY-YY" (e.g. "1996-97", "2023-24"), inclusive
        from the configured start year through the current season year.
    Returns:
            list[str]: Ordered list of season strings starting at SEASON_START and ending with the
                                 current season. Each season is formatted "YYYY-YY", where the second part
                                 is the last two digits of the next calendar year.
    Raises:
            ValueError: If SEASON_START cannot be converted to int, or if get_current_season()
                                    returns an unexpected format that prevents parsing the starting year.
    Notes:
            - The function expects get_current_season() to return a string containing a hyphen
                and a four-digit starting year as the portion before the hyphen (e.g. "2023-24").
            - Environment variables must be loadable via load_dotenv() prior to reading SEASON_START.
    """
    load_dotenv()

    start = int(os.getenv("SEASON_START", "1996"))
    current = int(get_current_season().split("-")[0])

    seasons = []

    for year in range(start, current + 1):
        next_year = str(year + 1)[2:]
        season = f"{year}-{next_year}"
        seasons.append(season)

    return seasons


def get_season_range_reverse() -> list[str]:
    """
    Return a list of season identifiers from the current season down to the configured start year.
    This function:
    - Calls get_season_range() to get the ordered list of seasons.
    - Reverses the list so that the most recent season is first.
    Returns:
            list[str]: Ordered list of season strings starting with the current season and ending with
                                 SEASON_START. Each season is formatted "YYYY-YY", where the second part
                                 is the last two digits of the next calendar year.
    """
    seasons = get_season_range()
    seasons.reverse()
    return seasons
