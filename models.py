from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.String(50), nullable=False)  # מזהה כיתה
    date = db.Column(db.String(10), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(200))
    device_type = db.Column(db.String(50))
