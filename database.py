from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class UserState(Base):
    __tablename__ = 'user_states'
    user_id = Column(Integer, primary_key=True)
    state = Column(String(50))
    data = Column(Text)

class Database:
    def __init__(self, db_url='sqlite:///bot.db'):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def save_state(self, user_id, state, data):
        session = self.Session()
        try:
            record = session.query(UserState).filter_by(user_id=user_id).first() or UserState(user_id=user_id)
            record.state = state
            record.data = json.dumps(data)
            session.add(record)
            session.commit()
        finally:
            session.close()

    def get_state(self, user_id):
        session = self.Session()
        try:
            record = session.query(UserState).filter_by(user_id=user_id).first()
            return json.loads(record.data) if record else None
        finally:
            session.close()