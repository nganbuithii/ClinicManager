from datetime import datetime

from flask_admin import Admin, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from PhongMachApp import app, db
from flask_login import current_user, logout_user
from flask_admin.contrib.sqla import ModelView
from PhongMachApp.models import (User, MedicineUnit, Medicine, Regulation, UserRole)
from flask import redirect, request

admin = Admin(app=app, name='PhongMach Administration', template_mode='bootstrap4')


class AdminView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN


class AdminBaseView(BaseView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN


class MedicineUnitView(AdminView):
    create_modal = True
    column_list = ['name', 'medicines']


class MedicineView(AdminView):
    create_modal = True
    can_view_details = True
    column_searchable_list = ['name']


class UserView(AdminView):
    create_modal = True
    column_list = ['name', 'email', 'password', 'user_role']


class ChangeRegulationView(AdminView):
    create_modal = True
    column_list = ['patient_quantity', 'examination_fee']


class ReportStatistics(AdminBaseView):
    @expose('/')
    def index(self):
        year = request.args.get('year', datetime.now().year)
        kw = request.args.get('kw')
        from PhongMachApp import utils

        medicine_stats = utils.medicines_stats(kw=kw)
        medicine_message = 'Không có dữ liệu, vui lòng nhập lại' if not medicine_stats else None

        medical_stats = utils.medical_stats(year=year)
        revenue_stats = utils.revenue_stats(year=year)

        medical_message = 'Không có dữ liệu, vui lòng nhập lại' if not medical_stats else None

        return self.render('/admin/report_statistics.html', medicine_chart=medicine_stats,
                           medical_chart=medical_stats, revenue_chart=revenue_stats, medicine_message=medicine_message,
                           medical_message=medical_message)


class LogoutView(BaseView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect('/admin')

    def is_accessible(self):
        return current_user.is_authenticated


admin.add_view(UserView(User, db.session, name='Người dùng'))
admin.add_view(MedicineUnitView(MedicineUnit, db.session, name='Đơn vị thuốc'))
admin.add_view(MedicineView(Medicine, db.session, name='Thuốc'))
admin.add_view(ChangeRegulationView(Regulation, db.session, name='Thay đổi quy định'))
admin.add_view(ReportStatistics(name='Thống kê báo cáo'))
admin.add_view(LogoutView(name='Đăng xuất'))
