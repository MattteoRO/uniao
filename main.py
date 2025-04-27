from app import app

if __name__ == "__main__":
    with app.app_context():
        from models import add_sample_questions
        from app import db
        db.create_all()
        add_sample_questions()
    app.run(host='0.0.0.0', port=5000, debug=True)