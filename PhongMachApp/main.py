import math, re
from twilio.rest import Client
import cloudinary.uploader
from flask import render_template, request, redirect, url_for, session, jsonify, flash
from flask_login import login_user, logout_user
from sqlalchemy import func

from PhongMachApp.models import UserRole, Payment
from datetime import datetime, date
from PhongMachApp import app, utils, login, models, db
from PhongMachApp.models import UserRole, MedicalExamList, Appointment, Prescription, PromissoryNote, Regulation
from flask import make_response

app.secret_key = 'Caichyrua11@'


@app.route("/")
def index():
    kwmedi = request.args.get('keywordmedi')
    page = request.args.get('page', 1)
    medis = utils.load_medicine(kw=kwmedi, page=int(page))
    countmedi = utils.count_medicine()

    return render_template('index.html', medicines=medis, current_page='index',
                           pages=math.ceil(countmedi / app.config['PAGE_SIZE']))


# Thuoc, danh muc thuoc
@app.route('/medicines/<int:medicine_id>')
def medicine_detail(medicine_id):
    medicine = utils.get_medicine_by_id(medicine_id)
    return render_template('medicine_detail.html', medicine=medicine)


# kiem tra dinh dang email
def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None


@app.route('/register', methods=['get', 'post'])
def user_register():
    err_msg = ""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        avatar_path = None

        if password.strip() == confirm.strip():

            # Check if email is in a valid format
            if not is_valid_email(email):
                err_msg = "Định dạng email không hợp lệ."
            else:
                # Check if the email is already registered
                if utils.get_email(email):
                    err_msg = "Email đã được đăng ký. Vui lòng chọn email khác."
                else:
                    avatar = request.files.get('avatar')
                    if avatar:
                        res = cloudinary.uploader.upload(avatar)
                        avatar_path = res['secure_url']
                    # Add the new user to the database
                    utils.add_user(name=name, email=email, password=password, phone=phone, avatar=avatar_path)
                    return redirect(url_for('user_login'))
        else:
            err_msg = "Mật khẩu và xác nhận mật khẩu không khớp."

    return render_template('register.html', err_msg=err_msg)


@app.route('/login', methods=['get', 'post'])
def user_login():
    err_msg = ""
    if request.method.__eq__('POST'):
        email = request.form.get('email')
        password = request.form.get('password')
        user = utils.check_login(email=email, password=password)

        if user:
            login_user(user=user)
            session['name'] = user.name
            session['user_role'] = user.user_role.value
            if user.user_role == UserRole.DOCTOR:
                return redirect('doctor/patient_list')
            elif user.user_role == UserRole.NURSE:
                return redirect('nurse/patient_list')
            elif user.user_role == UserRole.CASHIER:
                return redirect('cashier')
            elif user.user_role == UserRole.ADMIN:
                return redirect('admin')
            else:
                return redirect(url_for('index'))
        else:
            err_msg = "Email hoặc mật khẩu không chính xác."
    return render_template('login.html', err_msg=err_msg)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))


@login.user_loader
def user_load(user_id):
    return utils.get_user_by_id(user_id=user_id)


# xem profile và lưu hồ sơ khám bệnh
@app.route("/profile")
def profile():
    # def medical_history():
    if current_user.is_authenticated:
        user_id = current_user.id
        medical_records = (db.session.query(PromissoryNote)
                           .join(Appointment, PromissoryNote.appointment_id == Appointment.id)
                           .filter(Appointment.user_id == user_id)
                           .options(db.joinedload(PromissoryNote.prescriptions).joinedload(Prescription.medicine))
                           .all())

        return render_template('profile.html', medical_records=medical_records)
    return render_template('profile.html')


@app.route('/edit_profile', methods=['POST'])
def edit_profile():
    if request.method == 'POST':
        new_name = request.form['new_name']
        new_email = request.form['new_email']
        new_phone = request.form['new_phone']

        # Thực hiện tìm và cập nhật thông tin người dùng trong cơ sở dữ liệu
        user_id_to_update = current_user.id  # ID của người dùng cần cập nhật, đây chỉ là ví dụ
        user = User.query.get(user_id_to_update)

        if user:
            user.name = new_name
            user.email = new_email
            user.phone = new_phone

            db.session.commit()
            return jsonify(
                {'message': 'Thông tin đã được cập nhật thành công'})  # Trả về thông báo khi cập nhật thành công

        return jsonify({
            'message': 'Không tìm thấy người dùng để cập nhật'})  # Trả về thông báo khi không tìm thấy người dùng để cập nhật


@app.route("/datLichKham", methods=['get', 'post'])
def datLichKham():
    err_msg = ""
    err_msg1 = ""
    if request.method.__eq__('POST'):
        name = request.form.get('name')
        cccd = request.form.get('cccd')
        gender = request.form.get('optradio')
        sdt = request.form.get('sdt')
        birthday = request.form.get('birthday')
        address = request.form.get('address')
        calendar = request.form.get('calendar')

        try:
            existing_appointments_count = Appointment.query.filter_by(calendar=calendar).count()

            # Truy vấn giá trị patient_quantity từ bảng Regulation
            regulation = Regulation.query.first()
            max_appointments_allowed = regulation.patient_quantity

            if existing_appointments_count >= max_appointments_allowed:
                err_msg = "Lỗi đặt lịch! Đã đủ số lượng đăng kí khám"
            else:
                user_id = current_user.id
                utils.add_lich_kham(name=name, cccd=cccd, gender=gender, sdt=sdt, birthday=birthday, address=address,
                                    calendar=calendar, user_id=user_id)
                err_msg = "Đặt lịch khám thành công!"
        except Exception as e:
            print(e)
            err_msg = "Đã xảy ra lỗi khi đặt lịch!"
    return render_template('datLichKham.html', err_msg=err_msg, err_msg1=err_msg1, current_page='datLichKham')


# HIỂN THỊ DANH SÁCH Để bác sĩ lập phiếu khám
@app.route('/doctor/patient_list')
def doctor_patient_list():
    today = date.today()
    medical_exams = utils.get_medical_exams_by_date(today)#lấy danh sách khám ngày hôm nay
    # medical_exams=MedicalExamList.query.all() ##test
    appointment_ids = [note.appointment_id for note in PromissoryNote.query.all()]#check

    cccd = request.args.get('cccd')
    filtered_exams = None

    if cccd:
        filtered_exams = [exam for exam in medical_exams if exam.appointment.cccd == cccd]
        if not filtered_exams:
            flash('Không tìm thấy cuộc hẹn của số căn cước này!!!', 'danger')
    return render_template('doctor/patient_list.html', medical_exams=filtered_exams or medical_exams,
                           target_date=today, appointment_ids=appointment_ids)


# Lap phieu kham
@app.route('/examination_form/<int:appointment_id>')
def examination_form(appointment_id):
    kwmedi = request.args.get('keywordmedi')
    medis = utils.load_medicine(kw=kwmedi)
    patient_info = utils.get_patient_info(appointment_id)
    return render_template('doctor/PhieuKham.html', kw=kwmedi, medicines=medis, name=patient_info['name'],
                           calendar=patient_info['appointment_date'], CCCD=patient_info['CCCD'],
                           appointment_id=appointment_id)


# Thêm thuốc
@app.route('/api/add_medicine', methods=['put'])
def add_medicine():
    data = request.json
    id = str(data.get('id'))
    name = data.get('name')
    medicineUnit_id = data.get('medicineUnit_id')

    cart = session.get('cart')
    if not cart:
        cart = {}
    if id in cart:
        cart[id]['quantity'] += 1
    else:
        cart[id] = {
            'id': id,
            'name': name,
            'medicineUnit_id': medicineUnit_id,
            'medicine_unit_name': utils.get_unit_name_by_id(medicineUnit_id),
            'quantity': 1
        }
    session['cart'] = cart
    return jsonify(utils.count_cart(cart))


# Xóa thuốc
@app.route('/api/delete_cart/<medicine_id>', methods=['delete'])
def delete_cart(medicine_id):
    cart = session.get('cart')

    if cart and medicine_id in cart:
        del cart[medicine_id]
        session['cart'] = cart
    return jsonify(utils.count_cart(cart))


# LẬP PHIẾU KHÁM
@app.route('/create_prescription', methods=['POST'])
def create_prescription():
    if request.method == 'POST':
        if current_user.is_authenticated:
            user_id = current_user.get_id()

            appointment_id = request.form.get('appointment_id')
            date = request.form.get('date')
            symptom = request.form.get('symptom')
            forecast = request.form.get('forecast')
            CCCD = request.form.get('CCCD')
            new_prescription = PromissoryNote(
                date=date,
                symptom=symptom,
                forecast=forecast,
                appointment_id=appointment_id,
                user_id=user_id,
                CCCD=CCCD
            )

            db.session.add(new_prescription)
            db.session.commit()

            medicine_list = []  # Tạo danh sách Prescription để thêm vào session

            medicine_ids = request.form.getlist('id_medi')
            medicine_quantities = request.form.getlist('count_medi')
            usages = request.form.getlist('usage')

            for i in range(len(medicine_ids)):
                medicine = Medicine.query.get(medicine_ids[i])
                if medicine:
                    prescription = Prescription(
                        promissory_id=new_prescription.id,
                        medicine_id=medicine_ids[i],
                        quantity=medicine_quantities[i],
                        usage_detail=usages[i],
                        use_number=1
                    )
                    medicine_list.append(prescription)

            # Thêm tất cả các Prescription vào session cùng một lúc
            db.session.add_all(medicine_list)
            db.session.commit()

            # session['success'] = True
            session.pop('cart', None)
        flash(f'LẬP PHIẾU KHÁM THÀNH CÔNG!!!!', 'success')
        return redirect('/doctor/patient_list')


# lịch sử khám trong lập phiếu khám
@app.route('/fetch_medical_history', methods=['POST'])
def fetch_medical_history():
    cccd = request.form.get('cccd')
    # Truy vấn cơ sở dữ liệu để lấy lịch sử khám bệnh dựa trên CCCD
    medical_history = PromissoryNote.query.filter_by(CCCD=cccd).all()
    # Chuyển đổi kết quả thành dạng JSON và trả về cho frontend
    result = []
    for history in medical_history:
        result.append({
            'date': history.date,
            'symptom': history.symptom,
            'forecast': history.forecast
        })
    return jsonify(result)


# HIỂN THỊ DANH SÁCH BỆNH NHÂN ĐK
@app.route('/result', methods=['POST', 'GET'])
def add_patient():
    if request.method == 'POST':
        name = request.form['name']
        cccd = request.form['cccd']
        gender = request.form['optradio']
        sdt = request.form['sdt']
        birthday = request.form['birthday']
        address = request.form['address']
        calendar = request.form['calendar']

        try:
            user_id = current_user.id

            new_appointment = Appointment(
                name=name,
                cccd=cccd,
                gender=gender,
                sdt=sdt,
                birthday=birthday,
                address=address,
                calendar=calendar,
                user_id=user_id  # Thêm user_id vào lịch hẹn mới
            )

            # Kiểm tra số lượng lịch hẹn cho ngày đã chọn
            existing_appointments_count = Appointment.query.filter_by(calendar=calendar).count()

            # Truy vấn giá trị patient_quantity từ bảng Regulation
            regulation = Regulation.query.first()
            max_appointments_allowed = regulation.patient_quantity

            if existing_appointments_count >= max_appointments_allowed:
                flash('Đã đủ số lượng khám bệnh cho ngày này. Vui lòng chọn ngày khác.', 'danger')
                return redirect('/nurse/patient_list')

            # Thêm lịch hẹn mới vào cơ sở dữ liệu
            db.session.add(new_appointment)
            db.session.commit()
            flash('Thêm thông tin khám bệnh nhân thành công', 'success')
            return redirect('/nurse/patient_list')

        except Exception as e:
            print(e)
            flash('Đã xảy ra lỗi khi thêm thông tin khám bệnh nhân', 'danger')
            return redirect('/nurse/patient_list')


# hiển thị danh sách đăng kí khám
@app.route('/nurse/patient_list')
def show_result():
    appointments = Appointment.query.all()
    appointment_list = MedicalExamList.query.all()  # Danh sách đã lập
    filtered_appointments = [appointment for appointment in appointments if
                             appointment.id not in [item.appointment_id for item in appointment_list]]
    return render_template('nurse/patient_list.html', appointments=filtered_appointments)


# xóa bệnh nhân khỏi db
@app.route('/patients/<int:appointment_id>/delete', methods=['POST'])
def delete_patient(appointment_id):
    appointment = Appointment.query.get(appointment_id)
    db.session.delete(appointment)
    db.session.commit()
    appointments = Appointment.query.all()
    db.session.commit()
    flash('Xóa bệnh nhân thành công', 'success')
    return redirect('/nurse/patient_list')


# lọc bệnh nhân theo ngày khám
@app.route('/get_patients_by_date', methods=['GET'])
def get_patients_by_date():
    selected_date = request.args.get('ngayKham')

    # Danh sách bệnh nhân đã có trong MedicalExamList
    appointments_in_list = [medical_exam.appointment_id for medical_exam in
                            MedicalExamList.query.filter_by(appointment_date=selected_date).all()]

    # Lọc danh sách các bệnh nhân chưa có trong danh sách khám
    appointments = Appointment.query.filter_by(calendar=selected_date).all()
    # sau đó lấy các lịch hẹn có ngày kha trùng với ngày chọn lọc
    appointments_not_in_list = [appointment for appointment in appointments if
                                appointment.id not in appointments_in_list]

    appointment_count = len(appointments_not_in_list)

    if appointment_count == 0:
        flash('Không có bệnh nhân đăng ký lịch khám vào ngày này !!!', 'danger')
        return redirect('/nurse/patient_list')

    # Lưu danh sách bệnh nhân vào session
    session['selected_patients'] = [appointment.id for appointment in appointments_not_in_list]

    return render_template('nurse/patient_list_by_date.html', appointments=appointments_not_in_list,
                           appointment_count=appointment_count, selected_date=selected_date)


# lập danh sách khám
@app.route('/appointment_list', methods=['POST'])
def create_appointment_list():
    # Lấy danh sách bệnh nhân đã được chọn từ session
    selected_patients = session.get('selected_patients', [])
    # Lấy ID ca khám cuối cùng trong bảng MedicalExamList
    latest_count = db.session.query(func.max(MedicalExamList.list_code)).scalar() or 0
    new_count = int(latest_count) + 1
    list_code = new_count
    # Lấy ngày khám từ form
    appointment_date = request.form.get('appointment_date')
    if current_user.is_authenticated:
        user_id = current_user.get_id()
        if appointment_date:
            for patient_id in selected_patients:
                person = MedicalExamList(
                    list_code=list_code,
                    created_date=datetime.now().date(),
                    appointment_date=appointment_date,
                    user_id=user_id,
                    appointment_id=patient_id
                )
                db.session.add(person)
                # twilio gửi sms
                # account_sid = 'ACb81b7f5d8233ec77aa3f822f47965153'
                # auth_token = '85de982771f3a3bfc779e6f921ff2f6d'
                # client = Client(account_sid, auth_token)
                #
                # patient_phone_number = utils.get_patient_phone_number(patient_id)
                # patient_name = utils.get_patient_name(patient_id)
                # appointment_date = utils.get_patient_date(patient_id)
                # # format định dạng sdt +84
                # international_format = '+84' + patient_phone_number[1:]
                # message = client.messages.create(
                #     body=f'Đăng ký khám thành công, hẹn {patient_name} đến khám vào ngày {appointment_date} tại phòng khám HKN',
                #     from_='+12059273657',
                #     to=international_format
                # )

                # print(message.sid)
            db.session.commit()
            session.pop('selected_patients', None)

            # Hiển thị danh sách đã lập
            new_appointments = MedicalExamList.query.filter_by(appointment_date=appointment_date).all()
            return render_template('nurse/appointment_list.html', appointments=new_appointments,
                                   appointment_date=utils.format_date(appointment_date), appointment_code=list_code)
        return 'Lập danh sách không thành công'


#  thu ngân
@app.route("/cashier")
def cashier_home():
    all_notes = PromissoryNote.query.all()  # Truy vấn phiếu khám
    payment_status = {}   # Tạo một từ điển để theo dõi trạng thái thanh toán của từng phiếu khám

    cccd_query = request.args.get('cccd_query')  # Lấy thông tin tìm kiếm từ URL

    if cccd_query:
        # Nếu có thông tin tìm kiếm, lọc theo CCCD
        filtered_notes = PromissoryNote.query.filter_by(CCCD=cccd_query).all() #Lọc các phiếu khám theo CCCD nếu có.
        if not filtered_notes:
            flash(f"Không có phiếu khám nào cho CCCD: {cccd_query}", 'warning')
            return redirect(url_for('cashier_home'))

        # Kiểm tra trạng thái thanh toán của từng phiếu khám lọc được
        for note in filtered_notes:# Nếu không có phiếu khám nào được tìm thấy, thông báo và chuyển hướng về trang cashier_home.
            payment_exists = Payment.query.filter_by(promissory_note_id=note.id).first()#Kiểm tra xem có thanh toán nào liên quan đến phiếu khám hiện tại hay không.
            payment_status[note.appointment_id] = payment_exists is not None# Cập nhật trạng thái thanh toán trong từ điển. Nếu thanh toán tồn tại, giá trị là True, ngược lại là False
        return render_template('cashier/cashier_home.html', all_notes=filtered_notes, payment_status=payment_status)
    else:
    # Nếu không có thông tin tìm kiếm, hiển thị tất cả các phiếu khám
        for note in all_notes:# duyệt qua tất cả các phiếu kha
            payment_exists = Payment.query.filter_by(promissory_note_id=note.id).first()
            payment_status[note.appointment_id] = payment_exists is not None
        return render_template('cashier/cashier_home.html', all_notes=all_notes, payment_status=payment_status)


@app.route('/pay_info/<appointment_id>', methods=['GET'])
def pay_info(appointment_id):
    promissory_note = PromissoryNote.query.filter_by(appointment_id=appointment_id).first()
    patient_name = promissory_note.appointment.name
    exam_date = promissory_note.appointment.calendar

    # Lấy danh sách toa thuốc từ phiếu khám
    prescriptions = Prescription.query.filter_by(promissory_id=promissory_note.id).all()
    exam_fee = Regulation.query.first().examination_fee
    medicine_cost = sum(p.quantity * p.medicine.price for p in prescriptions)
    total_cost = exam_fee + medicine_cost

    # Khi thanh toán lưu về db payment
    promissory_note_id = promissory_note.id
    paid_date = date.today()
    patient_id = promissory_note.user_id
    nurse_id = current_user.id
    payment = Payment(promissory_note_id=promissory_note.id, total_cost=total_cost, patient_id=patient_id,
                      paid_date=paid_date, user_id=nurse_id)
    db.session.add(payment)
    db.session.commit()
    return render_template('cashier/pay_bill.html',
                           patient_name=patient_name,
                           exam_date=exam_date,
                           promissory_note_id=promissory_note_id,
                           paid_date=paid_date,
                           exam_fee=exam_fee,
                           medicine_cost=medicine_cost,
                           total_cost=total_cost)


# admin
@app.route('/admin/signin_admin', methods=['post'])
def signin_admin():
    email = request.form.get('email')
    password = request.form.get('password')

    user = utils.check_login(email=email, password=password)
    if user:
        login_user(user=user)
    else:
        flash('Đăng nhập không thành công. Vui lòng kiểm tra email và mật khẩu.', 'danger')
    return redirect(utils.get_prev_url())


####

if __name__ == '__main__':
    from PhongMachApp.admin import *

    app.run(debug=True, port=5000)
