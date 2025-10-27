from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..db.engine import Base


class Player(Base):
    """
    SQLAlchemy ORM model representing a player stored in the "players" table.
    Attributes
    ---------
    id : int
        Primary key identifier for the player.
    full_name : str
        Full name of the player (non-null, indexed).
    first_name : str
        Player's first name (non-null, indexed).
    last_name : str
        Player's last name (non-null, indexed).
    is_active : bool
        Flag indicating whether the player is currently active (non-null).
    Notes
    -----
    - This class uses SQLAlchemy's `Mapped`/`mapped_column` typing for declarative
      column definitions.
    - The __repr__ implementation returns a compact representation including the
      player's id and full_name.
    """

    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String, index=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String, index=True, nullable=False)
    last_name: Mapped[str] = mapped_column(String, index=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)

    def __repr__(self):
        return f"<Player(id={self.id}, full_name={self.full_name})>"
