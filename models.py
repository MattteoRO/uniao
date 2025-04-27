from app import db
from datetime import datetime

class Question(db.Model):
    """Database model for questions"""
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.String(500), nullable=False)
    options = db.Column(db.String(1000), nullable=False)  # JSON string of options
    correct_answer = db.Column(db.String(500), nullable=False)
    explanation = db.Column(db.Text)
    category = db.Column(db.String(50), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False, default='medium')
    culture = db.Column(db.String(100))
    image_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class GameResult(db.Model):
    """Database model for game results/leaderboard"""
    id = db.Column(db.Integer, primary_key=True)
    player_name = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)
    played_at = db.Column(db.DateTime, default=datetime.utcnow)

# Sample question data for initial database setup
def add_sample_questions():
    """Add sample questions to the database"""
    sample_questions = [
        # Geography
        {
            'question_text': 'What is the traditional stilt house found in many parts of Southeast Asia called?',
            'options': '["Nipa hut", "Longhouse", "Batak house", "Stilted pavilion"]',
            'correct_answer': 'Nipa hut',
            'explanation': 'Nipa huts, also known as "bahay kubo" in the Philippines, are traditional homes built on stilts found throughout Southeast Asia, particularly in rural areas.',
            'category': 'geography',
            'difficulty': 'medium',
            'culture': 'Southeast Asia',
            'image_url': '/static/images/nipa-hut.jpg'
        },
        {
            'question_text': 'Which African natural feature is known as "the smoke that thunders"?',
            'options': '["Mount Kilimanjaro", "Victoria Falls", "The Sahara Desert", "Lake Victoria"]',
            'correct_answer': 'Victoria Falls',
            'explanation': 'Victoria Falls on the Zambezi River is known locally as "Mosi-oa-Tunya" which translates to "the smoke that thunders" due to the massive spray and noise the falls create.',
            'category': 'geography',
            'difficulty': 'medium',
            'culture': 'Southern Africa',
            'image_url': '/static/images/victoria-falls.jpg'
        },
        
        # History
        {
            'question_text': 'Which ancient Mesoamerican civilization is known for creating a highly accurate calendar system?',
            'options': '["Aztec", "Inca", "Maya", "Olmec"]',
            'correct_answer': 'Maya',
            'explanation': 'The Maya civilization created an incredibly accurate calendar system that included multiple calendar cycles, including the 260-day Tzolkin and the 365-day Haab.',
            'category': 'history',
            'difficulty': 'medium',
            'culture': 'Mesoamerica',
            'image_url': '/static/images/mayan-calendar.jpg'
        },
        {
            'question_text': 'Which Japanese historical period is known for its samurai, shoguns, and feudal system?',
            'options': '["Meiji Period", "Edo Period", "Heian Period", "Nara Period"]',
            'correct_answer': 'Edo Period',
            'explanation': 'The Edo Period (1603-1868) was a time when Japan was ruled by the Tokugawa shogunate, featuring a strong feudal system with samurai as the warrior class.',
            'category': 'history',
            'difficulty': 'medium',
            'culture': 'Japan',
            'image_url': '/static/images/edo-period.jpg'
        },
        
        # Art
        {
            'question_text': 'What is the traditional paper-cutting art of China called?',
            'options': '["Origami", "Jianzhi", "Calligraphy", "Ikebana"]',
            'correct_answer': 'Jianzhi',
            'explanation': 'Jianzhi is the art of Chinese paper cutting that dates back to the 6th century. These intricate designs often feature animals, plants, and scenes from daily life.',
            'category': 'art',
            'difficulty': 'hard',
            'culture': 'China',
            'image_url': '/static/images/jianzhi.jpg'
        },
        {
            'question_text': 'Which artistic technique involves decorated eggs and is a tradition in Ukraine?',
            'options': '["Batik", "Pysanka", "Marquetry", "Cloisonné"]',
            'correct_answer': 'Pysanka',
            'explanation': 'Pysanka involves creating intricate designs on eggs using a wax-resist method. These decorated eggs are an important part of Ukrainian Easter traditions.',
            'category': 'art',
            'difficulty': 'hard',
            'culture': 'Ukraine',
            'image_url': '/static/images/pysanka.jpg'
        },
        
        # Food
        {
            'question_text': 'Which spice is essential to authentic Indian curry and gives it a yellow color?',
            'options': '["Cardamom", "Cumin", "Turmeric", "Coriander"]',
            'correct_answer': 'Turmeric',
            'explanation': 'Turmeric is a bright yellow spice essential in Indian cooking. It not only gives curry its distinctive color but also has anti-inflammatory properties.',
            'category': 'food',
            'difficulty': 'easy',
            'culture': 'India',
            'image_url': '/static/images/turmeric.jpg'
        },
        {
            'question_text': 'What is the national dish of Brazil?',
            'options': '["Paella", "Feijoada", "Empanadas", "Ceviche"]',
            'correct_answer': 'Feijoada',
            'explanation': 'Feijoada is a hearty black bean stew with various pork cuts. It originated during the colonial period and is now considered Brazil\'s national dish.',
            'category': 'food',
            'difficulty': 'medium',
            'culture': 'Brazil',
            'image_url': '/static/images/feijoada.jpg'
        },
        
        # Traditions
        {
            'question_text': 'During which festival do people in India fly colorful kites?',
            'options': '["Diwali", "Holi", "Makar Sankranti", "Navratri"]',
            'correct_answer': 'Makar Sankranti',
            'explanation': 'Makar Sankranti, celebrated in January, marks the beginning of the harvest season. Flying kites is a major tradition during this festival across India.',
            'category': 'traditions',
            'difficulty': 'medium',
            'culture': 'India',
            'image_url': '/static/images/makar-sankranti.jpg'
        },
        {
            'question_text': 'What ritual occurs at midnight on December 31st in Spain involving grapes?',
            'options': '["Grape harvest", "Twelve Grapes", "Wine toasting", "Grape stomping"]',
            'correct_answer': 'Twelve Grapes',
            'explanation': 'In Spain, people eat 12 grapes at midnight on New Year\'s Eve, one with each bell strike. Each grape represents good luck for one month of the coming year.',
            'category': 'traditions',
            'difficulty': 'medium',
            'culture': 'Spain',
            'image_url': '/static/images/twelve-grapes.jpg'
        }
    ]
    
    # Check if questions already exist
    if Question.query.count() == 0:
        for q_data in sample_questions:
            question = Question(**q_data)
            db.session.add(question)
        
        db.session.commit()