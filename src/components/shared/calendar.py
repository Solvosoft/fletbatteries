import flet as ft
import datetime
from datetime import timezone
import uuid
from data.models import calendar_event
from data.manager.calendar_event_manager import EventManager
from components.shared.draggableModal import DraggableModal
import re

# ---------------------------
# Cabecera del calendario
# ---------------------------
class CalendarHeader(ft.Column):
    def __init__(self, today, week_days, on_day_change=None):
        super().__init__()
        self.today = today
        self.week_days = week_days
        self.day_selected = today
        self.on_day_change = on_day_change
        self.spacing = 0
        self.controls = [self.build_row()]

    def build_row(self):
        return ft.Row(
            spacing=0,
            controls=[
                ft.Container(width=80, height=100,
                    border=ft.border.only(
                        top=ft.BorderSide(0.2, ft.Colors.GREY_400),
                        right=ft.BorderSide(0.2, ft.Colors.GREY_400),
                        bottom=ft.BorderSide(0.2, ft.Colors.GREY_400)
                    ),
                ),
                *[
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(
                                    day.strftime("%a"),
                                    size=11,
                                    weight=ft.FontWeight.W_700,
                                    color="red" if day == self.today else "blue" if day == self.day_selected else "black",
                                ),
                                ft.Container(
                                    content=ft.Text(
                                        day.strftime("%d"),
                                        size=21,
                                        color="White" if day == self.day_selected else "red" if day == self.today else "black",
                                    ),
                                    alignment=ft.alignment.center,
                                    height=50,
                                    width=50,
                                    border_radius=100,
                                    bgcolor="blue" if self.day_selected == day else None,
                                    on_click=lambda e, d=day: self.change_day(d),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=4,
                        ),
                        border=ft.border.only(
                            top=ft.BorderSide(0.2, ft.Colors.GREY_400),
                            bottom=ft.BorderSide(0.2, ft.Colors.GREY_400)
                        ),
                        expand=True,
                        height=100,
                    )
                    for day in self.week_days
                ],
            ],
        )

    def change_day(self, day):
        self.day_selected = day
        self.controls[0] = self.build_row()
        self.update()

    def update_week(self, week_days):
        self.week_days = week_days
        self.controls[0] = self.build_row()
        self.update()

# ---------------------------
# Grilla del calendario
# ---------------------------
class CalendarGrid(ft.Column):
    def __init__(self, week_days, events, hour_height=60, open_edit_event=None, new_event=None):
        super().__init__(scroll=ft.ScrollMode.AUTO, expand=True, spacing=0)
        self.week_days = week_days
        self.events = events
        self.hour_height = hour_height
        self.open_edit_event = open_edit_event
        self.new_event = new_event
        self.build_grid()

    def build_grid(self):
        self.controls = []

        def format_hour(h: int) -> str:
            # Se le da formato 12 horas
            t = datetime.time(h, 0)
            formatted = t.strftime("%I %p").lstrip("0")  
            return formatted.lower().replace("am", "a.m.").replace("pm", "p.m.")

        # Columna de horas
        hour_column = ft.Column(
            controls=[
            ft.Container(
                content=ft.Text(format_hour(h)),
                height=self.hour_height,
                alignment=ft.alignment.top_center
            ) for h in range(24)
            ],
            spacing=0
        )
        # Fila principal: primera columna horas + días
        main_row = ft.Row(expand=True, spacing=0)
        main_row.controls.append(ft.Container(width=80, content=hour_column))

        # Columnas de días
        for day in self.week_days:
            day_stack = ft.Stack(height=self.hour_height * 24, expand=True, controls=[])

            # Celdas de fondo
            for h in range(24):
                day_stack.controls.append(
                    ft.Container(
                        top=h*self.hour_height,
                        left=0,
                        right=0,
                        height=self.hour_height,
                        border=ft.border.all(0.2, ft.Colors.GREY_400),
                        on_click=lambda e, d=day, hr=h: self.new_event(day=d, hour=f"{hr:02d}:00") if self.new_event else None,
                        on_hover= self.on_hover
                    )
                )       
            # Eventos del día
            day_events = [ev for ev in self.events if  ev.start_time.date() == day]
            for ev in day_events:
                start_minutes = ev.start_time.hour * 60 + ev.start_time.minute
                end_minutes = ev.end_time.hour * 60 + ev.end_time.minute
                duration = max(1, end_minutes - start_minutes)
                #altura minima de 25 para eventos muy cortos
                if duration < 25:
                    duration = 25

                day_stack.controls.append(
                    ft.Container(
                        top=self.hour_height * start_minutes / 60,
                        left=0,
                        right=5,
                         height=self.hour_height * duration / 60,
                        bgcolor=ev.color,
                        alignment=ft.alignment.center,
                        content=ft.Text(ev.title, size=10, color="white"),
                        on_click=lambda e, ev=ev: self.open_edit_event(ev) if self.open_edit_event else None  
                    )
                )
            main_row.controls.append(ft.Container(content=day_stack, expand=1))

        self.controls.append(main_row)

    def render_events(self, events, week_days):
        self.events = events
        self.week_days = week_days
        self.build_grid()
        self.update()
    
    def on_hover(self, e: ft.HoverEvent):
        if e.data == "true":
            e.control.bgcolor = ft.Colors.LIGHT_BLUE_50
        else:
            e.control.bgcolor = None
        e.control.update()

    
# ---------------------------
# Formulario de crear/editar
# ---------------------------
class FormCalendar(ft.Column):
    def __init__(self, save_event, close_callback, event=None, delete_event=None, day=None, hour=None):
        super().__init__(expand=True, tight=True, spacing=10)
        self.save_event = save_event
        self.delete_event = delete_event
        self.close_callback = close_callback
        self.event = event
        self.day = day
        self.hour = hour

        # valores iniciales 
        if self.event:
            self.fechaInicio = self.event.start_time.strftime("%d/%m/%Y")
            self.horaInicio = self.event.start_time.strftime("%I:%M %p").lstrip("0")
            self.fechaFin = self.event.end_time.strftime("%d/%m/%Y")
            self.horaFin = self.event.end_time.strftime("%I:%M %p").lstrip("0")
            self.NombreEvento = self.event.title or "Evento"
            self.descripcion = self.event.description or ""
            self.ubicacion = self.event.location or ""
            self.color = self.event.color or ft.Colors.BLUE_400
        else:
            hoy = datetime.date.today()
            self.fechaInicio = (self.day.strftime("%d/%m/%Y") if isinstance(self.day, datetime.date) else hoy.strftime("%d/%m/%Y"))
            self.horaInicio = (datetime.time(int(self.hour.split(":")[0]), 0).strftime("%I:%M %p").lstrip("0") if self.hour else datetime.datetime.now().strftime("%I:%M %p").lstrip("0"))
            self.fechaFin = self.fechaInicio
            try:
                hh = datetime.datetime.strptime(self.horaInicio, "%I:%M %p")
                if hh.hour >= 23:
                    self.horaFin = "11:59 PM"
                else:
                    self.horaFin = (hh + datetime.timedelta(hours=1)).strftime("%I:%M %p").lstrip("0")
            except Exception:
                self.horaFin = (datetime.datetime.now() + datetime.timedelta(hours=1)).strftime("%I:%M %p").lstrip("0")
            self.NombreEvento = "Nuevo evento"
            self.descripcion = ""
            self.ubicacion = ""
            self.color = ft.Colors.BLUE_400

        # referencias a controles
        self.tf_nombre = None
        self.tf_fechaInicio = None
        self.dd_horaInicio = None
        self.tf_fechaFin = None
        self.dd_horaFin = None
        self.header = None
        self.delete_button = None
        self.build_form()

    def get_time_options(self, is_fechaInicio=True):
        options = []
        if is_fechaInicio:
            for h in range(24):
                value = f"{h:02d}:00"
                label = datetime.time(h, 0).strftime("%I:%M %p").lstrip("0")
                options.append(ft.dropdownm2.Option(text=label, key=value))
        else:
            #opciones de hora fin a partir de hora inicio
            #convertir hora inicio a formato 24 horas
            if self.horaInicio:
             try:
                 start_hour = int(datetime.datetime.strptime(self.horaInicio, "%I:%M %p").strftime("%H"))
             except ValueError:
                 start_hour = int(datetime.datetime.strptime(self.horaInicio, "%H:%M").strftime("%H"))
            else:
                 start_hour = 0
            for h in range(start_hour , 24):
                value = f"{h%24:02d}:00"
                label = datetime.time(h%24, 0).strftime("%I:%M %p").lstrip("0")
                options.append(ft.dropdownm2.Option(text=label, key=value))
           
        return options

    def build_form(self):
        self.controls.clear()
      
        # Header
        self.header = ft.Container(
                content=ft.Row(controls=[
                    ft.Text("Editar evento" if self.event else "Nuevo evento", size=18, weight=ft.FontWeight.W_400, text_align=ft.TextAlign.CENTER, color=ft.Colors.WHITE),
                    ft.CupertinoButton(icon=ft.Icons.CLOSE, on_click=self.close_callback, icon_color=ft.Colors.WHITE)
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                alignment=ft.alignment.center_left,
                expand=True,
                padding=ft.padding.only(top=10, bottom=10, left=20, right=20),
                bgcolor=ft.Colors.BLUE_GREY_800,
                width=500,
                border=ft.border.only(bottom=ft.BorderSide(0.5, ft.Colors.GREY_400)),    
        )
        
        # Titulo
        self.tf_nombre = ft.Container(
            content=ft.TextField(
                border=ft.InputBorder.NONE,
                hint_text="Agregar título",
                on_change=lambda e: setattr(self, 'NombreEvento', e.control.value),
                value=self.NombreEvento
            ),
            bgcolor=ft.Colors.BLUE_GREY_100,
            border_radius=5,
            padding=ft.padding.only(left=10, right=10),
            expand=True,
        )

        # Descripción
        self.tf_descripcion = ft.Container(
            content=ft.TextField(
                border=ft.InputBorder.NONE,
                hint_text="Agregar descripción",
                on_change=lambda e: setattr(self, 'descripcion', e.control.value),
                value=self.descripcion,
                max_lines=3,
                min_lines=3,
                multiline=True,
            ),
            bgcolor=ft.Colors.BLUE_GREY_100,
            border_radius=5,
            padding=ft.padding.only(left=10, right=10),
            expand=True,
        )

        # Ubicación
        self.tf_ubicacion = ft.Container(
            content=ft.TextField(
                border=ft.InputBorder.NONE,
                hint_text="Agregar ubicación",
                on_change=lambda e: setattr(self, 'ubicacion', e.control.value),
                value=self.ubicacion
            ),
            bgcolor=ft.Colors.BLUE_GREY_100,
            border_radius=5,
            padding=ft.padding.only(left=10, right=10),
            expand=True,
        )

        # Fecha
        self.tf_fechaInicio = ft.Container(
            content=ft.TextField(
                border=ft.InputBorder.NONE,
                label="Fecha inicio",
                hint_text="dd/mm/YYYY",
                value=self.fechaInicio,
                width=200,
                on_blur=self.verifyForm,
            ),
            border_radius=5,
            padding=ft.padding.only(left=10, right=10)
        )
       
        # Hora inicio
        self.tf_horaInicio = ft.TextField(
            hint_text="HH:MM",
            value=self.horaInicio,
            label="Hora inicio",
            width=100,
            border=ft.InputBorder.NONE,
            on_blur=self.verifyForm,
        )

        self.dd_horaInicio = ft.Container(
            content=ft.Row(
                [
                    self.tf_horaInicio,
                    ft.Dropdown(
                        width=50,
                        menu_height=250,
                        menu_width=150,
                        border=ft.InputBorder.NONE,
                        options=self.get_time_options(),
                        on_change=lambda e: self.change_hour(e, is_horaInicio=True ),
                    ) 

                ]
        ),
            bgcolor=ft.Colors.BLUE_GREY_100,
            border_radius=5,
            padding=ft.padding.only(left=10, right=10),
        )
      
        # Hora Fin
        self.tf_horaFin = ft.TextField(
            hint_text="HH:MM",
            value=self.horaFin,
            label="Hora fin",
            width=100,
            border=ft.InputBorder.NONE,
            on_blur=self.verifyForm,
        )

        self.dropdown_horaFin = ft.Dropdown(
            width=50,
            menu_height=250,
            menu_width=150,
            border=ft.InputBorder.NONE,
            options=self.get_time_options(is_fechaInicio=False),
            on_change=lambda e: self.change_hour(e, is_horaInicio=False),
        )

        self.dd_horaFin = ft.Container(
            content=ft.Row([self.tf_horaFin, self.dropdown_horaFin]),
            bgcolor=ft.Colors.BLUE_GREY_100,
            border_radius=5,
            padding=ft.padding.only(left=10, right=10),
        )

    
        # botones 
        self.saveButton = ft.FilledButton("Guardar", on_click=self.on_save_click, bgcolor=ft.Colors.BLUE_500, width=460, height=40)

        if self.event:
            self.delete_button = ft.CupertinoButton(icon=ft.Icons.DELETE, icon_color=ft.Colors.RED, on_click=lambda e, id=self.event.id: self.delete_event(id))
        else:
            self.delete_button = ft.Container(height=40)  

        self.controls.extend(
            [self.header,
            ft.Container( padding=ft.padding.all(20), 
                content=ft.Column([ 
                    ft.Row([ft.Row([ft.Icon(name=ft.Icons.CALENDAR_MONTH_OUTLINED, color=ft.Colors.BLACK),self.tf_fechaInicio]), self.delete_button], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, width=460),
                    ft.Row([ft.Icon(name=ft.Icons.ACCESS_TIME, color=ft.Colors.BLACK), ft.Row([self.dd_horaInicio, ft.Icon(name=ft.Icons.ARROW_FORWARD, color=ft.Colors.BLACK), self.dd_horaFin],alignment=ft.MainAxisAlignment.SPACE_AROUND, expand=1)], width=460),
                    ft.Row([ft.Icon(name=ft.Icons.EDIT_SHARP, color=ft.Colors.BLACK),self.tf_nombre],expand=1, width=460),
                    ft.Row([ft.Icon(name=ft.Icons.LOCATION_ON, color=ft.Colors.BLACK),self.tf_ubicacion],expand=1, width=460),
                    ft.Row([ft.Icon(name=ft.Icons.DESCRIPTION, color=ft.Colors.BLACK),self.tf_descripcion],expand=1, width=460),
                    self.saveButton,
                ],spacing=20)
            )]
        )

    def change_hour(self, e, is_horaInicio=True):
        if is_horaInicio:
            self.horaInicio = e.control.value
            self.tf_horaInicio.value = datetime.time(int(self.horaInicio.split(":")[0]), 0).strftime("%I:%M %p").lstrip("0")
            self.dropdown_horaFin.options = self.get_time_options(is_fechaInicio=False)
            self.dropdown_horaFin.update()
            self.verifyForm()
            self.tf_horaInicio.update()
        else:
            self.horaFin = e.control.value
            self.tf_horaFin.value = datetime.time(int(self.horaFin.split(":")[0]), 0).strftime("%I:%M %p").lstrip("0")
            self.tf_horaFin.update()


    def verifyForm(self,  e=None):
        # Limpia espacios
        self.fechaInicio = (self.fechaInicio or "").strip()
        self.fechaFin = (self.fechaFin or "").strip()
        self.horaInicio = (self.horaInicio or "").strip()
        self.horaFin = (self.horaFin or "").strip()
        self.NombreEvento = (self.NombreEvento or "").strip()

        # Validadores: dd/mm/YYYY y HH:MM (24h)
        date_pattern = r"^\d{2}/\d{2}/\d{4}$"
        #validar formato 12 horas con AM/PM
        time_pattern = r"^(0?[1-9]|1[0-2]):[0-5]\d (AM|PM)$"

        # Fecha inicio
        if not re.match(date_pattern, self.tf_fechaInicio.content.value):
            self.fechaInicio = self.event.start_time.strftime("%d/%m/%Y") if self.event else self.fechaInicio
            if self.tf_fechaInicio: self.tf_fechaInicio.content.value = self.fechaInicio
            self.tf_fechaInicio.update()
            return False
        else:
            self.fechaInicio = self.tf_fechaInicio.content.value
            
        # Hora inicio
        if not re.match(time_pattern, self.tf_horaInicio.value):
            self.horaInicio = datetime.datetime.strptime(self.horaInicio, "%I:%M %p").strftime("%I:%M %p").lstrip("0")
            if self.tf_horaInicio: self.tf_horaInicio.value = self.horaInicio
            self.tf_horaInicio.update()
            return False
        else:
            self.horaInicio = self.tf_horaInicio.value
                    
        # Hora fin
        #validar formato 
        if not re.match(time_pattern, self.tf_horaFin.value):
            self.horaFin = datetime.datetime.strptime(self.horaFin, "%I:%M %p").strftime("%I:%M %p").lstrip("0")
            if self.tf_horaFin: self.tf_horaFin.value = self.horaFin
            self.tf_horaFin.update()
            return False
        else:
            self.horaFin = self.tf_horaFin.value

        #hora fin no puede ser menor que hora inicio convierte a formato 24 horas para comparar
        horaFin_24 = datetime.datetime.strptime(self.tf_horaFin.value, "%I:%M %p")
        horaInicio_24 = datetime.datetime.strptime(self.tf_horaInicio.value, "%I:%M %p")

        if horaFin_24 < horaInicio_24:
            #si hora inicio es mayor a 11:00PM pone hora fin a 11:59PM
            if horaInicio_24.hour >= 23:
                self.horaFin = "11:59 PM"
            else:
                self.horaFin = (datetime.datetime.strptime(self.horaInicio, "%I:%M %p") + datetime.timedelta(hours=1)).strftime("%I:%M %p").lstrip("0")
            if self.tf_horaFin: self.tf_horaFin.value = self.horaFin
            self.tf_horaFin.update()
            return False

        if not self.NombreEvento:
            self.NombreEvento = "Nuevo evento"

        return True

    def on_save_click(self, e):
        # 1) validar / corregir campos
        istrue = self.verifyForm()
    
        if istrue:
            try:
                self.save_event(e)
            except TypeError:
                self.save_event()


# ---------------------------
# Vista principal del calendario
# ---------------------------
class Calendar(ft.Container):
    def __init__(self, data = None, add_event=None, remove_event=None, update_event=None):
        super().__init__(expand=True)

        # Estado inicial
        self.api_add_event = add_event
        self.api_update_event = update_event
        self.api_remove_event = remove_event
        self.data = data if data else []
        self.today = datetime.date.today()
        self.start_week = self.today - datetime.timedelta(days=self.today.weekday())
        self.week_days = [self.start_week + datetime.timedelta(days=i) for i in range(7)]
        self.event_manager = EventManager()

        # Eventos iniciales
        if self.data:
            self._load_initial_events()

        # Label del mes
        self.month_label = ft.Text("", size=16, weight=ft.FontWeight.W_700)
        first_month = self.week_days[0].strftime("%B %Y")
        last_month = self.week_days[-1].strftime("%B %Y")
        self.month_label.value = first_month if first_month == last_month else f"{first_month} - {last_month}"

        self.header = CalendarHeader(self.today, self.week_days)
        self.grid = CalendarGrid(
            self.week_days,
            self.event_manager.get_events_for_week(self.week_days),
            open_edit_event=self.open_edit_event,
            new_event=self.open_new_event
        )
        
        self.formCalendar = FormCalendar(
            save_event=lambda e: self.create_event(e),
            close_callback=lambda e=None: self.modal.close()  
        )

        self.modal = DraggableModal(left=150, top=150, content=self.formCalendar)

        # Botones de navegación
        self.week_navigator = ft.Row([
            ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=ft.Colors.BLACK, on_click=self.back_week),
            self.month_label,
            ft.IconButton(icon=ft.Icons.ARROW_FORWARD, icon_color=ft.Colors.BLACK, on_click=self.next_week),
            ft.IconButton(icon=ft.Icons.ADD, icon_color=ft.Colors.BLACK,  on_click=lambda e: self.open_new_event()),
        ])

        # Layout principal
        self.content = ft.Stack(
            controls=[
                ft.Column([self.week_navigator, self.header, self.grid], expand=True, spacing=0, ),
                self.modal.get_control(),
            ]
        ) 
       

    # Se cargan eventos de prueba
    def _load_initial_events(self):
        self.event_manager = EventManager()
        for ev_data in self.data:
            self.event_manager.add_event(calendar_event.Event.from_json(ev_data))


    def update_month_label(self, week_days):
        first_month = week_days[0].strftime("%B %Y")
        last_month = week_days[-1].strftime("%B %Y")
        self.month_label.value = first_month if first_month == last_month else f"{first_month} - {last_month}"
        self.month_label.update()

    def next_week(self, e):
        self.start_week += datetime.timedelta(days=7)
        self._update_week()

    def back_week(self, e):
        self.start_week -= datetime.timedelta(days=7)
        self._update_week()

    #abrir modal vacío
    def open_new_event(self, day=None, hour=None):
        self.formCalendar = FormCalendar(
            save_event=lambda e: self.create_event(e),
            close_callback=lambda e=None: self.modal.close(),
            day=day,
            hour=hour
        )

        self.modal.update_content(self.formCalendar)
        self.modal.open()

    def create_event(self, e):
        new_event = calendar_event.Event(
            id=str(uuid.uuid4()),
            title=self.formCalendar.NombreEvento,
            start_time=self.to_utc_datetime(self.formCalendar.fechaInicio, datetime.datetime.strptime(self.formCalendar.horaInicio, "%I:%M %p").strftime("%H:%M")),
            end_time=self.to_utc_datetime(self.formCalendar.fechaFin, datetime.datetime.strptime(self.formCalendar.horaFin, "%I:%M %p").strftime("%H:%M")),
            description=self.formCalendar.descripcion,
            location=self.formCalendar.ubicacion,
            color=ft.Colors.GREEN_800,
        )
        response = self.api_add_event(new_event) if self.api_add_event else None
        if response:
            new_event.id = response.data[0]["id"]
        self.event_manager.add_event(new_event)
        self.modal.close()
        self.grid.render_events(self.event_manager.get_events_for_week(self.week_days), self.week_days)
    
    # abrir modal en modo edición
    def open_edit_event(self, event: calendar_event.Event):
        self.formCalendar = FormCalendar(
            save_event=lambda e, ev=event: self.update_event(ev),
            close_callback=lambda e=None: self.modal.close(),
            event=event,
            delete_event=lambda e, ev_id=event.id: self.delete_event(ev_id)
        )
        self.modal.update_content(self.formCalendar)
        self.modal.open()

    # actualizar evento existente
    def update_event(self, event: calendar_event.Event):
        event.title = self.formCalendar.NombreEvento
        event.start_time = self.to_utc_datetime(self.formCalendar.fechaInicio, datetime.datetime.strptime(self.formCalendar.horaInicio, "%I:%M %p").strftime("%H:%M"))
        event.end_time = self.to_utc_datetime(self.formCalendar.fechaFin, datetime.datetime.strptime(self.formCalendar.horaFin, "%I:%M %p").strftime("%H:%M"))
        self.modal.close()
        self.api_update_event(event) if self.api_update_event else None
        self.grid.render_events(self.event_manager.get_events_for_week(self.week_days), self.week_days)

    def delete_event(self, id):
        self.event_manager.remove_event(id)
        self.modal.close()
        self.api_remove_event(id) if self.api_remove_event else None
        self.grid.render_events(self.event_manager.get_events_for_week(self.week_days), self.week_days)

    def _update_week(self):
        self.week_days = [self.start_week + datetime.timedelta(days=i) for i in range(7)]
        self.header.update_week(self.week_days)
        self.grid.render_events(self.event_manager.get_events_for_week(self.week_days), self.week_days)
        self.update_month_label(self.week_days)

    def to_utc_datetime(self, fecha: str, hora: str) -> datetime.datetime:
        # Intentar varios formatos comunes
        dt_str = f"{fecha} {hora}"
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M"):
            try:
                dt = datetime.datetime.strptime(dt_str, fmt)
                return dt.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        dt = datetime.datetime.now()
        return dt.replace(tzinfo=timezone.utc)
