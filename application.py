import os
import requests
import json
from flask import Flask, session, render_template, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")


# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

#---------------------------------------------------------------------app.routes
#Homepage
@app.route("/",methods=["GET", "POST"])
def index():
    print(session.get("isLoggedIn"))
    if(session.get("isLoggedIn") is None):
        session["isLoggedIn"] = False

    return render_template("index.html")


#Registration form page
@app.route("/registration",methods=["GET"])
def registration():
    return render_template("registration.html")


#registration database commit & confirmation
@app.route("/registered",methods=["POST"])
def registered():
    username = request.form.get("username")
    password = request.form.get("password")
    print(username, password)
    db.execute("INSERT INTO credentials (username, password) VALUES (:username, :password)",{"username":username, "password":password})
    db.commit()
    session["isLoggedIn"] = True
    if username is None:
        return render_template("error.html", message="Error")
    return render_template("hello.html",username=username, password=password)


#Login form
@app.route("/login",methods=["GET"])
def login():
    return render_template("login.html")


#Login check database for user/pass
@app.route("/loggedIn", methods=["POST"])
def logged():
    username = request.form.get("username")
    password = request.form.get("password")
    correctInfo = db.execute("SELECT username, password FROM credentials WHERE (username=:username) AND (password=:password)",{"username":username, "password":password}).fetchone()
    if correctInfo is None:
        return "incorrect password"
    session["isLoggedIn"] = True
    print(session.get("isLoggedIn"))
    return f"Welcome, {username}"


#Logs user out of session
@app.route("/logout", methods=["GET"])
def logout():
    if(session.get("isLoggedIn") == True):
        session["isLoggedIn"] = False
        return "You are logged out"
    else:
        return "You are already logged out"


#Takes user to search form
@app.route("/searchBook", methods=["GET"])
def search():
    session["isLoggedIn"] = True
    if(session["isLoggedIn"] == False):
        return "You must login to search for books"
    return render_template("search.html")


#Displays results based on search
@app.route("/searchResults/", methods=["GET", "POST"])
def searchResults():
    session["isLoggedIn"] = True
    searchInfo = request.form.get("searchInfo")
    print(searchInfo)
    if(session["isLoggedIn"] is False):
        return "You must login to search for books"
    book = db.execute("SELECT * FROM books WHERE title LIKE :searchKey OR isbn LIKE :searchKey",{"searchKey": "%" + searchInfo + "%"}).fetchall()
    return render_template("results.html", book=book)


#Displays specific book info and reviews
@app.route("/bookPage/<string:book>", methods=["GET", "POST"])
def bookPage(book):

    #Requesting book info from database
    bookInfo = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn":book}).fetchone()
    print(bookInfo)
    #JSON GoodReads API request
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "Ofp1GU7uUbEelrn6ZrT9w", "isbns": book})
    print(res.json())
    parsed = res.json()
    bookJson= parsed["books"]
    print(bookJson)

    #parsing ratings info from JSON
    numRatings = bookJson[0]["ratings_count"]
    average_rating = bookJson[0]["average_rating"]

    return render_template("bookPage.html", numRatings=numRatings, average_rating=average_rating, book=bookInfo)