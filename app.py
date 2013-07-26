from werkzeug import url_decode
from flask import Flask, abort, render_template
import json
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import create_engine
from sqlalchemy import Integer
from sqlalchemy import Enum
from sqlalchemy import String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import UniqueConstraint
from contextlib import contextmanager   
import functools
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'secret'

Base = declarative_base()
engine = create_engine('sqlite:////tmp/trackroom.db', echo=True)
Session = sessionmaker(bind=engine)


def get_session():
  return Session() 

class Room(Base):
  """Room for checking in"""

  __tablename__ = 'rooms'  

  id = Column(Integer, primary_key=True)
  aux_id = Column(Integer, nullable=False)
  name = Column(String, unique=True, nullable=False)
  occupied = Column(Boolean, default=False)
  floor = Column(Integer, nullable=False)


  def __init__(self, name, occupied, floor, aux_id):
      self.name = name
      self.occupied = occupied
      self.floor = floor
      self.aux_id = aux_id

  def to_dict(self):
		return {'name' : self.name, 'occupied' : self.occupied, 'floor': self.floor, 'id': self.id, 'aux_id': self.aux_id}

def rowtodict(row):
  d = {}
  for column in row.__table__.columns:
    d[column.name] = getattr(row, column.name)
    return d  

Base.metadata.create_all(engine)

def with_session(func):
  @functools.wraps(func)
  def with_session_func(*args, **kwargs):
    session = get_session()
    result = func(session, *args, **kwargs)
    session.commit()
    return result
  return with_session_func  

@app.errorhandler(404)
def page_not_found(e):
	return json.dumps({"status":404}), 404

@with_session
def load_data(session, json_string):
	plans = json.loads(json_string)
	rooms = plans.get('rooms')
	for room_json in rooms:
		try:
			room = Room(room_json.get('name', None), False, room_json.get('floor', None), room_json.get('id', None))
			session.add(room)
		except IntegrityError as error:
			pass

@app.route('/floor/<int:floor_id>')
@with_session
def show_floor(session, floor_id):
  try:
    rooms_on_floor = session.query(Room).filter(Room.floor==floor_id).all()
    room_dicts = []
    for room in rooms_on_floor:
			room_dicts.append(room.to_dict())
  except NoResultFound as error:
		abort(404)

  return json.dumps({'rooms' : room_dicts}), 200 

@app.route('/room/<int:room_id>')
@with_session
def show_room(session, room_id):
  try:
    room = session.query(Room).filter(Room.aux_id==room_id).one().to_dict()
  except NoResultFound as error:
		abort(404)

  return json.dumps(room), 200 

@app.route('/room/checkin/<int:room_id>', methods=['POST',])
@with_session
def check_into_room(session, room_id):
  try:
    room = session.query(Room).filter(Room.id==room_id).all()[0]
  except NoResultFound as error:
		abort(404)
  room.occupied = True
  session.add(room)
  return json.dumps({'status' : 'Succeeded'}), 200

@app.route('/room/checkout/<int:room_id>', methods=['POST',])
@with_session
def check_out_of_room(session, room_id):
  room = None
  try:
    room = session.query(Room).filter(Room.id==room_id).all()[0]
  except NoResultFound as error:
    abort(404)

  room.occupied = False
  session.add(room)
  return json.dumps({'status' : 'Succeeded'}), 200  

@app.route('/rooms')
@with_session
def list_rooms(session):
    rooms = session.query(Room).all() 
    rooms_dicts = [room.to_dict() for room in rooms]
    return json.dumps({'rooms' : rooms_dicts})

@app.route('/')
def homepage():
	return render_template('index.html')

if __name__ == '__main__':
  app.run(host='0.0.0.0')
