#!/usr/bin/env python3
from flask import Flask, render_template, request
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Item, Category, User
from flask import redirect, jsonify, url_for, flash, session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)


CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog Application"

# Connect to Database and create database session
engine = create_engine('sqlite:///itemcatalog.db?check_same_thread=False')

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1].decode('utf-8'))
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

# see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id
    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;'
    output += ' -webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    print("done!")
    return output


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print('Access Token is None')
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print('In gdisconnect access token is %s', access_token)
    print('User name is: ')
    print(login_session['username'])
    url = 'https://accounts.google.com/o/oauth2/revoke?'\
          'token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print('result is ')
    print(result)
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(
                    json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except Exception:
        return None


# READ - Selecting a specific item shows you specific information of that item
@app.route('/')
@app.route('/categories')
def showCatalog():
    categories = session.query(Category).all()
    items = session.query(Item).order_by(Item.id.desc()).limit(5).all()
    if 'username' not in login_session:
        return render_template('homepage.html', categories=categories,
                               items=items)
    else:
        return render_template('homepage1.html', categories=categories,
                               items=items, login_session=login_session)


# READ - show category items
@app.route('/categories/<int:category_id>/')
@app.route('/categories/<int:category_id>/items/')
def showCategoryItems(category_id):
    """returns items in category"""
    categories = session.query(Category).all()
    items = session.query(Item).filter_by(
            category_id=category_id).order_by(Item.id.desc())
    category = session.query(Category).filter_by(id=category_id).one()

    if 'username' not in login_session:
        return render_template('homepage.html', categories=categories,
                               category=category, items=items)
    else:
        return render_template('homepage1.html', categories=categories,
                               category=category, items=items,
                               login_session=login_session)


# READ - Selecting a specific item shows you specific information of that item
@app.route('/categories/<int:category_id>/item/<int:item_id>/')
def showItem(category_id, item_id):
    """returns item"""
    category = session.query(Category).filter_by(id=category_id).one()
    item = session.query(
        Item).filter_by(id=item_id).one()

    if 'username' not in login_session:
        return render_template('catlog.html', category=category,
                               item=item)
    else:
        return render_template('catlog1.html', category=category,
                               item=item, login_session=login_session)


# Create a new item
@app.route('/categories/new/', methods=['GET', 'POST'])
def addNewItem():
    categories = session.query(Category).all()
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    if request.method == 'POST':
        newItem = Item(
            name=request.form['name'], description=request.form['description'],
            category_id=session.query(Category).filter_by(
                name=request.form['category']).one().id,
            user_id=login_session['user_id'])
        session.add(newItem)
        session.commit()
        return redirect(url_for('showCatalog'))
    else:
        return render_template('addNewItem.html',
                               categories=categories,
                               login_session=login_session)


# Edit an item
@app.route('/categories/<path:category_id>/item/<path:item_id>/edit',
           methods=['GET', 'POST'])
def editItem(category_id, item_id):
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    editedItem = session.query(Item).filter_by(id=item_id).one()
    categories = session.query(Category).all()
    # See if the logged in user is the owner of item
    creator = getUserInfo(editedItem.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        return "<script>function myFunction() "\
              "{alert('You cannot edit this Item, "\
              "It belongs to "+creator.name+"');"\
              "location.href = '/categories';}</script>"\
              "<body onload='myFunction()'>"
    # POST methods
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['category']:
            category_id = session.query(Category).filter_by(
                name=request.form['category']).one().id
            editedItem.category_id = category_id
        return redirect(url_for('showCategoryItems',
                                category_id=editedItem.category.id))
    else:
        return render_template('edititem.html',
                               item=editedItem, categories=categories,
                               login_session=login_session)


# Delete an item
@app.route('/catalog/<path:category_id>/item/<path:item_id>/delete',
           methods=['GET', 'POST'])
def deleteItem(category_id, item_id):
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    category = session.query(Category).filter_by(id=category_id).one()
    item = session.query(Item).filter_by(id=item_id).one()
    categories = session.query(Category).all()
    # See if the logged in user is the owner of item
    creator = getUserInfo(item.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        return "<script>function myFunction() "\
              "{alert('You cannot edit this Item, "\
              "It belongs to "+creator.name+"');"\
              "location.href = '/categories';}</script>"\
              "<body onload='myFunction()'>"

    if request.method == 'POST':
        session.delete(item)
        session.commit()
        return redirect(url_for('showCategoryItems',
                                category_id=category.id))
    else:
        return render_template('deleteitem.html',
                               item=item, login_session=login_session)


# JSON API
@app.route('/categories/JSON')
def allItemsJSON():
    categories = session.query(Category).all()
    category_dict = [c.serialize for c in categories]
    for c in range(len(category_dict)):
        items = [i.serialize for i in session.query(Item)
                 .filter_by(category_id=category_dict[c]["id"]).all()]
        if items:
            category_dict[c]["Item"] = items
    return jsonify(Category=category_dict)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
