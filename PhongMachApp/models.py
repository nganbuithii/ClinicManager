from datetime import datetime
from sqlalchemy import Column, String, Integer, Enum, Float, ForeignKey, Date, DateTime
from sqlalchemy.orm import relationship
from PhongMachApp import db, app
from flask_login import UserMixin
from enum import Enum as UserEnum


class Basemodel(db.Model):
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)


class UserRole(UserEnum):
    CASHIER = 5
    DOCTOR = 4
    NURSE = 2
    ADMIN = 3
    USER = 1


class User(Basemodel, UserMixin):
    name = Column(String(50), nullable=False)
    email = Column(String(50), nullable=False, unique=True)
    password = Column(String(50), nullable=False)
    phone = Column(String(50), nullable=False, unique=True)
    avatar = Column(String(100))
    user_role = Column(Enum(UserRole), default=UserRole.USER)


class MedicineUnit(Basemodel):
    name = Column(String(30), unique=True, default='')
    medicines = relationship('Medicine', backref='medicine_unit', lazy=True)

    def __str__(self):
        return self.name


# Thuốc
class Medicine(Basemodel):
    name = Column(String(50), unique=True, default='', nullable=False)
    amount = Column(Integer, default=0)
    image = Column(String(255), nullable=True)
    import_date = Column(DateTime, default=datetime.now())
    expiration_date = Column(DateTime, default=datetime.now())
    component = Column(String(200), default='')
    price = Column(Integer, default=0.0)
    description = Column(String(1000), default='')
    # # foreign keys
    medicineUnit_id = Column(Integer, ForeignKey(MedicineUnit.id), nullable=False)  # khóa ngoại tới đơn vị thuốc
    prescriptions = relationship("Prescription", backref="related_medicine")

    def __str__(self):
        return self.name


class PromissoryNote(Basemodel):  # PHIẾU KHÁM
    __tablename__ = 'promissory_note'

    date = Column(Date, nullable=False)
    symptom = Column(String(100), nullable=False)  # Triệu chứng
    forecast = Column(String(100), nullable=False)  # chẩn đoán
    user_id = Column(Integer, ForeignKey('user.id'))  # id nhân viên
    user = relationship("User", backref="promissory_notes")
    CCCD = Column(String(50), nullable=False)

    appointment_id = Column(Integer, ForeignKey('appointment.id'))  # id lịch hẹn
    appointment = relationship("Appointment", backref="promissory_notes")

    prescriptions = relationship("Prescription", backref="promissory_note")  # đơn thuốc


class Prescription(db.Model):  # chi tiết phiếu thuốc
    __tablename__ = 'prescription'

    id = db.Column(db.Integer, primary_key=True)
    promissory_id = db.Column(db.Integer, db.ForeignKey('promissory_note.id'))
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicine.id'))
    quantity = db.Column(db.Integer)
    use_number = db.Column(db.Integer)
    usage_detail = db.Column(db.String(255))

    related_promissory_note = relationship("PromissoryNote", backref="related_prescriptions")
    medicine = db.relationship('Medicine')


class Appointment(Basemodel):  # LỊCH HẸN
    __tablename__ = 'appointment'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    cccd = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    sdt = db.Column(db.String(20), nullable=False)
    birthday = db.Column(db.Date, nullable=False)
    address = db.Column(db.String(255), nullable=False)
    calendar = db.Column(db.Date, nullable=False)
    medical_exam_lists = db.relationship('MedicalExamList',
                                         back_populates='appointment')  # Quan hệ với bảng MedicalExamList

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # Thêm khóa ngoại tới bảng User
    user = db.relationship('User', backref='appointments')  # Quan hệ với bảng User


# Danh sách khám gửi cho bác sĩ
class MedicalExamList(db.Model):  # Appointment list
    __tablename__ = 'medical_exam_list'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    list_code = db.Column(db.String(50), nullable=False)
    created_date = db.Column(db.Date, default=datetime.now().date())
    appointment_date = db.Column(db.Date)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # Khóa ngoại tới bảng User
    user = db.relationship('User', backref='medical_exam_lists')  # Quan hệ với bảng User
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'))  # Khóa ngoại mã cuộc hẹn
    appointment = db.relationship('Appointment', back_populates='medical_exam_lists')


# Hóa đơn
class Payment(Basemodel):
    __tablename__ = 'payment'

    promissory_note_id = db.Column(db.Integer, db.ForeignKey('promissory_note.id'))
    total_cost = db.Column(db.Float, nullable=False)
    paid_date = db.Column(db.DateTime, nullable=False)
    patient_id = Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    user = db.relationship("User", backref="payments")
    promissory_note = db.relationship('PromissoryNote', backref='payments')


# amin quy dinh
class Regulation(Basemodel):
    patient_quantity = Column(Integer, default=40)
    examination_fee = Column(Float, default=100000)

    def __str__(self):
        return self.name

    def is_patient_quantity_exceeded(self, list_code):
        # Lấy số lượng bệnh nhân đã đăng kí trong danh sách mới
        current_patient_count = MedicalExamList.query.filter_by(list_code=list_code).count()
        return current_patient_count >= self.patient_quantity


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
