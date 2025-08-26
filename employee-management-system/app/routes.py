from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from .models import BillingRecord, BillingAdjustment
from app.models import Employee, User, Attendance, Project, WorkReport, LeaveRequest, Message, CalendarEvent, db
from datetime import datetime

main = Blueprint('main', __name__)

@main.route('/')
def welcome():
    active_employees = Employee.query.filter_by(is_active=True).all()
    return render_template('welcome.html', employees=active_employees)

@main.route('/employee/<int:employee_id>')
def employee_dashboard(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    # Check if the employee is currently clocked in
    latest_attendance = Attendance.query.filter_by(employee_id=employee.id).order_by(Attendance.clock_in_time.desc()).first()
    is_clocked_in = latest_attendance and latest_attendance.clock_out_time is None
    
    # Get assigned projects for the employee (assuming a many-to-many relationship or a simple assignment for now)
    # For now, let's assume all active projects are available to all employees for work reporting
    assigned_projects = Project.query.filter_by(is_active=True).all()

    return render_template('employee_dashboard.html',
                           employee=employee,
                           is_clocked_in=is_clocked_in,
                           projects=assigned_projects)

@main.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('main.admin_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('main.admin_dashboard'))
        else:
            flash('Invalid username or password')
    return render_template('admin_login.html')

@main.route('/admin/dashboard')
@login_required
def admin_dashboard():
    total_active_employees = Employee.query.filter_by(is_active=True).count()
    pending_leave_requests = LeaveRequest.query.filter_by(status='Pending').count()
    active_projects = Project.query.filter_by(is_active=True).count()
    
    today = datetime.utcnow().date()
    clocked_in_today = Attendance.query.filter(
        db.func.date(Attendance.clock_in_time) == today,
        Attendance.clock_out_time == None
    ).count()

    return render_template('admin_dashboard.html',
                           total_active_employees=total_active_employees,
                           pending_leave_requests=pending_leave_requests,
                           active_projects=active_projects,
                           clocked_in_today=clocked_in_today)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.welcome'))

@main.route('/api/attendance/clock_in', methods=['POST'])
def clock_in():
    employee_id = request.json.get('employee_id')
    if not employee_id:
        return jsonify({'status': 'error', 'message': 'Employee ID is required'}), 400

    attendance = Attendance(employee_id=employee_id, clock_in_time=datetime.utcnow())
    db.session.add(attendance)
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Clocked in successfully'})

@main.route('/api/attendance/clock_out', methods=['POST'])
def clock_out():
    employee_id = request.json.get('employee_id')
    if not employee_id:
        return jsonify({'status': 'error', 'message': 'Employee ID is required'}), 400

    latest_attendance = Attendance.query.filter_by(employee_id=employee_id, clock_out_time=None).order_by(Attendance.clock_in_time.desc()).first()

    if latest_attendance:
        latest_attendance.clock_out_time = datetime.utcnow()
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Clocked out successfully'})
    else:
        return jsonify({'status': 'error', 'message': 'No active clock-in found'}), 400

@main.route('/api/attendance/status/<int:employee_id>', methods=['GET'])
def attendance_status(employee_id):
    latest_attendance = Attendance.query.filter_by(employee_id=employee_id).order_by(Attendance.clock_in_time.desc()).first()

    if latest_attendance and latest_attendance.clock_out_time is None:
        return jsonify({'status': 'Clocked In'})
    else:
        return jsonify({'status': 'Clocked Out'})

@main.route('/admin/attendance')
@login_required
def view_attendance():
    employees = Employee.query.filter_by(is_active=True).all()
    attendance_data = []
    for employee in employees:
        latest_attendance = Attendance.query.filter_by(employee_id=employee.id).order_by(Attendance.clock_in_time.desc()).first()
        status = 'Clocked Out'
        clock_in = None
        if latest_attendance and latest_attendance.clock_out_time is None:
            status = 'Clocked In'
            clock_in = latest_attendance.clock_in_time
        attendance_data.append({
            'employee_name': f"{employee.first_name} {employee.last_name}",
            'status': status,
            'clock_in_time': clock_in
        })
    return render_template('admin_attendance.html', attendance_data=attendance_data)

@main.route('/admin/projects')
@login_required
def manage_projects():
    projects = Project.query.all()
    return render_template('admin_projects.html', projects=projects)

@main.route('/admin/projects/add', methods=['POST'])
@login_required
def add_project():
    name = request.form.get('name')
    description = request.form.get('description')
    billing_method = request.form.get('billing_method')
    is_active = 'is_active' in request.form

    if not name or not billing_method:
        flash('Project name and billing method are required.', 'danger')
        return redirect(url_for('main.manage_projects'))
    
    @main.route('/employee/<int:employee_id>/work_report', methods=['GET', 'POST'])
    def submit_work_report(employee_id):
        employee = Employee.query.get_or_404(employee_id)
        projects = Project.query.filter_by(is_active=True).all()
    
        if request.method == 'POST':
            project_id = request.form.get('project_id')
            description = request.form.get('description')
            hours_worked = request.form.get('hours_worked')
            units_completed = request.form.get('units_completed')
    
            project = Project.query.get(project_id)
            if not project:
                flash('Invalid project selected.', 'danger')
                return redirect(url_for('main.submit_work_report', employee_id=employee.id))
    
            if project.billing_method == 'Hourly' and not hours_worked:
                flash('Hours worked is required for hourly projects.', 'danger')
                return redirect(url_for('main.submit_work_report', employee_id=employee.id))
            elif project.billing_method == 'Count-Based' and not units_completed:
                flash('Units completed is required for count-based projects.', 'danger')
                return redirect(url_for('main.submit_work_report', employee_id=employee.id))
    
            work_report = WorkReport(
                employee_id=employee.id,
                project_id=project.id,
                description=description,
                hours_worked=float(hours_worked) if hours_worked else None,
                units_completed=int(units_completed) if units_completed else None
            )
            db.session.add(work_report)
            db.session.commit()
            flash('Work report submitted successfully!', 'success')
            return redirect(url_for('main.employee_dashboard', employee_id=employee.id))
    
        return render_template('employee_work_report.html', employee=employee, projects=projects)
    
    @main.route('/admin/work_reports', methods=['GET'])
    @login_required
    def view_work_reports():
        employees = Employee.query.all()
        projects = Project.query.all()
    
        employee_id = request.args.get('employee_id', type=int)
        project_id = request.args.get('project_id', type=int)
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
    
        query = WorkReport.query.join(Employee).join(Project)
    
        if employee_id:
            query = query.filter(WorkReport.employee_id == employee_id)
        if project_id:
            query = query.filter(WorkReport.project_id == project_id)
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            query = query.filter(WorkReport.date >= start_date)
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            query = query.filter(WorkReport.date <= end_date)
    
        work_reports = query.order_by(WorkReport.date.desc()).all()
    
        return render_template('admin_work_reports.html',
                               work_reports=work_reports,
                               employees=employees,
                               projects=projects)
    
    @main.route('/employee/<int:employee_id>/leave_request', methods=['GET', 'POST'])
    def submit_leave_request(employee_id):
        employee = Employee.query.get_or_404(employee_id)
    
        if request.method == 'POST':
            start_date_str = request.form.get('start_date')
            end_date_str = request.form.get('end_date')
            leave_type = request.form.get('leave_type')
    
            if not start_date_str or not end_date_str or not leave_type:
                flash('All fields are required for leave request.', 'danger')
                return redirect(url_for('main.submit_leave_request', employee_id=employee.id))
    
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    
            if start_date > end_date:
                flash('Start date cannot be after end date.', 'danger')
                return redirect(url_for('main.submit_leave_request', employee_id=employee.id))
    
            leave_request = LeaveRequest(
                employee_id=employee.id,
                start_date=start_date,
                end_date=end_date,
                leave_type=leave_type,
                status='Pending'
            )
            db.session.add(leave_request)
            db.session.commit()
            flash('Leave request submitted successfully!', 'success')
            return redirect(url_for('main.employee_dashboard', employee_id=employee.id))
    
        return render_template('employee_leave_request.html', employee=employee)
    
    @main.route('/admin/leave_requests')
    @login_required
    def manage_leave_requests():
        leave_requests = LeaveRequest.query.join(Employee).order_by(LeaveRequest.request_date.desc()).all()
        return render_template('admin_leave_requests.html', leave_requests=leave_requests)
    
    @main.route('/admin/leave_requests/approve/<int:request_id>', methods=['POST'])
    @login_required
    def approve_leave_request(request_id):
        leave_request = LeaveRequest.query.get_or_404(request_id)
        leave_request.status = 'Approved'
        db.session.commit()
        flash('Leave request approved.', 'success')
        return redirect(url_for('main.manage_leave_requests'))
    
    @main.route('/admin/leave_requests/reject/<int:request_id>', methods=['POST'])
    @login_required
    def reject_leave_request(request_id):
        leave_request = LeaveRequest.query.get_or_404(request_id)
        leave_request.status = 'Rejected'
        db.session.commit()
        flash('Leave request rejected.', 'danger')
        return redirect(url_for('main.manage_leave_requests'))

@main.route('/messages', methods=['GET', 'POST'])
@login_required
def messages():
    if request.method == 'POST':
        recipient_id = request.form.get('recipient_id')
        is_recipient_admin = request.form.get('is_recipient_admin') == 'true'
        subject = request.form.get('subject')
        body = request.form.get('body')
        attachment = request.files.get('attachment')

        sender_id = current_user.id
        is_sender_admin = True # Assuming only admins can send messages for now

        attachment_path = None
        if attachment:
            # Save attachment to a secure location and store its path
            # For simplicity, let's just store the filename for now
            attachment_path = attachment.filename

        message = Message(
            sender_id=sender_id,
            recipient_id=recipient_id if recipient_id else None,
            is_sender_admin=is_sender_admin,
            is_recipient_admin=is_recipient_admin if recipient_id else None,
            subject=subject,
            body=body,
            attachment_path=attachment_path
        )
        db.session.add(message)
        db.session.commit()
        flash('Message sent successfully!', 'success')
        return redirect(url_for('main.messages'))

    # For displaying messages
    # Admin can see all messages, employees only messages to/from them
    if current_user.is_authenticated: # Assuming current_user is an Admin
        sent_messages = Message.query.filter_by(sender_id=current_user.id, is_sender_admin=True).order_by(Message.timestamp.desc()).all()
        received_messages = Message.query.filter(
            (Message.recipient_id == current_user.id and Message.is_recipient_admin == True) |
            (Message.recipient_id == None) # Broadcast messages
        ).order_by(Message.timestamp.desc()).all()
    else: # Employee
        # This part needs to be adjusted based on how employees are logged in and identified
        # For now, let's assume employee_id is available in session or through a different login
        employee_id = 1 # Placeholder for employee ID
        sent_messages = Message.query.filter_by(sender_id=employee_id, is_sender_admin=False).order_by(Message.timestamp.desc()).all()
        received_messages = Message.query.filter(
            (Message.recipient_id == employee_id and Message.is_recipient_admin == False) |
            (Message.recipient_id == None) # Broadcast messages
        ).order_by(Message.timestamp.desc()).all()

    users = User.query.all()
    employees = Employee.query.all()
    return render_template('messages.html', sent_messages=sent_messages, received_messages=received_messages, users=users, employees=employees)

@main.route('/admin/calendar', methods=['GET', 'POST'])
@login_required
def manage_calendar_events():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        event_type = request.form.get('event_type')

        if not title or not start_date_str or not end_date_str or not event_type:
            flash('All fields are required for a calendar event.', 'danger')
            return redirect(url_for('main.manage_calendar_events'))

        start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%dT%H:%M')

        event = CalendarEvent(
            title=title,
            description=description,
            start_date=start_date,
            end_date=end_date,
            event_type=event_type,
            created_by=current_user.id
        )
        db.session.add(event)
        db.session.commit()
        flash('Calendar event added successfully!', 'success')
        return redirect(url_for('main.manage_calendar_events'))

    events = CalendarEvent.query.order_by(CalendarEvent.start_date.asc()).all()
    return render_template('admin_calendar.html', events=events)

@main.route('/admin/calendar/edit/<int:event_id>', methods=['GET', 'POST'])
@login_required
def edit_calendar_event(event_id):
    event = CalendarEvent.query.get_or_404(event_id)
    if request.method == 'POST':
        event.title = request.form.get('title')
        event.description = request.form.get('description')
        event.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%dT%H:%M')
        event.end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%dT%H:%M')
        event.event_type = request.form.get('event_type')
        db.session.commit()
        flash('Calendar event updated successfully!', 'success')
        return redirect(url_for('main.manage_calendar_events'))
    return render_template('admin_edit_calendar_event.html', event=event)

@main.route('/admin/calendar/delete/<int:event_id>', methods=['POST'])
@login_required
def delete_calendar_event(event_id):
    event = CalendarEvent.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    flash('Calendar event deleted successfully!', 'success')
    return redirect(url_for('main.manage_calendar_events'))

    new_project = Project(name=name, description=description, billing_method=billing_method, is_active=is_active)
    db.session.add(new_project)
    db.session.commit()
    flash('Project added successfully!', 'success')
    return redirect(url_for('main.manage_projects'))

@main.route('/admin/projects/edit/<int:project_id>', methods=['POST'])
@login_required
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)
    project.name = request.form.get('name')
    project.description = request.form.get('description')
    project.billing_method = request.form.get('billing_method')
    project.is_active = 'is_active' in request.form
    db.session.commit()
    flash('Project updated successfully!', 'success')
    return redirect(url_for('main.manage_projects'))

@main.route('/admin/projects/delete/<int:project_id>', methods=['POST'])
@login_required
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    flash('Project deleted successfully!', 'success')
    return redirect(url_for('main.manage_projects'))

@main.route('/admin/billing_records', methods=['GET', 'POST'])
@login_required
def manage_billing_records():
    if request.method == 'POST':
        project_id = request.form.get('project_id')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')

        if not project_id or not start_date_str or not end_date_str:
            flash('Project, start date, and end date are required for billing record generation.', 'danger')
            return redirect(url_for('main.manage_billing_records'))

        project = Project.query.get_or_404(project_id)
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

        work_reports = WorkReport.query.filter(
            WorkReport.project_id == project.id,
            WorkReport.date >= start_date,
            WorkReport.date <= end_date
        ).all()

        # Group work reports by employee
        employee_work = {}
        for report in work_reports:
            if report.employee_id not in employee_work:
                employee_work[report.employee_id] = {'hours': 0, 'units': 0}
            employee_work[report.employee_id]['hours'] += (report.hours_worked if report.hours_worked else 0)
            employee_work[report.employee_id]['units'] += (report.units_completed if report.units_completed else 0)

        for employee_id, data in employee_work.items():
            amount = 0
            if project.billing_method == 'Hourly':
                # Assuming a fixed hourly rate for now, or it could be stored in Employee/Project model
                hourly_rate = 50 # Example rate
                amount = data['hours'] * hourly_rate
                billing_record = BillingRecord(
                    project_id=project.id,
                    employee_id=employee_id,
                    start_date=start_date,
                    end_date=end_date,
                    hours_billed=data['hours'],
                    units_billed=None,
                    amount=amount
                )
            elif project.billing_method == 'Count-Based':
                # Assuming a fixed unit rate for now
                unit_rate = 5 # Example rate
                amount = data['units'] * unit_rate
                billing_record = BillingRecord(
                    project_id=project.id,
                    employee_id=employee_id,
                    start_date=start_date,
                    end_date=end_date,
                    hours_billed=None,
                    units_billed=data['units'],
                    amount=amount
                )
            db.session.add(billing_record)
        db.session.commit()
        flash('Billing records generated successfully!', 'success')
        return redirect(url_for('main.manage_billing_records'))

    projects = Project.query.all()
    billing_records = BillingRecord.query.join(Project).join(Employee).order_by(BillingRecord.generated_date.desc()).all()
    return render_template('admin_billing_records.html', projects=projects, billing_records=billing_records)

@main.route('/admin/billing_records/adjust/<int:record_id>', methods=['GET', 'POST'])
@login_required
def adjust_billing_record(record_id):
    billing_record = BillingRecord.query.get_or_404(record_id)
    if request.method == 'POST':
        adjustment_amount = float(request.form.get('adjustment_amount'))
        reason = request.form.get('reason')

        if not adjustment_amount:
            flash('Adjustment amount is required.', 'danger')
            return redirect(url_for('main.adjust_billing_record', record_id=record_id))

        # Apply adjustment to the billing record's amount
        billing_record.amount += adjustment_amount
        
        adjustment = BillingAdjustment(
            billing_record_id=billing_record.id,
            admin_id=current_user.id,
            adjustment_amount=adjustment_amount,
            reason=reason
        )
        db.session.add(adjustment)
        db.session.commit()
        flash('Billing record adjusted successfully!', 'success')
        return redirect(url_for('main.manage_billing_records'))
    
    return render_template('admin_adjust_billing.html', billing_record=billing_record)