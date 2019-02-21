from pony.orm import *

set_sql_debug(False)
db = Database()

class User(db.Entity):
    tguser_id = PrimaryKey(int)
    tgusername = Required(str)
    tgfirstname = Required(str)


class Show(db.Entity):
    show_id = PrimaryKey(int, auto=True)
    show_title = Required(str, unique=True)
    show_airing_day = Required(str)
    show_airing_time = Required(str)


class Subscription(db.Entity):
    ext_user_id = Required(int)
    ext_show_id = Required(int)
    sub_id = PrimaryKey(ext_user_id, ext_show_id)


db.bind(provider='sqlite', filename='data.db', create_db=True)
db.generate_mapping(create_tables=True)

@db_session
def insert_user(userid: int, username: str, firstname: str):
    User(tguser_id=userid, tgusername=username, tgfirstname=firstname)

@db_session
def insert_show(title: str, airday: str, airtime: str):
    Show(show_title=title, show_airing_day=airday, show_airing_time=airtime)

@db_session
def insert_subscription(userid: int, showid: int):
    Subscription(ext_user_id=userid, ext_show_id=showid)

@db_session
def remove_subscription(userid: int, showid: int):
    select(sub for sub in Subscription if sub.ext_user_id == userid and sub.ext_show_id == showid)[:][0].delete()

@db_session
def get_show_id_by_name(title: str):
    return select(s.show_id for s in Show if s.show_title == title)[:][0]

@db_session
def check_subscribed(userid: int, showid: int):
    if len(select(sub for sub in Subscription if sub.ext_user_id == userid and sub.ext_show_id == showid)[:]) > 0:
        return True
    else:
        return False

@db_session
def check_user_exists(userid: int):
    if len(select(u for u in User if userid == u.tguser_id)[:]) > 0:
        return True
    else:
        return False
