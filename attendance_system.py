from models import db, Attendance
from datetime import datetime
import pytz



class AttendanceSystem:
    def __init__(self):
        self.CUTOFF_HOUR = 9  # שעה לאחר חצות
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
                "ירחם מנדלסון",
                "נחמן בן אור",
                "בצלאל שטרן",
                "יוסי בן חיים",
                "שמריהו זלמנוב",
                "יואל אידר",
                "יעקב מתן",
                "יקיר אוזן",
                "יונתן רוזנפלד",
                "ישראל בינונסקי",
                "שלמה הופמן",
                "ברוך צבי (הערשי) שור",
                "תולי ברגר",
                "מוטי קופשיץ",
                "אלעזר רוזן",
                "שמואל בלאו",
                "בן פזי",
                "דוב צוקר",
                "שלומי וינד",
                "שלומי ניישטאט",
                "יוסי רוזנפלד",
                "יצחק הילרמן",
                "יהודה גואטה",
                "דוד טייבמן",
                ],  

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
