from models import db, Attendance
from datetime import datetime, time
import pytz
from flask import jsonify
from collections import defaultdict
from datetime import datetime



class AttendanceSystem:
    def __init__(self):
        self.CUTOFF_HOUR = time(9, 25)
        self.israel_tz = pytz.timezone('Asia/Jerusalem')
        self.CLASSES = {
            'A': [
                "מנחם מענדל אייזנבך",
                "משה כהן",
                "חגי טובין",
                "אור זלינגר",
                "אוראל דוידוב",
                "יצחק דמן",
                "משה גבריאל טאלר",
                "דן חמד",
                "יהונתן בן עמי",
                "אליהו גלעד יומטוביאן",
                "אשר וסרמן",
                "מנשרש יעקב",
                "סטון אלחנן מאיר",
                "פישר דניאל גבע",
                "פישר אלי",
                "פרנקרייך יצחק",
                "צירקוס שניאור זלמן",
                "קופרמן מנחם מנדל",
                "קליר נתנאל",
                "רבינוביץ אלעזר",
                "ריזה ישראל",
                "שבדרון חיים",
                "שובר אריה"
                ],
            'B': [
                "ירוחם מנדלסון",
                "הערשי שור",
                "שלומי היימליך",
                "יונתן רוזנפלד",
                "הרשי רוזנפלד",
                "אלעזר מתן",
                "בצלאל שטרן",
                "דוב צוקר",
                "מוטי קופשיץ",
                "יעקב מתן",
                "שלומי וינד",
                "שלמה הופמן",
                "ישראל בינונסקי",
                "דוד טייכמן",
                "יקיר אוזן",
                "תולי ברגר",
                "שמואל בלאו",
                "אריאל בן פזי",
                "יוסי בן חיים",
                "שלומי נוישטאט",
                "נחמן בר אור",
                "ינון גואטה",
                "יואל אידר",
                "שמריהו זלמנוב"
                ]
        }

    def after_cutoff(self):
        now = datetime.now(self.israel_tz)
        return now.hour >= self.CUTOFF_HOUR

    def get_real_ip(self, request):
        x_forwarded_for = request.headers.get('X-Forwarded-For')
        return x_forwarded_for.split(',')[0].strip() if x_forwarded_for else request.remote_addr

    def update_attendance(self, name, status, ip_address, user_agent, class_id):
        if class_id not in self.CLASSES:
            return {'error': 'כיתה לא קיימת'}, 404
        if self.after_cutoff():
            return {'error': 'עבר הזמן!'}, 403
        if not name or not status:
            return {'error': 'שדות חסרים'}, 400
        if name not in self.CLASSES[class_id]:
            return {'error': 'שם לא חוקי'}, 400

        now = datetime.now(self.israel_tz)
        today = now.strftime('%Y-%m-%d')
        device_type = self.detect_device_type(user_agent)

        record = Attendance.query.filter_by(date=today, name=name, class_id=class_id).first()

        if record:
            record.status = status
            record.timestamp = now
            record.ip_address = ip_address
            record.user_agent = user_agent
            record.device_type = device_type
        else:
            db.session.add(Attendance(
                class_id=class_id,
                date=today,
                name=name,
                status=status,
                ip_address=ip_address,
                user_agent=user_agent,
                device_type=device_type,
                timestamp=now
            ))

        db.session.commit()
        return {'success': True}, 200

    def detect_device_type(self, user_agent):
        ua = user_agent.lower() if user_agent else ''
        if 'android' in ua:
            return 'Mobile (Android)'
        elif 'iphone' in ua:
            return 'Mobile (iPhone)'
        elif 'ipad' in ua:
            return 'Tablet (iPad)'
        elif 'mobile' in ua:
            return 'Mobile'
        elif 'tablet' in ua:
            return 'Tablet'
        elif 'windows' in ua:
            return 'Desktop (Windows)'
        elif 'macintosh' in ua:
            return 'Desktop (Mac)'
        elif 'linux' in ua:
            return 'Desktop (Linux)'
        return 'Unknown'

    def get_soldiers(self, class_id):
        if class_id not in self.CLASSES:
            return []
        today = datetime.now().strftime('%Y-%m-%d')
        records = Attendance.query.filter_by(date=today, class_id=class_id).all()
        reported_names = [r.name for r in records]
        return [name for name in self.CLASSES[class_id] if name not in reported_names]

    def get_attendance_details(self, class_id):
        if class_id not in self.CLASSES:
            return []

        today = datetime.now().strftime('%Y-%m-%d')
        records = Attendance.query.filter_by(date=today, class_id=class_id).all()
        records_dict = {record.name: record for record in records}

        details = []
        for soldier in self.CLASSES[class_id]:
            if soldier in records_dict:
                record = records_dict[soldier]
                details.append({
                    'name': soldier,
                    'status': record.status,
                    'timestamp': record.timestamp.isoformat() if record.timestamp else None,
                    'ip_address': record.ip_address,
                    'device_type': record.device_type,
                    'reported': True
                })
            else:
                details.append({
                    'name': soldier,
                    'status': 'לא נוכח',
                    'timestamp': None,
                    'ip_address': None,
                    'device_type': None,
                    'reported': False
                })
        return details
    
    def attendance_stats(self):

        # קבלת כל הרשומות מה-attendance כדי למצוא את כל התלמידים הייחודיים
        all_attendance = Attendance.query.all()
        
        # יצירת רשימת תלמידים ייחודיים מהרשומות הקיימות
        student_names = {record.name for record in all_attendance}
        
        # קבלת נוכחות להיום
        today = datetime.now().strftime('%Y-%m-%d')
        today_attendance = Attendance.query.filter_by(date=today).all()
        
        # חישוב סטטיסטיקות
        present = set()
        absent = set()
        late = set()
        
        for record in today_attendance:
            if record.status == 'present':
                present.add(record.name)
            elif record.status == 'absent':
                absent.add(record.name)
            elif record.status == 'late':
                late.add(record.name)
        
        # חישוב מי לא נוכח (לא מופיע כלל במערכת היום)
        not_recorded = student_names - (present | absent | late)
        
        # סטטיסטיקה לפי כיתה
        class_stats = defaultdict(lambda: {
            'present': 0,
            'absent': 0,
            'late': 0,
            'not_recorded': 0,
            'total': 0
        })
        
        # עדכון הסטטיסטיקה לפי כיתה
        for record in all_attendance:
            if record.name in student_names:  # רק תלמידים ייחודיים
                class_stats[record.class_id]['total'] += 1
                student_names.discard(record.name)  # מונע ספירה כפולה
                
                if record.date == today:
                    if record.status == 'present':
                        class_stats[record.class_id]['present'] += 1
                    elif record.status == 'absent':
                        class_stats[record.class_id]['absent'] += 1
                    elif record.status == 'late':
                        class_stats[record.class_id]['late'] += 1
                    # לא מעדכנים not_recorded כאן כי זה רק עבור היום
        
        # עדכון not_recorded עבור היום
        for record in all_attendance:
            if record.name in not_recorded and record.date == today:
                class_stats[record.class_id]['not_recorded'] += 1
        
        return jsonify({
            'date': today,
            'totals': {
                'present': len(present),
                'absent': len(absent),
                'late': len(late),
                'not_recorded': len(not_recorded),
                'total_students': len(student_names)
            },
            'by_class': class_stats,
            'not_recorded_students': list(not_recorded)
        })
