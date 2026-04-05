import decimal
import uuid
from typing import Optional, List

from sqlalchemy import Text, DECIMAL, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import Base


movie_genres = Table(
    "movie_genres",
    Base.metadata,
Column("left_id", ForeignKey("movies.id"), primary_key=True),
    Column("right_id", ForeignKey("genres.id"), primary_key=True),
)


movie_stars = Table(
    "movie_stars",
    Base.metadata,
Column("left_id", ForeignKey("movies.id"), primary_key=True),
    Column("right_id", ForeignKey("stars.id"), primary_key=True),
)


movie_directors = Table(
    "movie_directors",
    Base.metadata,
Column("left_id", ForeignKey("movies.id"), primary_key=True),
    Column("right_id", ForeignKey("directors.id"), primary_key=True),
)


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    movies: Mapped[List["Movie"]] = relationship(secondary=movie_genres)


class Star(Base):
    __tablename__ = "stars"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    movies: Mapped[List["Movie"]] = relationship(secondary=movie_stars)


class Director(Base):
    __tablename__ = "directors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    movies: Mapped[List["Movie"]] = relationship(secondary=movie_directors)


class Certification(Base):
    __tablename__ = "certifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)


class Movie(Base):
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uuid: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(nullable=False)
    year: Mapped[int] = mapped_column(nullable=False)
    time: Mapped[int] = mapped_column(nullable=False)
    imdb: Mapped[float] = mapped_column(nullable=False)
    votes: Mapped[int] = mapped_column(nullable=False)
    meta_score: Mapped[Optional[float]] = mapped_column(nullable=True)
    gross: Mapped[Optional[float]] = mapped_column(nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[decimal] = mapped_column(DECIMAL(decimal_return_scale=2), nullable=False)
    certification_id: Mapped[int] = mapped_column(ForeignKey("certifications.id"), nullable=False)
    certification: Mapped[Certification] = relationship(back_populates="movies")
    genres: Mapped[List[Genre]] = relationship(back_populates="movies", secondary=movie_genres)
    directors: Mapped[List[Director]] = relationship(back_populates="movies", secondary=movie_directors)
    stars: Mapped[List[Star]] = relationship(back_populates="movies", secondary=movie_stars)