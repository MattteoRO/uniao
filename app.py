import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
import random
import json

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "brain_training_secret_key")

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
db.init_app(app)

# Import models after initializing db
from models import *

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/new-game')
def new_game():
    """New game setup page"""
    # Reset game-related session data
    for key in ['current_game', 'players', 'score', 'current_round', 'total_rounds']:
        if key in session:
            session.pop(key)
    return render_template('new_game.html')

@app.route('/setup-game', methods=['POST'])
def setup_game():
    """Process game setup form"""
    players = []
    # Get player names from form
    for i in range(1, 5):  # Supporting up to 4 players
        player_name = request.form.get(f'player{i}', '').strip()
        if player_name:
            players.append(player_name)
    
    if not players:
        return redirect(url_for('new_game'))
    
    # Get game settings
    categories = request.form.getlist('categories')
    difficulty = request.form.get('difficulty', 'medium')
    rounds = int(request.form.get('rounds', 5))
    
    if not categories:
        categories = ['geography', 'history', 'art', 'food', 'traditions']
    
    # Store game settings in session
    session['players'] = players
    session['current_game'] = {
        'categories': categories,
        'difficulty': difficulty,
    }
    session['score'] = {player: 0 for player in players}
    session['current_round'] = 0
    session['total_rounds'] = rounds
    
    return redirect(url_for('game'))

@app.route('/game')
def game():
    """Main game page"""
    if 'current_game' not in session:
        return redirect(url_for('new_game'))
    
    # Advance to next round
    session['current_round'] = session.get('current_round', 0) + 1
    
    # Check if game is over
    if session['current_round'] > session['total_rounds']:
        return redirect(url_for('results'))
    
    return render_template('game.html', 
        players=session['players'],
        score=session['score'],
        current_round=session['current_round'],
        total_rounds=session['total_rounds'])

@app.route('/get-question')
def get_question():
    """AJAX endpoint to get a new question"""
    if 'current_game' not in session:
        return jsonify({'error': 'No active game'})
    
    # Get random question based on current game settings
    categories = session['current_game']['categories']
    difficulty = session['current_game']['difficulty']
    
    # Query database for questions matching criteria
    questions = Question.query.filter(
        Question.category.in_(categories),
        Question.difficulty == difficulty
    ).all()
    
    if not questions:
        # Fallback to get any question if no matches
        questions = Question.query.all()
    
    if not questions:
        return jsonify({
            'error': 'No questions available',
            'question': 'What is the capital of France?',
            'options': ['Paris', 'London', 'Berlin', 'Madrid'],
            'correct': 'Paris',
            'culture': 'Europe',
            'explanation': 'Paris is the capital and most populous city of France.'
        })
    
    # Select random question
    question = random.choice(questions)
    
    # Format question data for frontend
    options = json.loads(question.options)
    
    return jsonify({
        'id': question.id,
        'question': question.question_text,
        'options': options,
        'correct': question.correct_answer,
        'culture': question.culture,
        'category': question.category,
        'explanation': question.explanation,
        'image_url': question.image_url
    })

@app.route('/submit-answer', methods=['POST'])
def submit_answer():
    """AJAX endpoint to submit an answer"""
    if 'current_game' not in session:
        return jsonify({'error': 'No active game'})
    
    data = request.json
    player_name = data.get('player')
    is_correct = data.get('correct', False)
    
    # Update score
    if player_name in session['score'] and is_correct:
        session['score'][player_name] += 1
        session.modified = True
    
    return jsonify({
        'success': True,
        'updated_score': session['score']
    })

@app.route('/results')
def results():
    """Game results page"""
    if 'score' not in session:
        return redirect(url_for('new_game'))
    
    # Calculate winner
    scores = session['score']
    max_score = max(scores.values()) if scores else 0
    winners = [player for player, score in scores.items() if score == max_score]
    
    return render_template('results.html', 
        scores=scores,
        winners=winners)

@app.route('/leaderboard')
def leaderboard():
    """Display global leaderboard"""
    # Get top scores from database
    top_scores = GameResult.query.order_by(GameResult.score.desc()).limit(10).all()
    return render_template('leaderboard.html', top_scores=top_scores)

@app.route('/save-result', methods=['POST'])
def save_result():
    """Save game result to leaderboard"""
    if 'score' not in session:
        return redirect(url_for('new_game'))
    
    data = request.form
    player_name = data.get('player_name')
    score = session['score'].get(player_name, 0)
    
    # Save to database
    result = GameResult(
        player_name=player_name,
        score=score,
        difficulty=session['current_game'].get('difficulty', 'medium')
    )
    db.session.add(result)
    db.session.commit()
    
    return redirect(url_for('leaderboard'))

@app.route('/about')
def about():
    """About page with game information"""
    return render_template('about.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)