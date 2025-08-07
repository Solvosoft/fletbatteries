import flet as ft


def make_columns(columns, text_color):
    cols = []
    for n, column in enumerate(columns):
        name = column.get("name")
        if not name:
            print(f"Skipping column {n}")
            continue

        col = ft.DataColumn(
            label=ft.Text(name, color=text_color),
            numeric=column.get("numeric", False),
        )
        tip = column.get("tooltip")

        if tip:
            col.tooltip = tip

        cols.append(col)

    return cols


def make_rows(columns, data, text_color):
    rows = []
    keys = [
        (col.get("key") or col["name"].lower().replace(" ", "_"))
        for col in columns
    ]

    for item in data:
        cells = [
            ft.DataCell(
                ft.Text(str(item.get(k, "")),
                        color=text_color),            )
            for k in keys
        ]
        rows.append(ft.DataRow(cells=cells))
    return rows


def create_datatable(
        columns,
        data,
        bgcolor=ft.Colors.WHITE,
        text_color=ft.Colors.BLACK,
        border_width=1,
        border_color=ft.Colors.BLACK,
        radius=5,
):
    return ft.DataTable(
        width=700,
        bgcolor=bgcolor,
        border=ft.border.all(border_width, border_color),
        border_radius=radius,
        sort_column_index=0,
        sort_ascending=True,
        vertical_lines=ft.border.BorderSide(border_width, border_color),
        horizontal_lines=ft.border.BorderSide(border_width, border_color),
        columns=make_columns(columns, text_color),
        rows=make_rows(columns, data, text_color),
    )


def init_datatable():
    columns = [
        {"name": "ID", "tooltip": "This is a first column", "numeric": False, "sort": True},
        {"name": "Name", "tooltip": "This is a second column", "numeric": False, "sort": True},
        {"name": "Last Name", "numeric": False, "sort": True},
        {"name": "Phone", "numeric": True, "sort": False},
        {"name": "Email", "numeric": False, "sort": True},
    ]
    data = [
        {"id": 1, "name": "Ana", "last_name": "Gómez", "phone": 88888888, "email": "ana@gmail.com"},
        {"id": 2, "name": "Luis", "last_name": "Rojas", "phone": 55555555, "email": "luis@gmail.com"},
        {"id": 3, "name": "Eva", "last_name": "Zamora", "phone": 66666666, "email": "eva@gmail.com"},
        {"id": 4, "name": "Juan", "last_name": "Perez", "phone": 77777777, "email": "juan@gmail.com"},
        {"id": 5, "name": "Maria", "last_name": "Rodríguez", "phone": 88888888, "email": "maria@gmail.com"},
    ]


    return ft.Container(
        content=create_datatable(columns, data),
        expand=True,
        padding=10,
        alignment=ft.alignment.center,
    )



