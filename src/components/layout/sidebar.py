import flet as ft

from controls.router.views import Views

class Sidebar(ft.Container):

    def __init__(self, app_layout): #, store: DataStore):
        # self.store: DataStore = store
        self.app_layout = app_layout
        self.nav_rail_visible = True
        self.top_nav_items = [
            ft.NavigationRailDestination(
                label_content=ft.Text(v.name),
                label=v.name,
                icon=v.icon,
                selected_icon=v.icon,
                data=v.route,
            ) for v in Views(self.app_layout.page).views if v.position == 1
        ]

        self.top_nav_rail = ft.NavigationRail(
            selected_index=None,
            label_type=ft.NavigationRailLabelType.ALL,
            on_change=self.top_nav_change,
            destinations=self.top_nav_items,
            extended=True,
            height=55*len(self.top_nav_items),
        )

        self.toggle_nav_rail_button = ft.IconButton(ft.Icons.ARROW_BACK)

        super().__init__(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text("Panel", weight=ft.FontWeight.BOLD),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    # divider
                    ft.Container(
                        border_radius=ft.border_radius.all(30),
                        height=1,
                        alignment=ft.alignment.center_right,
                        width=220,
                    ),
                    self.top_nav_rail,
                    # divider
                    ft.Container(
                        border_radius=ft.border_radius.all(30),
                        height=1,
                        alignment=ft.alignment.center_right,
                        width=220,
                    ),
                ],
                tight=True,
            ),
            padding=ft.padding.all(15),
            margin=ft.margin.all(0),
            width=250,
            visible=self.nav_rail_visible,
            alignment=ft.alignment.top_center,
        )

    def top_nav_change(self, e):
        self.top_nav_rail.selected_index = e.control.selected_index
        self.update()
        route = self.top_nav_rail.destinations[e.control.selected_index].data
        self.app_layout.page.go(route)

