import flet as ft
import datetime
import uuid
from data.models import calendar_event
from data.manager.calendar_event_manager import EventManager
from components.shared.draggableModal import DraggableModal


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
                ft.Container(width=60, height=100,
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
            t = datetime.time(h, 0)
            # "%I" → hora 12h, "%p" → AM/PM
            formatted = t.strftime("%I %p").lstrip("0")  # "01 PM" → "1 PM"
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
            day_events = [ev for ev in self.events if ev.date == day]
            for ev in day_events:
                start_hour = int(ev.start_time.split(":")[0])
                end_hour = int(ev.end_time.split(":")[0])
                duration = max(1, end_hour - start_hour)

                day_stack.controls.append(
                    ft.Container(
                        top=self.hour_height * start_hour,
                        left=0,
                        right=5,
                        height=self.hour_height * duration,
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
        print(f"FormCalendar initialized with day={day}, hour={hour}")
        
        # Inicializa los campos según si es edición o creación
        if self.event:
            self.fechaInicio = str(self.event.date)
            self.horaInicio = self.event.start_time
            self.fechaFin = str(self.event.date)
            self.horaFin = self.event.end_time
            self.NombreEvento = self.event.title
        else:
            self.fechaInicio = self.day if self.day else str(datetime.date.today())
            self.horaInicio = self.hour if self.hour else datetime.datetime.now().strftime("%H:00")
            self.fechaFin = self.day if self.day else str(datetime.date.today())
            self.horaFin = self.hour if self.hour else (datetime.datetime.now() + datetime.timedelta(hours=1)).strftime("%H:00")
            self.NombreEvento = "Nuevo evento"

        self.build_form()

    def get_time_options(self):
        options = []
        for h in range(24):
            value = f"{h:02d}:00"  # valor real en 24h
            label = datetime.time(h, 0).strftime("%I:%M %p").lstrip("0")  # formato 12h
            options.append(ft.dropdownm2.Option(text=label, key=value))
        return options

    def build_form(self):
        self.controls.clear() 
        self.controls.append(
            ft.TextField(value=self.NombreEvento, label="Nombre del evento",
                         on_change=lambda e: setattr(self, 'NombreEvento', e.control.value))
        )
        self.controls.append(
            ft.Column([
                ft.Text("Inicio"),
                ft.Row([
                    ft.TextField(value=self.fechaInicio, width=200,
                                 on_change=lambda e: setattr(self, 'fechaInicio', e.control.value)),
                    ft.Dropdown(menu_height=250, menu_width=150, options=self.get_time_options(), enable_filter=True,editable=True,
                                  value=self.horaInicio, on_change=lambda e: setattr(self, 'horaInicio', e.control.value))
                ])
            ])
        )
        self.controls.append(
            ft.Column([
                ft.Text("Fin"),
                ft.Row([
                    ft.TextField(value=self.fechaFin, width=200,
                                 on_change=lambda e: setattr(self, 'fechaFin', e.control.value)),
                    ft.Dropdown(menu_height=250, menu_width=150, options=self.get_time_options(), enable_filter=True,editable=True,
                                  value=self.horaFin, on_change=lambda e: setattr(self, 'horaFin', e.control.value))
                ])
            ])
        )

        buttons = [
            ft.FilledButton("Guardar", on_click=self.save_event, bgcolor=ft.Colors.BLUE_400),
            ft.FilledButton("Cancelar", on_click=self.close_callback, bgcolor=ft.Colors.GREY_400),
            ]

        if self.event: 
                buttons.append(
                ft.FilledButton("Eliminar", bgcolor=ft.Colors.GREY_400, on_click=lambda e: self.delete_event(self.event.id))
        )

        self.controls.append(ft.Row(buttons))
    

# ---------------------------
# Vista principal del calendario
# ---------------------------
class Calendar(ft.Container):
    def __init__(self):
        super().__init__(expand=True)

        # Estado inicial
        self.today = datetime.date.today()
        self.start_week = self.today - datetime.timedelta(days=self.today.weekday())
        self.week_days = [self.start_week + datetime.timedelta(days=i) for i in range(7)]
        self.event_manager = EventManager()

        # Eventos iniciales
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
        self.event_manager.add_event(calendar_event.Event(str(uuid.uuid4()), "Reunión equipo", self.today, "09:00", "11:00", "green"))
        self.event_manager.add_event(calendar_event.Event(str(uuid.uuid4()), "Clase inglés", self.today, "14:00", "15:00", "blue"))
        self.event_manager.add_event(calendar_event.Event(str(uuid.uuid4()), "Gym", self.today, "18:00", "19:00", "purple"))
        day_1 = self.today + datetime.timedelta(days=1)
        self.event_manager.add_event(calendar_event.Event(str(uuid.uuid4()), "Proyecto X", day_1, "10:00", "12:15", "orange"))
        self.event_manager.add_event(calendar_event.Event(str(uuid.uuid4()), "Cita médica", day_1, "16:00", "17:00", "red"))
        day_2 = datetime.date(self.today.year, 9, 8)
        self.event_manager.add_event(calendar_event.Event(str(uuid.uuid4()), "Reunión con clientes", day_2, "11:00", "12:30", "blue"))
        self.event_manager.add_event(calendar_event.Event(str(uuid.uuid4()), "Clase de yoga", day_2, "18:00", "19:00", "purple"))


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
            date=datetime.datetime.strptime(self.formCalendar.fechaInicio, "%Y-%m-%d").date(),
            start_time=self.formCalendar.horaInicio,
            end_time=self.formCalendar.horaFin,
            color=ft.Colors.GREEN_800,
        )
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
        event.date = datetime.datetime.strptime(self.formCalendar.fechaInicio, "%Y-%m-%d").date()
        event.start_time = self.formCalendar.horaInicio
        event.end_time = self.formCalendar.horaFin
        self.modal.close()
        self.grid.render_events(self.event_manager.get_events_for_week(self.week_days), self.week_days)

    def delete_event(self, id):
        self.event_manager.remove_event(id)
        self.modal.close()
        self.grid.render_events(self.event_manager.get_events_for_week(self.week_days), self.week_days)

    def _update_week(self):
        self.week_days = [self.start_week + datetime.timedelta(days=i) for i in range(7)]
        self.header.update_week(self.week_days)
        self.grid.render_events(self.event_manager.get_events_for_week(self.week_days), self.week_days)
        self.update_month_label(self.week_days)
