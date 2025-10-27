from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.engine import Base
from .team import Team


class Game(Base):
    """
    ORM model representing a single game entry in the "games" table.
    Attributes:
        id (int): Primary key, auto-incremented unique identifier for the DB row.
        game_id (int): External or league-provided identifier for the game (not the DB PK).
        season (str): Season identifier (e.g., "2024-25"); stored as a short string.
        game_date (datetime): Timestamp for when the game took place.
        team_id (int): Foreign key referencing teams.id; identifies the team this record is for.
        result (str): Single-character result code (commonly 'W' for win, 'L' for loss, etc.).
        points (int): Points scored by the team in this game.
        plus_minus (float | None): Plus/minus metric for the team/player in the game; may be null.
        team (Team): SQLAlchemy relationship to the Team model for eager/lazy access to team details.
    Behavior/Notes:
        - This class is intended for use with SQLAlchemy ORM sessions.
        - Column types and constraints (nullable, foreign key, indexing) are defined on the mapped columns.
        - __repr__ provides a compact, human-readable identification: "<Game(game_id=..., season=..., team_id=...)>".
    """

    __tablename__ = "games"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, index=True
    )

    game_id: Mapped[int] = mapped_column(Integer, nullable=False)
    season: Mapped[str] = mapped_column(String(7), nullable=False)

    game_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    team_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("teams.id"), nullable=False
    )

    result: Mapped[str] = mapped_column(String(1), nullable=False)
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    plus_minus: Mapped[Float] = mapped_column(Float, nullable=True)

    team: Mapped["Team"] = relationship("Team", foreign_keys=[team_id])

    def __repr__(self):
        return f"<Game(game_id={self.game_id}, season={self.season}, team_id={self.team_id})>"
