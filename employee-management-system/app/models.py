from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    department = db.Column(db.String(64), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    attendance = db.relationship('Attendance', backref='employee', lazy='dynamic')

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    clock_in_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    clock_out_time = db.Column(db.DateTime, nullable=True)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    billing_method = db.Column(db.String(64), nullable=False) # 'Hourly' or 'Count-Based'
    is_active = db.Column(db.Boolean, default=True)
    work_reports = db.relationship('WorkReport', backref='project', lazy='dynamic')

class WorkReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    hours_worked = db.Column(db.Float, nullable=True)
    units_completed = db.Column(db.Integer, nullable=True)
    description = db.Column(db.Text, nullable=True)

class LeaveRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    leave_type = db.Column(db.String(64), nullable=False)
    status = db.Column(db.String(64), default='Pending') # Pending, Approved, Rejected
    request_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    admin_notes = db.Column(db.Text, nullable=True)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, nullable=False) # Can be User.id or Employee.id
    recipient_id = db.Column(db.Integer, nullable=True) # Null for broadcast messages
    is_sender_admin = db.Column(db.Boolean, nullable=False) # True if sender is Admin (User), False if Employee
    is_recipient_admin = db.Column(db.Boolean, nullable=True) # True if recipient is Admin (User), False if Employee, Null for broadcast
    subject = db.Column(db.String(256), nullable=True)
    body = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    attachment_path = db.Column(db.String(256), nullable=True)

class CalendarEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=True)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    event_type = db.Column(db.String(64), nullable=False) # 'Company Event', 'Holiday', 'Leave'
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # Null for system-generated events (e.g., holidays)
    user = db.relationship('User', backref='calendar_events', lazy=True)

class BillingRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    hours_billed = db.Column(db.Float, nullable=True)
    units_billed = db.Column(db.Integer, nullable=True)
    amount = db.Column(db.Float, nullable=False)
    generated_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    project = db.relationship('Project', backref='billing_records', lazy=True)
    employee = db.relationship('Employee', backref='billing_records', lazy=True)

class BillingAdjustment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    billing_record_id = db.Column(db.Integer, db.ForeignKey('billing_record.id'), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    adjustment_amount = db.Column(db.Float, nullable=False)
    reason = db.Column(db.Text, nullable=True)
    adjustment_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    billing_record = db.relationship('BillingRecord', backref='adjustments', lazy=True)
    admin = db.relationship('User', backref='billing_adjustments', lazy=True)