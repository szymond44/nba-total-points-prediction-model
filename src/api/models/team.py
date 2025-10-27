from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..db.engine import Base


class Team(Base):
    """ORM model representing a sports team.
    This SQLAlchemy declarative model maps to the "teams" table and describes
    the persistent attributes of a team entity stored in the database.
    Attributes
    ----------
    id : int
        Primary key for the table. Integer, indexed.
    name : str
        Team full name. Non-nullable, unique, and indexed.
    city : str
        City where the team is based. Non-nullable.
    abbreviation : str
        Short unique code for the team (e.g. "NYK"). Non-nullable, unique, and indexed.
    nickname : str
        Team nickname. Non-nullable.
    state : str | None
        Optional state or region for the team. Nullable.
    year_founded : int | None
        Optional year the team was founded. Nullable.
    Notes
    -----
    - Fields are defined using SQLAlchemy typing (Mapped[]) and mapped_column to
      declare column types and constraints.
    - Uniqueness and indexing constraints exist for convenience and performance
      (e.g., lookup by name or abbreviation).
    - Instances of this class are ORM-mapped objects; attributes correspond to
      database columns and can be used in queries, inserts, and updates.
    Examples
    --------
    Creating a new Team instance:
        team = Team(
            name="City Club",
            city="Metropolis",
            abbreviation="CC",
            nickname="Clubs",
            state="StateName",         # optional
            year_founded=1901          # optional
    Representation
    --------------
    The model defines a __repr__ that includes the id and name for easy debugging.
    """

    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    city: Mapped[str] = mapped_column(String, nullable=False)
    abbreviation: Mapped[str] = mapped_column(
        String, unique=True, index=True, nullable=False
    )
    nickname: Mapped[str] = mapped_column(String, nullable=False)
    state: Mapped[str] = mapped_column(String, nullable=True)
    year_founded: Mapped[int] = mapped_column(Integer, nullable=True)

    def __repr__(self):
        return f"<Team(id={self.id}, name={self.name})>"
