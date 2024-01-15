# Tuơng tác với csdl
from datetime import datetime
from datetime import date
from flask import request, flash
from flask import session
from sqlalchemy import func, extract

from PhongMachApp import app, db, sms
from PhongMachApp.models import User, Medicine, MedicineUnit, Appointment, MedicalExamList, Prescription, \
    PromissoryNote, Payment
import vonage
# Băm mật khẩu
import hashlib


def add_user(name, email, password, phone, **kwargs):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    user = User(name=name.strip(),
                email=email.strip(),
                phone=phone.strip(),
                password=password,
                avatar=kwargs.get('avatar'))
    db.session.add(user)
    db.session.commit()


def add_lich_kham(name, cccd, gender, sdt, birthday, address, calendar,user_id):
    # birthday = datetime.strptime(birthday, '%d-%m-%Y').date()
    # calendar = datetime.strptime(calendar, '%d-%m-%Y').date()
    datLichKham = Appointment(
        name=name.strip(),
        cccd=cccd.strip(),
        gender=gender.strip(),
        sdt=sdt.strip(),
        birthday=birthday,
        address=address.strip(),
        calendar=calendar,
        user_id=user_id)
    db.session.add(datLichKham)
    db.session.commit()

def check_login(email, password):
    if email and password:
        password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
        return User.query.filter(User.email.__eq__(email.strip()),
                                 User.password.__eq__(password)).first()

def get_prev_url():
    referer = request.headers.get('Referer')

    if referer and referer != request.url:
        return referer
    else:
        return '/'

def load_medicineUnit():
    return MedicineUnit.query.all()


def load_medicine(kw=None, page=1):
    medicines_query = Medicine.query
    if kw:
        medicines_query = medicines_query.filter(Medicine.name.contains(kw))

    page_size = app.config['PAGE_SIZE']
    start = (page - 1) * page_size
    end = start + page_size
    medicines = medicines_query.slice(start, end).all()
    return medicines

def count_medicine():
    return Medicine.query.count()

def get_email(user_email, ):
    return User.query.filter_by(email=user_email).first()

def get_user_by_id(user_id):
    return User.query.get(user_id)

def get_medicine_by_id(medicine_id):
    return Medicine.query.get(medicine_id)

def count_cart(cart):
    total_quantity = 0
    total_amount = 0
    if cart:
        for c in cart.values():
            total_quantity += c.get('quantity', 0)
    return {
        'total_quantity': total_quantity
    }

# y tas
def get_patient_phone_number(patient_id):
    patient = Appointment.query.get(patient_id)
    if patient:
        return patient.sdt
    return None

def get_patient_date(patient_id):
    patient = Appointment.query.get(patient_id)
    if patient:
        return patient.calendar
    return None

def format_date(input_date):
    # Chuyển đổi ngày từ chuỗi "YYYY-MM-DD" sang đối tượng datetime
    formatted_date = datetime.strptime(input_date, "%Y-%m-%d")

    # Định dạng lại ngày thành "Ngày tháng Năm"
    result_date = formatted_date.strftime("%d-%m-%Y")
    return result_date

def get_patient_name(patient_id):
    patient = Appointment.query.filter_by(id=patient_id).first()
    return patient.name if patient else None

# lấy danh sách khám theo ngày
def get_medical_exams_by_date(target_date):
    medical_exams = MedicalExamList.query.join(Appointment, MedicalExamList.appointment_id == Appointment.id).filter(
        Appointment.calendar == target_date).all()
    return medical_exams

def get_medical_exam_by_cccd(cccd):
    # Tìm kiếm cuộc hẹn dựa trên CCCD
    medical_exam = Appointment.query.filter_by(cccd=cccd).first()
    return medical_exam

def get_patient_info(appointment_id):
    appointment = Appointment.query.filter_by(id=appointment_id).first()
    if appointment:
        return {'name': appointment.name, 'appointment_date': appointment.calendar, 'CCCD': appointment.cccd}
    return {'name': None, 'appointment_date': None, 'CCCD': None}


def get_unit_name_by_id(unit_id):
    unit = MedicineUnit.query.filter_by(id=unit_id).first()
    if unit:
        return unit.name
    return None


# thống kê, báo cáo
def medicines_stats(kw):
    m = db.session.query(Medicine.id, Medicine.name, func.sum(Prescription.quantity), func.sum(Prescription.use_number)) \
        .join(Prescription, Prescription.medicine_id.__eq__(Medicine.id)) \
        .group_by(Medicine.id, Medicine.name)

    if kw:
        m = m.filter(Medicine.name.contains(kw))

    return m.all()


def medical_stats(year):
    medi = db.session.query(
        func.extract('month', PromissoryNote.date),
        func.count(PromissoryNote.id),
    ).group_by(func.extract('month', PromissoryNote.date)).order_by(extract('month', PromissoryNote.date))

    if year:
        medi = medi.filter(func.extract('year', PromissoryNote.date) == year)
    return medi.all()


def revenue_stats(year):
    reve = db.session.query(func.extract('month', Payment.paid_date), func.sum(Payment.total_cost), ).group_by(
        func.extract('month', Payment.paid_date)).order_by(extract('month', Payment.paid_date))

    if year:
        reve = reve.filter(func.extract('year', Payment.paid_date) == year)
    else:
        reve.all()
    return reve.all()

    # def is_patient_quantity_exceeded(list_code, patient_quantity):
    #     # Lấy số lượng bệnh nhân đã đăng kí trong danh sách mới
    #     current_patient_count = MedicalExamList.query.filter_by(list_code=list_code).count()
    #     return current_patient_count >= patient_quantity


def create_appointment(appointment_info):
    list_code = appointment_info.get('list_code')
    medical_exam_list = MedicalExamList.query.filter_by(list_code=list_code).first()

    if medical_exam_list.is_patient_quantity_exceeded():
        # Hiển thị thông báo không thể đăng ký cuộc hẹn do đủ số lượng bệnh nhân
        return flash(f"Không thể đăng ký cuộc hẹn vì đã đủ số lượng bệnh nhân trong danh sách khám này.")


def is_patient_quantity_exceeded(list_code, patient_quantity):
    # Lấy số lượng bệnh nhân đã đăng kí trong danh sách mới
    current_patient_count = MedicalExamList.query.filter_by(list_code=list_code).count()
    return current_patient_count >= patient_quantity
