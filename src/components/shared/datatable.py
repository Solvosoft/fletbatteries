import flet as ft
from assets.fontawesome.fontawesome import get_icon

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
            cursor_width=2,
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

        self.btn_first = ft.IconButton(
            icon=ft.Icons.FIRST_PAGE,
            tooltip="First page",
            on_click=lambda e: self._go_first()
        )
        self.btn_prev = ft.IconButton(
            icon=ft.Icons.CHEVRON_LEFT,
            tooltip="Previous page",
            on_click=lambda e: self._go_prev()
        )
        self.btn_next = ft.IconButton(
            icon=ft.Icons.CHEVRON_RIGHT,
            tooltip="Next page",
            on_click=lambda e: self._go_next()
        )
        self.btn_last = ft.IconButton(
            icon=ft.Icons.LAST_PAGE,
            tooltip="Last page",
            on_click=lambda e: self._go_last()
        )

        self.dd_page_size = ft.Dropdown(
            width=90,
            options=[
                ft.dropdown.Option("1"),
                ft.dropdown.Option("10"),
                ft.dropdown.Option("25"),
                ft.dropdown.Option("50")
            ],
            value="1",
            on_change=lambda e: self._change_page_size(int(e.control.value)),
        )

        self.lbl_page_info = ft.Text(size=12, color=ft.Colors.BLACK)

        self.row_headers = ft.Row(
            controls=self.create_columns(),
            alignment=ft.alignment.center,
        )

        self.header.datatable.on_pagination_update = lambda: self._update_page_info(do_update=True)

        self.row_actions = ft.Row(
            controls=[
                self.btn_clear,
                ft.Container(expand=True),
                ft.Text("Rows:", size=12),
                self.dd_page_size,
                self.btn_first,
                self.btn_prev,
                self.btn_next,
                self.btn_last,
                self.lbl_page_info,
            ],
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        self.content = self.content_header()
        self._update_page_info(do_update=False)

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
                cols.append(self.text_column(col.get("name")))
            elif col.get("type") == "filter":
                cols.append(self.filter_column(col.get("name")))
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
        return ft.Container(
            expand=expand,
            alignment=ft.alignment.top_center,
            content=ft.Text(
                name,
                size=13,
                color=ft.Colors.BLACK,
                weight=ft.FontWeight.BOLD,
            )
        )

    def filter_column(self, name, expand=True):
        label = ft.Text(
            name,
            size=13,
            color=ft.Colors.BLACK,
            weight=ft.FontWeight.BOLD,
        )
        filter_input = ft.TextField(
            text_size=13,
            content_padding=ft.padding.symmetric(horizontal=8),
            # bgcolor="#E5E7EB",
            border_radius=5,
            cursor_color=ft.Colors.BLACK,
            cursor_width=2,
            # border=ft.InputBorder.NONE,
            cursor_height=16,
            color=ft.Colors.BLACK,
            on_change=lambda e: self.on_change(e),
            expand=False,
        )
        self.filters_values.append(filter_input)
        return ft.Container(
            expand=expand,
            alignment=ft.alignment.top_center,
            content=ft.Column(
                spacing=4,
                controls=[
                    label,
                    filter_input
                ],
            ),
        )

    def on_change(self, e):
        keyword = e.control.value
        if not keyword:
            self.header.datatable.fill_data_table([])
            return
        results = self.header.filter_data(keyword)
        if not results:
            self.header.datatable.fill_data_table([])
            return
        self.header.datatable.fill_data_table(results)

    def _update_page_info(self, do_update: bool = True):
        dt = self.header.datatable
        total = dt._total_items()
        if total == 0:
            text = "0–0 de 0"
        else:
            start = (dt.current_page - 1) * dt.page_size + 1
            end = min(start + dt.page_size - 1, total)
            text = f"{start}–{end} de {total}  (pág. {dt.current_page}/{dt.total_pages()})"

        self.lbl_page_info.value = text
        self.btn_first.disabled = self.btn_prev.disabled = (dt.current_page <= 1)
        self.btn_last.disabled = self.btn_next.disabled = (dt.current_page >= dt.total_pages())

        # Solo llamar .update() si ya estamos montados en la Page
        if do_update and self.page is not None:
            self.lbl_page_info.update()
            self.btn_first.update()
            self.btn_prev.update()
            self.btn_next.update()
            self.btn_last.update()

    def _change_page_size(self, size: int):
        self.header.datatable.set_page_size(size)

    def _go_first(self):
        self.header.datatable.first_page()

    def _go_prev(self):
        self.header.datatable.prev_page()

    def _go_next(self):
        self.header.datatable.next_page()

    def _go_last(self):
        self.header.datatable.last_page()


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

        self.current_data = list(data)
        self.page_size = 1
        self.current_page = 1

        cols = self.create_columns()
        rows = self.create_rows(self._get_page_items())

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

    def create_rows(self, data=None):
        if data is None:
            data = []
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
                        ft.Text(
                            str(item.get(k, "")),
                            color=self.color_text
                        )
                    )
                    for k in keys
                ]
                rows.append(ft.DataRow(cells=cells))
        return rows

    def _total_items(self):
        return len(self.current_data)

    def total_pages(self):
        if self.page_size <= 0:
            return 1
        return max(1, (self._total_items() + self.page_size - 1) // self.page_size)

    def _get_page_items(self):
        start = (self.current_page - 1) * self.page_size
        end = start + self.page_size
        return self.current_data[start:end]

    def set_page_size(self, size: int):
        self.page_size = max(1, int(size))
        self.current_page = 1
        self._refresh_page()

    def first_page(self):
        self.current_page = 1
        self._refresh_page()

    def prev_page(self):
        self.current_page = max(1, self.current_page - 1)
        self._refresh_page()

    def next_page(self):
        self.current_page = min(self.total_pages(), self.current_page + 1)
        self._refresh_page()

    def last_page(self):
        self.current_page = self.total_pages()
        self._refresh_page()

    def _refresh_page(self):
        self.rows = self.create_rows(self._get_page_items())
        self.update()
        try:
            if hasattr(self, "on_pagination_update") and callable(self.on_pagination_update):
                self.on_pagination_update()
        except Exception as ex:
            print(f"Error al actualizar paginación: {ex}")

    def fill_data_table(self, data=None):
        if data is not None:
            self.current_data = list(data)
            self.current_page = 1
        self.rows = self.create_rows(self._get_page_items())
        self.update()
        try:
            if hasattr(self, "on_pagination_update") and callable(self.on_pagination_update):
                self.on_pagination_update()
        except Exception as ex:
            print(f"Error al actualizar paginación: {ex}")


class FBDataTable(ft.Container):

    def __init__(self, data, columns_names,title="My DataTable",
                 color_text=ft.Colors.BLACK, bgcolor=ft.Colors.WHITE10,
                 border_width=1, border_color=ft.Colors.BLACK,
                 border_radius=5, sort_as=True, sort_index=0
                 ):
        self.data= data
        self.columns_names = columns_names
        self.table = DataTable(data, columns_names, color_text, bgcolor, border_width, border_color, border_radius, sort_as, sort_index)
        self.header = Header(title, self.table)
        self.header_cols = HeaderColumn(columns_names, self.header)

        self.content = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[
                self.header,
                self.header_cols,
                self.table,
            ],
            spacing=5,
        )
        super().__init__(
            expand=True,
            content=self.content,
            alignment=ft.alignment.top_center,
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

    datatable = FBDataTable(data, columns_names, title="Customers")

    return ft.Container(
        content=datatable,
        expand=True,
        padding=10,
        alignment=ft.alignment.center,
    )
