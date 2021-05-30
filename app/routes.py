import json
import random
from flask import render_template, request, redirect, jsonify, flash
from flask_login import current_user, login_user, logout_user, login_required
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter
from app import app, db
from app.models import Card, User
from app.forms import LoginForm, RegistrationForm

import os
import openai
from random import randrange

openai.api_key = ""

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect("/")
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect("/login")
    return render_template('register.html', title='Register', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect("/")
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect("/login")
        login_user(user, remember=form.remember_me.data)
        return redirect("/")
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect("/login")    

@app.route("/")
@login_required
def index():
    try:
        u = User.query.get(current_user.id)
        cards = u.posts.all()
        topics = set(list(t.topic for t in cards))
        random_card = random.choice(cards)
        total_cards = len(cards)
        all_topics_len = len(topics)
        all_topics = sorted(topics)
    except:
        random_card = None
        total_cards = 0
        all_topics_len = 0
        all_topics = 0

    return render_template("index.html", card=random_card, total_cards=total_cards, all_topics_len=all_topics_len, all_topics=all_topics)

@app.route("/cards/new", methods=["GET", "POST"])
def new_card():
    u = User.query.get(current_user.id)

    if request.method == "GET":
        all_topics = sorted(set([t.topic for t in u.posts.all()]))
        return render_template("new.html", all_topics=all_topics)
    else:
        #category = request.form["category"]      
        topic = request.form["topic"]
        question = request.form["question"]
        
        #openai.api_key = os.getenv("OPENAI_API_KEY")

        category = ["Acrostic", "Acronym", "Story", "Simple Explanation"]

        #random_index = randrange(len(category))
        #print(category[random_index])
        #category = category[random_index]

        finalQuestion = question

        for c in category:
            response = openai.Completion.create(
                engine="davinci",
                prompt="Come up with an acrostic mnemonic device for the spelling of the word Psychology\nDescription: PSYCHOLOGY\nMnemonic Device: Please Say You Can Hit Old Ladies, Or Get Yogurt.\n\"\"\"\nCome up with an acrostic mnemonic device for the spelling for the Goal of Psychology\nDescription: Describe, Explain, Predict, and Control Behavior\nMnemonic Device: Don’t Eat Peanut Cookies, Boys\n\"\"\"\Come up with a story mnemonic device about the Hippocampus\nDescription: the brain structure (Hippocampus) that processes explicit memories (such as personal experiences)\nMnemonic Device: If you saw a Hippo on Campus, you would remember it\n\"\"\"Come up with a "+ c +" mnemonic device for " + topic + "\nDescription: " + question + "\nMnemonic Device:",
                temperature=0.7,
                max_tokens=100,
                top_p=0.9,
                frequency_penalty=0.18,
                presence_penalty=0.2,
                stop=["\"\"\""]
            )

            #print(response["choices"][0]["text"])

            finalQuestion += "\nMnemonic(" + c + "):" + response["choices"][0]["text"]
        
        #if category == 'code':
            #using pygments to store code as html elements for highlighting.
            #question = highlight(question, PythonLexer(), HtmlFormatter())

        card = Card(category[0], topic, finalQuestion, author=u)
        db.session.add(card)
        db.session.commit()

        return render_template("new.html", topic=topic, question=finalQuestion, mnemonic=response["choices"][0]["text"])

# All cards
@app.route("/cards")
def show_cards():
    u = User.query.get(current_user.id)
    cards = sorted(u.posts.all(), key=lambda card:card.topic)
    return render_template("cards.html", cards=cards)

# ---------------------------------------------------------------
'''
Can refactor this.

Make a form that given a certain request.form (e.g) it would handle the
constraints.

Like if checkbox == category or topic do first querying, else do second.
'''
# Cards by category: General vs Code
@app.route("/cards/category/<string:card_category>")
def get_card_category(card_category):
    u = User.query.get(current_user.id)
    cards = [c for c in u.posts.all() if c.category == card_category]
    return render_template("cards.html", cards=cards)

# Cards by Topic.
@app.route("/cards/topic/<string:card_topic>")
def get_card_topic(card_topic):
    u = User.query.get(current_user.id)
    cards = [c for c in u.posts.all() if c.topic == card_topic]
    print(cards)
    return render_template("cards.html", cards=cards)

# ---------------------------------------------------------------

# Show card's form with card info populated on form based on card id.
@app.route("/cards/<int:card_id>")
def get_card(card_id):
    u = User.query.get(current_user.id)
    card = [c for c in u.posts.all() if c.id == card_id]
    return render_template("show.html", card=card[0])

# Update card.
@app.route("/cards/<int:card_id>", methods=["POST"])
def edit(card_id):
    # TODO
        # Only show cards respective to user.
    card = Card.query.get(card_id)
    card.question = request.form["question"]
    card.topic = request.form["topic"]
    
    db.session.commit()
    return redirect("/")

@app.route("/cards/<int:card_id>/delete", methods=["POST"])
def delete_card(card_id):
    # TODO
        # Only show cards respective to user.
    Card.query.filter_by(id=card_id).delete()
    db.session.commit()
    return redirect("/")
