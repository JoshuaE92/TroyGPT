
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base

DATABASE_URL="sqlite:///./game.db" #the actual connection to the created game.db
engine=create_engine(DATABASE_URL,connect_args={"check_same_thread":False})  #connection to database, allwo for connection to be made across multipel threads
SessionLocal=sessionmaker(autocommit=False,autoflush=False,bind=engine)#sesion maker, session=transactions/read and writes, autoocomit=false=dont auto comit,
#autoflush=false stops from pushign qued objects to db b4 new query, bind=bind to engine/db created form b4
Base.metadata.create_all(bind=engine)#actually crates the tables n such, if not created go head and make al



def get_db():#inject into route used later to create a new database session instance
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()


