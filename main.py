from flet import *
from flet import dropdown
from datetime import datetime
import qrcode
import json
import os
import webbrowser
import subprocess
import platform
import uuid
from pywhatkit import sendwhatmsg_instantly, sendwhats_image
import time

class StudentManagementApp:
    def __init__(self, page: Page):
        self.page = page
        self.page.title = "نظام إدارة الطلاب"
        self.page.window_width = 400
        self.page.window_height = 700
        self.page.window_resizable = False
        self.page.bgcolor = "#E3F2FD"

        # Colors
        self.primary_color = "#1976D2"
        self.secondary_color = "#64B5F6"
        self.accent_color = "#42A5F5"
        self.success_color = "#4CAF50"
        self.warning_color = "#FF9800"
        self.danger_color = "#F44336"

        # Data
        self.groups = {}
        self.students = {}
        self.load_data()

        # Reusable snackbar
        self.snackbar = SnackBar(content=Text("", color="white"), open=False)
        self.page.overlay.append(self.snackbar)

        self.login_screen(None)

    def load_data(self):
        if os.path.exists('data.json'):
            try:
                with open('data.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.groups = data.get('groups', {})
                    self.students = data.get('students', {})
            except Exception as e:
                self.show_snackbar(f"خطأ في تحميل البيانات: {e}")

    def save_data(self):
        data = {'groups': self.groups, 'students': self.students}
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def create_qr_code(self, student_id):
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(student_id)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        unique_id = str(uuid.uuid4())[:8]
        img_path = f'qr_{unique_id}.png'
        img.save(img_path)
        return img_path

    def _normalize_phone(self, phone: str) -> str:
        """تحويل الرقم إلى صيغة دولية صحيحة لمصر (+2XXXXXXXXXX)"""
        phone = phone.strip()
        # إزالة أي مسافات أو شرطات
        phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        # إذا كان يبدأ بـ "00" استبداله بـ "+"
        if phone.startswith('00'):
            phone = '+' + phone[2:]
        # إذا كان يبدأ بـ "+2" يبقى كما هو
        if phone.startswith('+2'):
            return phone
        # إذا كان يبدأ بـ "2" فقط (بدون +) أضف "+"
        if phone.startswith('2'):
            return '+' + phone
        # إذا كان يبدأ بصفر (رقم محلي) أضف "+2" واحذف الصفر
        if phone.startswith('0'):
            return '+2' + phone[0:]
        # خلاف ذلك (رقم بدون رمز دولي) أضف "+2"
        return '+2' + phone

    def send_qr_via_whatsapp_auto(self, phone, student_name, student_id, qr_path, group_name):
        try:
            if not os.path.exists(qr_path):
                self.show_snackbar('خطأ: صورة QR Code غير موجودة')
                return False

            now = datetime.now()
            date = now.strftime("%d/%m/%Y")

            message = f"""السلام عليكم ورحمة الله وبركاته 👋

أهلا وسهلا بك في نظام إدارة الطلاب MASA 🎓

📋 بيانات الطالب:
الاسم: {student_name}
المجموعة: {group_name}
معرف الطالب: {student_id}
التاريخ: {date}

📱 تم إنشاء رمز QR فريد لابنك
يرجى حفظ الصورة المرسلة في مكان آمن

مع تحيات
نظام MASA
محمد عبد الجواد"""

            # توحيد الرقم
            phone_normalized = self._normalize_phone(phone)

            # Send using pywhatkit
            try:
                self.show_snackbar('جاري إرسال QR Code... يرجى الانتظار')
                time.sleep(2)
                # Send text message first
                sendwhatmsg_instantly(phone_normalized, message, wait_time=10, tab_close=True)
                time.sleep(2)
                # Send image (requires pywhatkit >= 5.0)
                sendwhats_image(phone_normalized, qr_path, caption="QR Code الطالب", wait_time=10, tab_close=True)
                self.show_snackbar('✅ تم إرسال QR Code بنجاح!')
                return True
            except Exception as e:
                self.show_snackbar(f'⚠️ فشل الإرسال التلقائي: {str(e)[:50]}')
                # Fallback: open WhatsApp manually
                self._open_whatsapp_manual(phone_normalized, message, qr_path)
                return False
        except Exception as e:
            self.show_snackbar(f'خطأ: {str(e)}')
            return False

    def _open_whatsapp_manual(self, phone, message, qr_path):
        try:
            import urllib.parse
            encoded_msg = urllib.parse.quote(message)
            webbrowser.open(f"https://wa.me/{phone}?text={encoded_msg}")
            time.sleep(1)
            # Open image file (cross-platform)
            if os.path.exists(qr_path):
                if platform.system() == "Windows":
                    os.startfile(qr_path)
                elif platform.system() == "Darwin":
                    subprocess.Popen(['open', qr_path])
                else:
                    subprocess.Popen(['xdg-open', qr_path])
        except Exception as e:
            self.show_snackbar(f'فشل الفتح اليدوي: {e}')

    # ---------- UI Methods ----------
    def login_screen(self, e):
        self.page.clean()
        self.page.add(
            Container(
                width=400, height=700, bgcolor="#E3F2FD",
                content=Column([
                    Container(height=60),
                    Container(
                        content=Icon(name=Icons.SCHOOL, size=100, color=self.primary_color),
                        alignment=alignment.center
                    ),
                    Text("نظام إدارة الطلاب", size=32, color=self.primary_color, weight='bold', text_align=TextAlign.CENTER),
                    Text("MASA", size=28, color=self.secondary_color, italic=True, text_align=TextAlign.CENTER, weight='bold'),
                    Container(height=60),
                    FilledButton(
                        text='🧑‍🏫 دخول المعلم', width=300, on_click=self.main_screen,
                        style=ButtonStyle(bgcolor={MaterialState.DEFAULT: self.secondary_color}, color={MaterialState.DEFAULT: "white"})
                    ),
                    Container(height=15),
                    FilledButton(
                        text='👨‍💼 دخول الإدارة', width=300, on_click=self.admin_screen,
                        style=ButtonStyle(bgcolor={MaterialState.DEFAULT: self.accent_color}, color={MaterialState.DEFAULT: "white"})
                    ),
                    Container(expand=True),
                ],
                alignment=MainAxisAlignment.START,
                horizontal_alignment=CrossAxisAlignment.CENTER,
                spacing=5)
            )
        )
        self.page.update()

    def main_screen(self, e):
        self.page.clean()
        self.page.add(
            Container(
                width=400, height=700, bgcolor="#E3F2FD",
                padding=15,
                content=Column([
                    Container(
                        content=Text("لوحة التحكم", size=28, color="white", weight='bold'),
                        bgcolor=self.primary_color, padding=15, border_radius=10
                    ),
                    Container(height=40),
                    FilledButton(
                        text='📚 إدارة المجموعات', width=320, height=50, on_click=self.manage_groups_screen,
                        style=ButtonStyle(bgcolor={MaterialState.DEFAULT: self.secondary_color}, color={MaterialState.DEFAULT: "white"})
                    ),
                    Container(height=12),
                    FilledButton(
                        text='✅ تسجيل الحضور', width=320, height=50, on_click=self.attendance_screen,
                        style=ButtonStyle(bgcolor={MaterialState.DEFAULT: self.success_color}, color={MaterialState.DEFAULT: "white"})
                    ),
                    Container(height=12),
                    FilledButton(
                        text='👥 عرض الطلاب', width=320, height=50, on_click=self.view_students_screen,
                        style=ButtonStyle(bgcolor={MaterialState.DEFAULT: self.accent_color}, color={MaterialState.DEFAULT: "white"})
                    ),
                    Container(height=12),
                    FilledButton(
                        text='🔙 الرجوع', width=320, height=50, on_click=self.login_screen,
                        style=ButtonStyle(bgcolor={MaterialState.DEFAULT: self.danger_color}, color={MaterialState.DEFAULT: "white"})
                    ),
                    Container(expand=True),
                ],
                alignment=MainAxisAlignment.START,
                horizontal_alignment=CrossAxisAlignment.CENTER,
                spacing=0)
            )
        )
        self.page.update()

    def manage_groups_screen(self, e):
        self.page.clean()
        group_name_field = TextField(label='اسم المجموعة', width=300, bgcolor="white", border_radius=8)

        def add_group(e):
            if group_name_field.value:
                group_name = group_name_field.value.strip()
                if group_name not in self.groups:
                    self.groups[group_name] = []
                    self.save_data()
                    group_name_field.value = ''
                    self.manage_groups_screen(None)
                else:
                    self.show_snackbar('المجموعة موجودة بالفعل')
            else:
                self.show_snackbar('أدخل اسم المجموعة')

        groups_list = Column()
        for group_name in self.groups:
            groups_list.controls.append(
                Container(
                    content=Row([
                        Text(f'📁 {group_name}', size=16, color='white', weight='bold'),
                        Container(expand=True),
                        IconButton(icon=Icons.DELETE, icon_color='white', on_click=lambda e, g=group_name: self.delete_group(g)),
                        IconButton(icon=Icons.EDIT, icon_color='white', on_click=lambda e, g=group_name: self.add_student_to_group(g))
                    ]),
                    padding=12, border_radius=8, bgcolor=self.accent_color
                )
            )

        self.page.add(
            Container(
                bgcolor="#E3F2FD",
                padding=15,
                content=Column([
                    Container(
                        content=Text("إدارة المجموعات", size=28, color="white", weight='bold'),
                        bgcolor=self.primary_color, padding=15, border_radius=10
                    ),
                    Container(height=20),
                    group_name_field,
                    Container(height=10),
                    FilledButton(
                        text='➕ إنشاء مجموعة', width=300, on_click=add_group,
                        style=ButtonStyle(bgcolor={MaterialState.DEFAULT: self.success_color})
                    ),
                    Container(height=20),
                    Text("المجموعات الموجودة:", size=16, color=self.primary_color, weight='bold'),
                    Container(height=10),
                    groups_list,
                    Container(height=15),
                    FilledButton(
                        text='🔙 رجوع', width=300, on_click=self.main_screen,
                        style=ButtonStyle(bgcolor={MaterialState.DEFAULT: self.danger_color})
                    )
                ], scroll='auto', spacing=0)
            )
        )
        self.page.update()

    def add_student_to_group(self, group_name):
        self.page.clean()
        student_name = TextField(label='اسم الطالب', width=300, bgcolor="white", border_radius=8)
        parent_phone = TextField(label='رقم تليفون ولي الأمر', width=300, hint_text='مثال: 01001234567', bgcolor="white", border_radius=8)
        parent_name = TextField(label='اسم ولي الأمر', width=300, bgcolor="white", border_radius=8)

        def add_student(e):
            if student_name.value and parent_phone.value and parent_name.value:
                phone = parent_phone.value.strip()
                # التحقق من صحة الرقم بعد التطبيع
                normalized = self._normalize_phone(phone)
                if len(normalized) < 12 or not normalized.startswith('+2'):
                    self.show_snackbar('رقم الهاتف غير صحيح')
                    return

                student_id = f"{group_name}_{len(self.groups[group_name]) + 1}"
                qr_path = self.create_qr_code(student_id)

                student_data = {
                    'name': student_name.value,
                    'parent_phone': parent_phone.value,  # نحتفظ بالرقم الأصلي
                    'parent_name': parent_name.value,
                    'group': group_name,
                    'qr_code': qr_path,
                    'student_id': student_id,
                    'qr_sent': False
                }

                self.students[student_id] = student_data
                self.groups[group_name].append(student_id)
                self.save_data()

                # Send QR via WhatsApp
                success = self.send_qr_via_whatsapp_auto(
                    parent_phone.value,  # نمرر الرقم الأصلي (سيتم تطبيعه داخل الدالة)
                    student_name.value,
                    student_id,
                    qr_path,
                    group_name
                )

                student_data['qr_sent'] = success
                self.save_data()

                self.show_snackbar('✅ تم إضافة الطالب')
                self.manage_groups_screen(None)
            else:
                self.show_snackbar('أدخل جميع البيانات')

        self.page.add(
            Container(
                bgcolor="#E3F2FD",
                padding=15,
                content=Column([
                    Container(
                        content=Text(f"➕ إضافة طالب", size=24, color="white", weight='bold'),
                        bgcolor=self.primary_color, padding=15, border_radius=10
                    ),
                    Container(height=20),
                    Text(f"المجموعة: {group_name}", size=14, color=self.primary_color, weight='bold'),
                    Container(height=15),
                    student_name,
                    Container(height=10),
                    parent_name,
                    Container(height=10),
                    parent_phone,
                    Container(height=15),
                    Text("⚠️ تأكد من أن WhatsApp Desktop مثبت وقيد التشغيل", size=11, color=self.warning_color, italic=True),
                    Container(height=20),
                    FilledButton(
                        text='✅ إضافة الطالب', width=300, on_click=add_student,
                        style=ButtonStyle(bgcolor={MaterialState.DEFAULT: self.success_color})
                    ),
                    Container(height=12),
                    FilledButton(
                        text='🔙 رجوع', width=300, on_click=self.manage_groups_screen,
                        style=ButtonStyle(bgcolor={MaterialState.DEFAULT: self.danger_color})
                    )
                ], scroll='auto', spacing=0)
            )
        )
        self.page.update()

    def delete_group(self, group_name):
        if group_name in self.groups:
            for student_id in self.groups[group_name]:
                if student_id in self.students:
                    qr_path = self.students[student_id].get('qr_code')
                    if qr_path and os.path.exists(qr_path):
                        try:
                            os.remove(qr_path)
                        except:
                            pass
                    del self.students[student_id]
            del self.groups[group_name]
            self.save_data()
            self.manage_groups_screen(None)

    def delete_student(self, student_id):
        if student_id in self.students:
            student = self.students[student_id]
            group_name = student['group']
            if group_name in self.groups and student_id in self.groups[group_name]:
                self.groups[group_name].remove(student_id)
            del self.students[student_id]
            qr_path = student.get('qr_code')
            if qr_path and os.path.exists(qr_path):
                try:
                    os.remove(qr_path)
                except:
                    pass
            self.save_data()
            self.show_snackbar(f'تم حذف الطالب: {student["name"]}')
            self.view_students_screen(None)

    def attendance_screen(self, e):
        self.page.clean()
        groups_dropdown = Dropdown(
            label='اختر المجموعة', width=300,
            options=[dropdown.Option(group) for group in self.groups.keys()],
            bgcolor="white"
        )
        students_list = Column()

        def load_students(e):
            students_list.controls.clear()
            if groups_dropdown.value and groups_dropdown.value in self.groups:
                for student_id in self.groups[groups_dropdown.value]:
                    student = self.students[student_id]
                    def mark_attendance(e, sid=student_id):
                        self.send_attendance_whatsapp_message(sid)
                    def delete_std(e, sid=student_id):
                        self.delete_student(sid)
                    students_list.controls.append(
                        Container(
                            content=Row([
                                Column([
                                    Text(f'👤 {student["name"]}', size=14, color='white', weight='bold'),
                                    Text(f'👨‍👩‍👧 {student["parent_name"]}', size=12, color='white'),
                                ]),
                                Container(expand=True),
                                IconButton(icon=Icons.QR_CODE, icon_color='white', tooltip='عرض QR Code',
                                           on_click=lambda e, s=student: self.show_qr_code(s)),
                                FilledButton(text='✅', width=50, on_click=mark_attendance,
                                             style=ButtonStyle(bgcolor={MaterialState.DEFAULT: self.success_color})),
                                IconButton(icon=Icons.DELETE, icon_color='white', tooltip='حذف الطالب', on_click=delete_std)
                            ]),
                            padding=12, border_radius=8, bgcolor=self.accent_color
                        )
                    )
            self.page.update()

        groups_dropdown.on_change = load_students

        self.page.add(
            Container(
                bgcolor="#E3F2FD",
                padding=15,
                content=Column([
                    Container(
                        content=Text("✅ تسجيل الحضور", size=28, color="white", weight='bold'),
                        bgcolor=self.primary_color, padding=15, border_radius=10
                    ),
                    Container(height=20),
                    groups_dropdown,
                    Container(height=15),
                    Text("الطلاب:", size=16, color=self.primary_color, weight='bold'),
                    Container(height=10),
                    students_list,
                    Container(height=12),
                    FilledButton(
                        text='🔙 رجوع', width=300, on_click=self.main_screen,
                        style=ButtonStyle(bgcolor={MaterialState.DEFAULT: self.danger_color})
                    )
                ], scroll='auto', spacing=0)
            )
        )
        self.page.update()

    def send_attendance_whatsapp_message(self, student_id):
        student = self.students[student_id]
        now = datetime.now()
        date_time = now.strftime("%d/%m/%Y")
        time_str = now.strftime("%H:%M:%S")
        message = f"""السلام عليكم ورحمة الله وبركاته

تم تسجيل حضور الطالب: {student['name']}

التاريخ : {date_time}
الوقت : {time_str}
مستر : محمد عبد الجواد"""
        phone = student['parent_phone']
        # توحيد الرقم
        phone_normalized = self._normalize_phone(phone)
        import urllib.parse
        encoded_message = urllib.parse.quote(message)
        webbrowser.open(f"https://wa.me/{phone_normalized}?text={encoded_message}")
        self.show_snackbar('تم فتح WhatsApp')

    def show_qr_code(self, student):
        dlg = AlertDialog(
            title=Text(f"🔲 QR Code - {student['name']}"),
            content=Image(src=student['qr_code'], width=300, height=300, fit=ImageFit.CONTAIN),
            actions=[TextButton("✅ إغلاق", on_click=lambda e: self.close_dlg(dlg))]
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def close_dlg(self, dlg):
        dlg.open = False
        self.page.update()

    def view_students_screen(self, e):
        self.page.clean()
        students_list = Column()
        for student_id, student in self.students.items():
            def delete_std(e, sid=student_id):
                self.delete_student(sid)
            qr_status = "✅ تم الإرسال" if student.get('qr_sent') else "⏳ لم يتم الإرسال"
            qr_color = self.success_color if student.get('qr_sent') else self.warning_color
            students_list.controls.append(
                Container(
                    content=Row([
                        Column([
                            Text(f'👤 {student["name"]}', size=14, color='white', weight='bold'),
                            Text(f'👨‍👩‍👧 {student["parent_name"]}', size=12, color='white'),
                            Text(f'📱 {student["parent_phone"]}', size=11, color='white'),
                            Text(f'📚 {student["group"]}', size=11, color='white'),
                            Text(f'📤 {qr_status}', size=10, color=qr_color, weight='bold'),
                        ]),
                        Container(expand=True),
                        IconButton(icon=Icons.DELETE, icon_color='white', tooltip='حذف الطالب', on_click=delete_std)
                    ]),
                    padding=12, border_radius=8, bgcolor=self.accent_color
                )
            )
        self.page.add(
            Container(
                bgcolor="#E3F2FD",
                padding=15,
                content=Column([
                    Container(
                        content=Text("👥 عرض الطلاب", size=28, color="white", weight='bold'),
                        bgcolor=self.primary_color, padding=15, border_radius=10
                    ),
                    Container(height=20),
                    students_list,
                    Container(height=12),
                    FilledButton(
                        text='🔙 رجوع', width=300, on_click=self.main_screen,
                        style=ButtonStyle(bgcolor={MaterialState.DEFAULT: self.danger_color})
                    )
                ], scroll='auto', spacing=0)
            )
        )
        self.page.update()

    def admin_screen(self, e):
        self.page.clean()
        self.page.add(
            Container(
                bgcolor="#E3F2FD",
                padding=15,
                content=Column([
                    Container(
                        content=Text("👨‍💼 لوحة الإدارة", size=28, color="white", weight='bold'),
                        bgcolor=self.primary_color, padding=15, border_radius=10
                    ),
                    Container(height=60),
                    FilledButton(
                        text='📊 إحصائيات الطلاب', width=320, height=50, on_click=self.statistics_screen,
                        style=ButtonStyle(bgcolor={MaterialState.DEFAULT: self.secondary_color})
                    ),
                    Container(height=12),
                    FilledButton(
                        text='💾 تصدير البيانات', width=320, height=50, on_click=self.export_data,
                        style=ButtonStyle(bgcolor={MaterialState.DEFAULT: self.accent_color})
                    ),
                    Container(height=12),
                    FilledButton(
                        text='🔙 الرجوع', width=320, height=50, on_click=self.login_screen,
                        style=ButtonStyle(bgcolor={MaterialState.DEFAULT: self.danger_color})
                    ),
                    Container(expand=True),
                ], scroll='auto', spacing=0)
            )
        )
        self.page.update()

    def statistics_screen(self, e):
        self.page.clean()
        total_students = len(self.students)
        total_groups = len(self.groups)
        qr_sent_count = sum(1 for s in self.students.values() if s.get('qr_sent', False))

        self.page.add(
            Container(
                bgcolor="#E3F2FD",
                padding=15,
                content=Column([
                    Container(
                        content=Text("📊 إحصائيات الطلاب", size=28, color="white", weight='bold'),
                        bgcolor=self.primary_color, padding=15, border_radius=10
                    ),
                    Container(height=40),
                    Container(
                        content=Column([
                            Row([
                                Icon(Icons.PEOPLE, size=40, color=self.secondary_color),
                                Column([
                                    Text("إجمالي الطلاب", size=14, color=self.primary_color),
                                    Text(str(total_students), size=28, color=self.primary_color, weight='bold')
                                ])
                            ]),
                            Container(height=20),
                            Row([
                                Icon(Icons.FOLDER, size=40, color=self.accent_color),
                                Column([
                                    Text("إجمالي المجموعات", size=14, color=self.primary_color),
                                    Text(str(total_groups), size=28, color=self.primary_color, weight='bold')
                                ])
                            ]),
                            Container(height=20),
                            Row([
                                Icon(Icons.CHECK_CIRCLE, size=40, color=self.success_color),
                                Column([
                                    Text("تم إرسال QR Code", size=14, color=self.primary_color),
                                    Text(f"{qr_sent_count}/{total_students}", size=28, color=self.primary_color, weight='bold')
                                ])
                            ])
                        ]),
                        padding=20, bgcolor="white", border_radius=10
                    ),
                    Container(expand=True),
                    FilledButton(
                        text='🔙 رجوع', width=300, on_click=self.admin_screen,
                        style=ButtonStyle(bgcolor={MaterialState.DEFAULT: self.danger_color})
                    )
                ], spacing=0)
            )
        )
        self.page.update()

    def export_data(self, e):
        self.show_snackbar('✅ تم حفظ البيانات بنجاح في data.json')

    def show_snackbar(self, message):
        self.snackbar.content = Text(message, color="white")
        self.snackbar.open = True
        self.page.update()

def main(page: Page):
    StudentManagementApp(page)

if __name__ == "__main__":
    app(main)
