from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy import create_engine


Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)


class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return the data as Json object"""
        return {
            'id': self.id,
            'name': self.name,
            'user_id': self.user_id
        }


class Item(Base):
    __tablename__ = 'item'

    name = Column(String(255), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(255))
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(
        "Category", backref=backref("items", cascade="all, delete"))

    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return the data as Json object"""
        return {
            'name': self.name,
            'description': self.description,
            'id': self.id,
            'category_id': self.category_id,
            'user_id': self.user_id
        }


engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.create_all(engine)
