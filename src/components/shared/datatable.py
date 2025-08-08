import flet as ft
from assets.fontawesome.fontawesome import get_icon

class Controller:
    items: list[dict]
    counter: int

    def __init__(self, items):
        self.items = items
        self.counter = len(items)

    def get_item(self):
        return self.items

    def add_item(self, item):
        self.items.append( item )
        self.counter += 1


header_style: dict = {
    "height": 60,
    "bgcolor": "#081d33",
    "border_radius": ft.border_radius.only(top_left=15, top_right=15),
    "padding": ft.padding.only(left=10, right=10),
    "expand": False,
}

class Header(ft.Container):

    def __init__(self, title, datatable):
        super().__init__(**header_style)
        self.datatable = datatable
        self.search_value = self.search_field()
        self.search = self.search_bar()
        self.name = ft.Text(title, color="white")
        self.btn_toggle = ft.IconButton(
            icon=ft.Icons.SEARCH,
            on_click=lambda e: self.toggle_search(e)
        )
        self.content = ft.Row(
            controls=[
                self.name,
                self.search,
                self.btn_toggle,
            ],
            expand=True,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def search_field(self):
        return ft.TextField(
            border_color="transparent",
            height=20,
            text_size=14,
            content_padding=0,
            cursor_color="white",
            cursor_width=1,
            color="white",
            hint_text="Search",
            on_change=self.filter_dt_rows,
            autofocus=True,
        )

    def search_bar(self):
        return ft.Container(
            # expand=True,
            content=self.search_value,
            visible=False,
            alignment=ft.alignment.center,
        )

    def toggle_search(self, e):
        self.search.visible = not self.search.visible
        self.search.update()

    def filter_data(self,keyword):
        # filtrar data
        data_values = self.datatable.data_values
        results = []

        for item in data_values:
            # buscar en los valores
            for key, value in item.items():
                if keyword.lower() in str(value).lower():
                    print(f"Match: {key}: {value}")
                    results.append(item)
                    break

        return results

    def filter_dt_rows(self, e):
        print(e.control.value)
        keyword = e.control.value
        if not keyword:
            self.datatable.fill_data_table(self.datatable.data_values)
            return

        results = self.filter_data(keyword)

        if not results:
            self.datatable.fill_data_table([])
            return

        self.datatable.fill_data_table(results)



header_cols_style: dict = {
    "border_radius": 8,
    "border": ft.border.all(1, "#ebebeb"),
    "bgcolor": ft.Colors.WHITE10,
    "padding": 10,
    "expand": True,
}

class HeaderColumn(ft.Container):
    def __init__(self, columns, header):
        super().__init__(**header_cols_style)
        self.header = header
        self.columns = columns
        self.filters_values = []

        self.btn_clear = ft.ElevatedButton(
            content=get_icon("eraser", color="black", size=15),
            on_click=self.clear_filter,
        )

        self.row_headers = ft.Row(
            controls=self.create_columns(),
            alignment=ft.alignment.center,
        )
        self.row_actions = ft.Row(
            controls=[
                self.btn_clear,
            ],
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
        )
        self.content = self.content_header()

    def content_header(self):
        return ft.Column(
            controls=[
                self.row_actions,
                self.row_headers,
            ],
            expand=True,
            alignment=ft.alignment.center,
        )

    def create_columns(self):
        cols = []

        for col in self.columns:
            if col.get("type") == "text":
                cols.append(
                    self.text_column(col.get("name"))
                )
            elif col.get("type") == "filter":
                cols.append(
                    self.filter_column(col.get("name"))
                )
            else:
                print(f"This column not supported type: {col.get('type')}")
                continue

        return cols

    def clear_filter(self, e):
        self.header.search_value.value = ""
        self.header.search_value.update()

        for tv in self.filters_values:
            tv.value = ""
            tv.update()

        self.header.datatable.fill_data_table(self.header.datatable.data_values)

    def text_column(self, name, expand=True):
        return self.col_container(
            [
                ft.Text(
                    name,
                    height=30,
                    size=13,
                    color=ft.Colors.BLACK,
                    weight=ft.FontWeight.BOLD,
                )
            ],
            expand=expand,
        )

    def on_change(self, e):
        print(e.control.value)
        keyword = e.control.value
        if not keyword:
            self.header.datatable.fill_data_table([])
            return

        results = self.header.filter_data(keyword)

        if not results:
            self.header.datatable.fill_data_table([])
            return

        self.header.datatable.fill_data_table(results)

    def filter_column(self, name, expand=True):

        label = ft.Text(
            name,
            size=13,
            color=ft.Colors.BLACK,
            weight=ft.FontWeight.BOLD,
        )

        filter_input = ft.TextField(
            height=25,
            text_size=13,
            content_padding=0,
            bgcolor="#E5E7EB",
            cursor_color=ft.Colors.BLACK,
            cursor_width=1,
            border_color="transparent",
            cursor_height=13,
            color=ft.Colors.BLACK,
            on_change=lambda e: self.on_change(e),
            expand=True,
        )

        self.filters_values.append(filter_input)

        return self.col_container(
            [
                label,
                filter_input,
            ],
            expand=expand,
        )

    def col_container(
            self,
            content: list,
            expand: bool | int = True,
    ):
        return ft.Container(
            expand=expand,
            border_radius=6,
            padding=8,
            content=ft.Column(
                spacing=1,
                controls=content
            )
        )

class DataTable(ft.DataTable):
    def __init__(
            self,
            data,
            columns_names,
            color_text=ft.Colors.BLACK,
            bgcolor=ft.Colors.WHITE10,
            border_width=1,
            border_color=ft.Colors.BLACK,
            border_radius=5,
            sort_as=True,
            sort_index=0
    ):
        self.data_values = data
        self.columns_names = columns_names
        self.color_text = color_text

        cols = self.create_columns()
        rows = self.create_rows(self.data_values)

        super().__init__(
            columns=cols,
            rows=rows,
            bgcolor=bgcolor,
            border=ft.border.all(border_width, border_color),
            border_radius=border_radius,
            vertical_lines=ft.border.BorderSide(border_width, border_color),
            horizontal_lines=ft.border.BorderSide(border_width, border_color),
            sort_column_index=sort_index,
            sort_ascending=sort_as,
            expand=True,
        )

    def create_columns(self):
        cols = []
        for n, column in enumerate(self.columns_names):
            name = column.get("name")
            if not name:
                print(f"Skipping column {n}")
                continue

            col = ft.DataColumn(
                label=ft.Text(name, color=self.color_text, weight=ft.FontWeight.BOLD),
                numeric=column.get("numeric", False),
            )
            tip = column.get("tooltip")

            if tip:
                col.tooltip = tip

            cols.append(col)

        return cols


    def create_rows(self, data = []):
        rows = []
        keys = [
            (col.get("key") or col["name"].lower().replace(" ", "_"))
            for col in self.columns_names
        ]

        if len(data) == 0:
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(
                            ft.Container(
                                content=ft.Text("-"),
                                alignment=ft.alignment.center,
                            )
                        )
                        for _ in keys
                    ]
                )
            )

        else:
            for item in data:
                cells = [
                    ft.DataCell(
                        ft.Text(str(item.get(k, "")),
                                color=self.color_text), )
                    for k in keys
                ]
                rows.append(ft.DataRow(cells=cells))
        return rows

    def fill_data_table(self, data):
        # clear rows
        self.rows = []
        self.update()

        # add new rows
        self.rows = self.create_rows(data)
        self.update()



def create_datatable_filter(data, columns_names):
    table = DataTable(data, columns_names)
    header = Header("Customers", table)
    header_cols = HeaderColumn(columns_names, header)

    return ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        controls=[
            header,
            header_cols,
            table,
        ],
        spacing=5,
    )

def init_datatable():

    data = [
        {"id": 1, "name": "Ana", "last_name": "Gómez", "phone": 88888888, "email": "ana@gmail.com"},
        {"id": 2, "name": "Luis", "last_name": "Rojas", "phone": 55555555, "email": "luis@gmail.com"},
        {"id": 3, "name": "Eva", "last_name": "Zamora", "phone": 66666666, "email": "eva@gmail.com"},
        {"id": 4, "name": "Juan", "last_name": "Perez", "phone": 77777777, "email": "juan@gmail.com"},
        {"id": 5, "name": "Maria", "last_name": "Rodríguez", "phone": 88888888, "email": "maria@gmail.com"},
    ]

    columns_names = [
        {"name": "ID", "type": "filter", "expand": True},
        {"name": "Name", "type": "filter", "expand": True},
        {"name": "Last Name", "type": "text", "expand": True},
        {"name": "Phone", "type": "filter", "expand": True},
        {"name": "Email", "type": "text", "expand": True},
    ]

    return ft.Container(
        content=create_datatable_filter(data, columns_names),
        expand=True,
        padding=10,
        alignment=ft.alignment.center,
    )
