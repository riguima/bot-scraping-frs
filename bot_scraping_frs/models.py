from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from bot_scraping_frs.database import db


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = 'produtos'
    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str]
    foto: Mapped[str]
    codigo: Mapped[str]
    descricao: Mapped[str]
    valor: Mapped[float]


Base.metadata.create_all(db)
