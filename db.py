# -*- coding: utf-8 -*-

# External
import json
import os
import psycopg2
from urllib import parse

# Internal
from constants import COLOR, DEBUG


# Initialize PostgreSQL database
parse.uses_netloc.append('postgres')
url = parse.urlparse(os.environ['DATABASE_URL'])
conn = psycopg2.connect(
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port
)
cur = conn.cursor()


def do(action, table, data, val=None):  # all of these need to return something
    if action == 'insert':
        # 'INSERT INTO table (x, y, z) VALUES (%s, %s, %s);', ('1','2','3',)
        dbstate = 'INSERT INTO ' + table + ' ('
        # 'INSERT INTO table ('
        tq = 0
        dbdata = ()
        for key in data:
            tq += 1
            if tq == 1:
                dbstate = dbstate + str(key)
                # 'INSERT INTO table (x'
            else:
                dbstate = dbstate + ', ' + str(key)
                # 'INSERT INTO table (x, y, z'
            if type(data[key]) is dict:
                dbdata = dbdata + (json.dumps(data[key]),)
            else:
                dbdata = dbdata + (data[key],)
            # ('1','2','3',)
        dbstate = dbstate + ') VALUES (%s' + ', %s'*(tq-1) + ');'
        # 'INSERT INTO table (x, y, z) VALUES (%s, %s, %s);', ('1','2','3',)
    elif action == 'select':
        # 'SELECT a FROM table WHERE x = %s AND y = %s AND z = %s;',('1','2','3',)
        dbstate = 'SELECT ' + val + ' FROM ' + table + ' WHERE '
        # 'SELECT a FROM table WHERE '
        tq = 0
        dbdata = ()
        for key in data:
            tq += 1
            if tq == 1:
                dbstate = dbstate + str(key) + ' = %s'
                # 'SELECT a FROM table WHERE x = %s'
            else:
                dbstate = dbstate + ' AND ' + str(key) + ' = %s'
                # 'SELECT a FROM table WHERE x = %s AND y = %s AND z = %s'
            if type(data[key]) is dict:
                dbdata = dbdata + (json.dumps(data[key]),)
            else:
                dbdata = dbdata + (data[key],)
            # ('1','2','3',)
        dbstate = dbstate + ';'
        # 'SELECT a FROM table WHERE x = %s AND y = %s AND z = %s;',('1','2','3',)
    elif action == 'delete':
        # 'DELETE FROM table WHERE x = %s AND y = %s AND z = %s;',('1','2','3',)
        dbstate = 'DELETE FROM ' + table + ' WHERE '
        # 'DELETE FROM table WHERE '
        tq = 0
        dbdata = ()
        for key in data:
            tq += 1
            if tq == 1:
                dbstate = dbstate + str(key) + ' = %s'
                # 'DELETE FROM table WHERE x = %s'
            else:
                dbstate = dbstate + ' AND ' + str(key) + ' = %s'
                # 'DELETE FROM table WHERE x = %s AND y = %s AND z = %s'
            if type(data[key]) is dict:
                dbdata = dbdata + (json.dumps(data[key]),)
            else:
                dbdata = dbdata + (data[key],)
            # ('1','2','3',)
        dbstate = dbstate + ';'
        # 'DELETE FROM table WHERE x = %s AND y = %s AND z = %s;',('1','2','3',)
    elif action == 'update':
        # 'UPDATE table SET a = %s WHERE x = %s AND y = %s AND z = %s;'('0','1','2','3',)
        dbstate = 'UPDATE ' + table + ' SET ' + \
            list(val.keys())[0] + ' = %s WHERE '
        # 'UPDATE table SET a = %s WHERE '
        tq = 0
        if type(list(val.values())[0]) is dict:
            dbdata = (json.dumps(list(val.values())[0]),)
        else:
            dbdata = (list(val.values())[0],)
        # ('0',)
        for key in data:
            tq += 1
            if tq == 1:
                dbstate = dbstate + str(key) + ' = %s'
                # 'SELECT a FROM table WHERE x = %s'
            else:
                dbstate = dbstate + ' AND ' + str(key) + ' = %s'
                # 'SELECT a FROM table WHERE x = %s AND y = %s AND z = %s'
            if type(data[key]) is dict:
                dbdata = dbdata + (json.dumps(data[key]),)
            else:
                dbdata = dbdata + (data[key],)
            # ('0','1','2','3',)
        dbstate = dbstate + ';'
        # 'SELECT a FROM table WHERE x = %s AND y = %s AND z = %s;',('0','1','2','3',)
    cur.execute(dbstate, dbdata)
    if action == 'select':
        return cur.fetchall()
    else:
        conn.commit()
        return


def select(col1, table, col2, val, position=None, condition=None, quantity='one'):
    if condition != None:
        cur.execute("SELECT " + col1 + " FROM " + table +
                    " WHERE move = %s AND position = %s AND condition = %s;", (val, position, json.dumps(condition)))
    elif position != None:
        cur.execute("SELECT " + col1 + " FROM " + table +
                    " WHERE move = %s AND position = %s AND condition IS NULL;", (val, position))
    else:
        cur.execute("SELECT " + col1 + " FROM " + table +
                    " WHERE " + col2 + " = %s;", (val,))

    if quantity == 'one':
        o = cur.fetchone()
        if o == None:
            if DEBUG.DB:
                print(COLOR.BLUE + 'Returning None.' + COLOR.END)
            return o
        else:
            if DEBUG.DB:
                print(COLOR.BLUE + 'Returning one:' + COLOR.END, o[0])
            return o[0]
    else:
        o = cur.fetchall()
        if DEBUG.DB:
            print(COLOR.BLUE + 'Returning all:' + COLOR.END, o)
        return o


def update(val1, val2, col='inventory'):
    if DEBUG.DB:
        print(COLOR.BLUE + 'Updating database.' + COLOR.END)
    if (col != 'inventory') and (col != 'events') and (col != 'attempts'):
        cur.execute("UPDATE users SET " + col +
                    " = %s WHERE id = %s;", (val1, val2))
    elif col == 'attempts':
        cur.execute(
            "UPDATE attempts SET attempts = %s WHERE move = %s", (val1, val2))
    else:
        cur.execute("UPDATE users SET " + col +
                    " = %s WHERE id = %s;", (json.dumps(val1), val2))
    conn.commit()


def delete(table, col, val):
    if table == 'console':
        cur.execute("DELETE FROM " + table +
                    " WHERE " + col + " != %s;", (val,))
        conn.commit()
    else:
        cur.execute("DELETE FROM " + table +
                    " WHERE " + col + " = %s;", (val,))
        conn.commit()


def newuser(name, id, tweet_id, position, inventory, events):
    cur.execute("INSERT INTO users (name, id, last_tweet_id, position, inventory, events) VALUES (%s, %s, %s, %s, %s, %s)",
                (name, id, tweet_id, position, json.dumps(inventory), json.dumps(events)))
    conn.commit()


def newmove(move, response, position, traits=None):
    if traits == None:
        cur.execute("INSERT INTO moves (move, response, position) VALUES (%s, %s, %s)",
                    (move, response, position))
        conn.commit()
    else:
        tq = 0
        dbcallstart = "INSERT INTO moves (move, response, position"
        dbdata = (move, response, position)
        for trait in traits:
            tq += 1
            dbcallstart = dbcallstart + ', ' + str(trait)
            if type(traits[trait]) is dict:
                dbdata = dbdata + (json.dumps(traits[trait]),)
            else:
                # must factor if inputting json (json.dumps)
                dbdata = dbdata + (traits[trait],)
        dbcallend = ") VALUES (%s, %s, %s" + ', %s'*tq + ")"
        cur.execute(dbcallstart + dbcallend, dbdata)
        conn.commit()


def copy_move(ogmove, newmove, position):
    cur.execute("INSERT INTO moves (move, response, position, item, condition, trigger, drop, travel) SELECT %s, response, position, item, condition, trigger, drop, travel FROM moves WHERE move = %s AND position = %s;", (newmove, ogmove, position))
    conn.commit()


def new_item(traits):
    tq = 0
    dbcallstart = "INSERT INTO items ("
    dbdata = ()
    for trait in traits:
        tq += 1
        if tq == 1:
            dbcallstart = dbcallstart + str(trait)
        else:
            dbcallstart = dbcallstart + ', ' + str(trait)
        # must factor if inputting json (json.dumps)
        dbdata = dbdata + (traits[trait],)
    dbcallend = ") VALUES (%s" + ', %s'*(tq-1) + ")"
    cur.execute(dbcallstart + dbcallend, dbdata)
    conn.commit()


def store_error(move, position):
    # Check if someone has attempted to make this failed move before.
    attempt = select('attempts', 'attempts', 'move', move, position)

    # If no, add it as a new entry.
    if attempt == None:
        cur.execute("INSERT INTO attempts (move, position, attempts) VALUES (%s, %s, %s)", (str(
            move), str(position), 1))
        conn.commit()
    else:
        # Someone else attempted this move previously, update the attempt count.
        update(attempt + 1, move, 'attempts')
