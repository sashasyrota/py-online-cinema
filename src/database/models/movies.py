import decimal
import uuid
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import Text, DECIMAL, ForeignKey, Table, Column, types, UniqueConstraint, UUID, Uuid, String, Integer
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models.base import Base

if TYPE_CHECKING:
    from src.database.models.accounts import User
    from src.database.models.orders import OrderItem


movies_users_who_add_to_favourite= Table(
    "movies_users_who_add_to_favourite",
    Base.metadata,
Column("movies_id", ForeignKey("movies.id"), primary_key=True),
    Column("users_id", ForeignKey("users.id"), primary_key=True),
)

movie_genres = Table(
    "movie_genres",
    Base.metadata,
Column("movies_id", ForeignKey("movies.id"), primary_key=True),
    Column("genres_id", ForeignKey("genres.id"), primary_key=True),
)


movie_stars = Table(
    "movie_stars",
    Base.metadata,
Column("movies_id", ForeignKey("movies.id"), primary_key=True),
    Column("stars_id", ForeignKey("stars.id"), primary_key=True),
)


movie_directors = Table(
    "movie_directors",
    Base.metadata,
Column("movies_id", ForeignKey("movies.id"), primary_key=True),
    Column("directors_id", ForeignKey("directors.id"), primary_key=True),
)

class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    movies: Mapped[List["Movie"]] = relationship(secondary=movie_genres, lazy="joined")

    @property
    def movies_count(self):
        return len(self.movies)


class Star(Base):
    __tablename__ = "stars"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    movies: Mapped[List["Movie"]] = relationship(secondary=movie_stars, lazy="joined")

    @property
    def movies_count(self):
        return len(self.movies)


class Director(Base):
    __tablename__ = "directors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    movies: Mapped[List["Movie"]] = relationship(secondary=movie_directors)


class Certification(Base):
    __tablename__ = "certifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    movies: Mapped[List["Movie"]] = relationship(back_populates="certification")


class LikeMovie(Base):
    __tablename__ = "likes_movies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), nullable=False)
    user: Mapped["User"] = relationship(back_populates="likes_movies")
    movie: Mapped["Movie"] = relationship(back_populates="likes_movies")

    __table_args__ = (UniqueConstraint('user_id', 'movie_id', name='user_movie_like_uc'),)


class DislikeMovie(Base):
    __tablename__ = "dislikes_movies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), nullable=False)
    user: Mapped["User"] = relationship(back_populates="dislikes_movies")
    movie: Mapped["Movie"] = relationship(back_populates="dislikes_movies")

    __table_args__ = (UniqueConstraint('user_id', 'movie_id', name='user_movie_dislike_uc'),)


class Rate(Base):
    __tablename__ = "rates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    rate: Mapped[int] = mapped_column(nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), nullable=False)
    user: Mapped["User"] = relationship(back_populates="rates")
    movie: Mapped["Movie"] = relationship(back_populates="rates")

    __table_args__ = (UniqueConstraint('user_id', 'movie_id', name='user_movie_rate_uc'),)


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    text: Mapped[str] = mapped_column(String(1000), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), nullable=False)
    user: Mapped["User"] = relationship(back_populates="comments")
    movie: Mapped["Movie"] = relationship(back_populates="comments")
    reply_comment_id: Mapped[int] = mapped_column(ForeignKey("comments.id"), nullable=True)
    likes_comments: Mapped[List["LikeComment"]] = relationship(back_populates="comment", lazy="joined")
    dislikes_comments: Mapped[List["DislikeComment"]] = relationship(back_populates="comment", lazy="joined")

class Movie(Base):
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4)
    name: Mapped[str] = mapped_column(nullable=False)
    year: Mapped[int] = mapped_column(nullable=False)
    time: Mapped[int] = mapped_column(nullable=False)
    imdb: Mapped[float] = mapped_column(nullable=False)
    votes: Mapped[int] = mapped_column(nullable=False)
    meta_score: Mapped[Optional[float]] = mapped_column(nullable=True)
    gross: Mapped[Optional[float]] = mapped_column(nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[decimal] = mapped_column(DECIMAL(10,2), nullable=False)
    certification_id: Mapped[int] = mapped_column(ForeignKey("certifications.id"), nullable=False)
    certification: Mapped[Certification] = relationship(back_populates="movies", lazy="joined")
    genres: Mapped[List[Genre]] = relationship(back_populates="movies", secondary=movie_genres, lazy="joined")
    directors: Mapped[List[Director]] = relationship(back_populates="movies", secondary=movie_directors, lazy="joined")
    stars: Mapped[List[Star]] = relationship(back_populates="movies", secondary=movie_stars, lazy="joined")
    likes_movies: Mapped[List[LikeMovie]] = relationship(back_populates="movie", lazy="joined")
    dislikes_movies: Mapped[List[DislikeMovie]] = relationship(back_populates="movie", lazy="joined")
    comments: Mapped[List[Comment]] = relationship(back_populates="movie", lazy="joined")
    order_items: Mapped[List["OrderItem"]] = relationship(back_populates="movie", lazy="joined")
    who_add_to_favourite: Mapped[List["User"]] = relationship(back_populates="favourite_movies", secondary=movies_users_who_add_to_favourite, lazy="joined")
    rates: Mapped[List[Rate]] = relationship(back_populates="movie", lazy="joined")


    __table_args__ = (UniqueConstraint('name', 'year', 'time', name='name_year_time_uc'),)

    @property
    def likes_count(self):
        return len(self.likes_movies)

    @property
    def dislikes_count(self):
        return len(self.dislikes_movies)


class LikeComment(Base):
    __tablename__ = "likes_comments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    comment_id: Mapped[int] = mapped_column(ForeignKey("comments.id"), nullable=False)
    user: Mapped["User"] = relationship(back_populates="likes_comments")
    comment: Mapped["Comment"] = relationship(back_populates="likes_comments")

    __table_args__ = (UniqueConstraint('user_id', 'comment_id', name='user_comment_like_uc'),)


class DislikeComment(Base):
    __tablename__ = "dislikes_comments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    comment_id: Mapped[int] = mapped_column(ForeignKey("comments.id"), nullable=False)
    user: Mapped["User"] = relationship(back_populates="dislikes_comments")
    comment: Mapped["Comment"] = relationship(back_populates="dislikes_comments")


    __table_args__ = (UniqueConstraint('user_id', 'comment_id', name='user_comment_dislike_uc'),)