import flet as ft
import datetime


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
                ft.Container(
                    width=60,
                    height=100,
                    border=ft.border.all(0.2, ft.Colors.GREY_400),
                ),
                *[
                    ft.Container(
                        content=ft.Column(
                            [
                                # Día abreviado (%a)
                                ft.Text(
                                    day.strftime("%a"),
                                    size=11,
                                    weight=ft.FontWeight.W_700,
                                    color="red"
                                    if day == self.today
                                    else "blue"
                                    if day == self.day_selected
                                    else "black",
                                ),
                                # Número de día (%d)
                                ft.Container(
                                    content=ft.Text(day.strftime("%d"), size=21,
                                        color="Red"
                                        if day == self.today
                                        else "White"
                                        if day == self.day_selected
                                        else "black",
                                    ),
                                    alignment=ft.alignment.center,
                                    height=50,
                                    width=50,
                                    border_radius=100,
                                    bgcolor="blue"
                                    if self.day_selected == day
                                    else "white",
                                    on_click=lambda e, d=day: self.change_day(d),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=4,
                        ),
                        border=ft.border.all(0.2, ft.Colors.GREY_400),
                        expand=True,
                        height=100,
                    )
                    for day in self.week_days
                ],
            ],
        )

    def change_day(self, day):
        self.day_selected = day
        self.controls[0] = self.build_row()  # reconstruir fila
        self.update()

    def update_week(self, week_days):
        self.week_days = week_days
        self.controls[0] = self.build_row()
        self.update()


def build_view_calendar(page: ft.Page) -> ft.Container:
    today = datetime.date.today()
    start_week = today - datetime.timedelta(days=today.weekday())
    week_days = [start_week + datetime.timedelta(days=i) for i in range(7)]
    #Mes de la semana
    first_month = week_days[0].strftime("%B %Y")
    last_month = week_days[-1].strftime("%B %Y")
    month_text = first_month if first_month == last_month else f"{first_month} - {last_month}"
    month_label = ft.Text(month_text, size=16, weight=ft.FontWeight.W_700)
    header = CalendarHeader(today, week_days,)

    # Grilla de horas
    grid = ft.Column(spacing=0, scroll=True, expand=True)
    for hour in range(0, 24):
        row = ft.Row(
            spacing=0,
            controls=[
                # Columna con la hora
                ft.Container(content=ft.Text(f"{hour:02d}:00", color="Black"), alignment= ft.alignment.center, width=60),
                # Celdas de los 7 días
                ft.Row(
                    controls=[
                        ft.Container(
                            width=100,
                            height=40,
                            bgcolor=ft.Colors.GREY_200,
                            border=ft.border.all(0.2, ft.Colors.GREY_400),
                            expand=True,
                        )
                        for _ in week_days
                    ],
                    expand=True,
                    spacing=0,
                ),
            ],
        )
        grid.controls.append(row)

    #Navegacion entre semanas

    def next_week(e):
        nonlocal start_week
        start_week += datetime.timedelta(days=7)
        new_week = [start_week + datetime.timedelta(days=i) for i in range(7)]
        header.update_week(new_week)
        update_month_label(new_week)
        #update_grid(new_week)

    def back_week(e):
        nonlocal start_week
        start_week -= datetime.timedelta(days=7)
        new_week = [start_week + datetime.timedelta(days=i) for i in range(7)]
        header.update_week(new_week)
        update_month_label(new_week)
        #update_grid(new_week)

    def update_month_label(week_days):
        # Tomamos el mes del primer día
        first_month = week_days[0].strftime("%B %Y")
        last_month = week_days[-1].strftime("%B %Y")
        if first_month == last_month:
            month_label.value = first_month
        else:
            month_label.value = f"{first_month} - {last_month}"
        month_label.update()

    week_navigator = ft.Row([
        ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=ft.Colors.BLACK, on_click=back_week),
        month_label,
        ft.IconButton(icon=ft.Icons.ARROW_FORWARD, icon_color=ft.Colors.BLACK, on_click=next_week)
    ])

    # Layout principal

    return ft.Container(
        expand=True,
        content = ft.Column([ week_navigator, header, grid], expand=True, spacing=0),
        
    )
