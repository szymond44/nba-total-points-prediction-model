from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.engine import Base
from .game import Game
from .player import Player
from .team import Team


class PlayerGameLog(Base):
    __tablename__ = "player_game_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    player_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("players.id"), nullable=False
    )
    game_id: Mapped[str] = mapped_column(String, nullable=False)
    team_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("teams.id"), nullable=False
    )

    game_pk_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("games.id"), nullable=False
    )

    minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    fgm: Mapped[int] = mapped_column(Integer, nullable=False)
    fga: Mapped[int] = mapped_column(Integer, nullable=False)
    fg_pct: Mapped[Float] = mapped_column(Float, nullable=True)

    fg3m: Mapped[int] = mapped_column(Integer, nullable=False)
    fg3a: Mapped[int] = mapped_column(Integer, nullable=False)
    fg3_pct: Mapped[Float] = mapped_column(Float, nullable=True)

    ftm: Mapped[int] = mapped_column(Integer, nullable=False)
    fta: Mapped[int] = mapped_column(Integer, nullable=False)
    ft_pct: Mapped[Float] = mapped_column(Float, nullable=True)

    oreb: Mapped[int] = mapped_column(Integer, nullable=False)
    dreb: Mapped[int] = mapped_column(Integer, nullable=False)
    reb: Mapped[int] = mapped_column(Integer, nullable=False)

    ast: Mapped[int] = mapped_column(Integer, nullable=False)
    tov: Mapped[int] = mapped_column(Integer, nullable=False)
    stl: Mapped[int] = mapped_column(Integer, nullable=False)
    blk: Mapped[int] = mapped_column(Integer, nullable=False)
    pf: Mapped[int] = mapped_column(Integer, nullable=False)
    pts: Mapped[int] = mapped_column(Integer, nullable=False)

    player: Mapped["Player"] = relationship("Player", foreign_keys=[player_id])
    team: Mapped["Team"] = relationship("Team", foreign_keys=[team_id])
    game: Mapped["Game"] = relationship("Game", foreign_keys=[game_pk_id])

    def __repr__(self):
        return f"<PlayerGameLog(player_id={self.player_id}, game_id={self.game_id}, pts={self.pts})>"
