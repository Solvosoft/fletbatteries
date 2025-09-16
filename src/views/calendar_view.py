import flet as ft
from components.shared.calendar import Calendar
import os
from dotenv import load_dotenv
load_dotenv()
from supabase import create_client, Client
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def build_view_calendar(page):

    response = (
    supabase.table("Events")
    .select("*")
    .execute()
)
    return ft.Container(
        content=Calendar(response.data),
        expand=True,
    )

if __name__ == "__main__":
    ft.app(target=build_view_calendar)
