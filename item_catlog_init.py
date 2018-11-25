from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import datetime
from database_setup import *

engine = create_engine('sqlite:///itemcatalog.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

# Create fake users
User1 = User(name="sara saad",
             email="sara@hotmail.com")
session.add(User1)
session.commit()


# Create fake categories
Category1 = Category(name="Soccer",
                     user_id=1)
session.add(Category1)
session.commit()

Category2 = Category(name="Basketball",
                     user_id=2)
session.add(Category2)
session.commit

Category3 = Category(name="Baseball",
                     user_id=1)
session.add(Category3)
session.commit()

Category4 = Category(name="Hockey",
                     user_id=1)
session.add(Category4)
session.commit()

Category5 = Category(name="Snowboading",
                     user_id=1)
session.add(Category5)
session.commit()

# Populate a category with items for testing
# Using different users for items also
Item1 = Item(name="Goggles",
             description="close-fitting glasses with side shields,"
             "for protecting the eyes from water",
             category_id=5,
             user_id=1)
session.add(Item1)
session.commit()

Item2 = Item(name="Snowboard",
             description="a board resembling a short, broad ski,"
             " used for sliding downhill on snow.",
             category_id=5,
             user_id=1)
session.add(Item2)
session.commit()

print("Your database has been init")
