import string
import item
from db import dbselect, dbdelete, newmove
from utils import cleanstr, invbuild

def get(tweet):
    if len((tweet).split()) >= 2:
        a, b = (tweet).split(' ',1)
        a = ''.join(ch for ch in a if ch not in set(string.punctuation)).lower()
        if (a == 'drop'):
            if dbselect('name', 'items', 'name', cleanstr(b)) != None:
                return a
        elif (a == 'give'):
            c, d = (b).split(' ',1)
            if dbselect('name', 'items', 'name', cleanstr(d)) != None:
                return a
        elif (a == 'liltadd') and ((user['id'] == '15332057') or (user['id'] == '724754312757272576')):
            return a
        else:
            return None
    else:
        return None
def drop(tweet, inventory, id):
    item_to_drop = (tweet).split(' ',1)[1]
    return item.drop(cleanstr(item_to_drop), inventory, id)
def give(tweet, inventory, id, position):
    b = (tweet).split(' ',1)[1]
    c, d = (b).split(' ',1)
    return item.give(cleanstr(d), inventory, id, position, ''.join(ch for ch in c if ch not in set(string.punctuation)).lower())
def inventory(inventory):
    if inventory == {}:
        return 'Your inventory is empty at the moment.'
    else:
        return invbuild(inventory)
def deleteme(id):
    dbdelete('users', 'id', id)
    return 'You\'ve been removed from Lilt. Thanks for playing!'
def liltadd(tweet, position):
    b = (tweet).split(' ',1)[1]
    addmove, addresponse = (b).split('~',1)
    newmove(addmove, addresponse, position)
    return '\'' + addmove + '\' was added to Lilt.'
