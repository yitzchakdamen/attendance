from flask import Flask, request, jsonify, send_from_directory
from models import db
from attendance_system import AttendanceSystem
import os


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

attendance_system = AttendanceSystem()

with app.app_context():
    db.create_all()

@app.route('/')
def index2():
    return send_from_directory('', 'house.html')

@app.route('/presence/<class_id>')
def presence_page(class_id):
    filename = f'presence_{class_id}.html'
    if os.path.exists(filename):
        return send_from_directory('', filename)
    return f'כיתה {class_id} לא קיימת', 404

@app.route('/attendance/<class_id>', methods=['POST'])
def update_attendance(class_id):
    name = request.json.get('name')
    status = request.json.get('status')

    ip_address = attendance_system.get_real_ip(request)
    user_agent = request.headers.get('User-Agent')

    result, status_code = attendance_system.update_attendance(name, status, ip_address, user_agent, class_id)
    return jsonify(result), status_code

@app.route('/attendance/details/<class_id>', methods=['GET'])
def get_attendance_details(class_id):
    data = attendance_system.get_attendance_details(class_id)
    return jsonify(data)

@app.route('/names/<class_id>', methods=['GET'])
def get_names(class_id):
    return jsonify(attendance_system.get_soldiers(class_id))

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/In_development')
def In_development():
    return send_from_directory('', 'dev.html')

@app.route('/PresenceSending')
def PresenceSending():
    return send_from_directory('', 'Presence_Sending.html')




if __name__ == '__main__':
    app.run(debug=True)
