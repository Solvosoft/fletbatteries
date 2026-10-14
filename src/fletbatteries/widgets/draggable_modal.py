import flet as ft


class DraggableModal:
    def __init__(self, left=100, top=100,  content=None):
        self.left = left
        self.expand = True
        self.top = top
       
        self.visible = False  
        self.content = content

        # Contenido del modal con GestureDetector
        self.modal_content = ft.GestureDetector(
            content= self.content,
            on_pan_update=self.move_modal,
        )

       

        # Container principal posicionado en el Stack
        self.modal = ft.Container(
            content=self.modal_content,
            bgcolor=ft.Colors.SURFACE,
            border_radius=10,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK_26),
            left=self.left,
            top=self.top,
            visible=self.visible,  
        )
    def update_content(self, new_content):
        self.content = new_content
        self.modal_content.content = new_content  
        self.modal_content.update()
        self.modal.update()


    # Función para mover el modal
    def move_modal(self, e: ft.DragUpdateEvent):
        if e.local_delta is None:
            return
        self.modal.left += e.local_delta.x
        self.modal.top += e.local_delta.y
        self.modal.update()

    # Abrir el modal
    def open(self):
        self.modal.visible = True
        self.modal.update()

    # Cerrar el modal
    def close(self):
        self.modal.visible = False
        self.modal.update()

    # Para usarlo en page.add
    def get_control(self):
        return self.modal
    
    



