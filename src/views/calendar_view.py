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

    response = (supabase.table("Events").select("*").execute())
    
    def event_to_dict(event):
        return {
            "title": event.title,
            "start_time": event.start_time.isoformat(),
            "end_time": event.end_time.isoformat(),
            "color": event.color
        }

    def add_event(event):
        response = supabase.table("Events").insert(event_to_dict(event)).execute()
        return response

    def remove_event(event_id):
       supabase.table("Events").delete().eq("id", event_id).execute()

    def update_event(event):
        response = supabase.table("Events").update(event_to_dict(event)).eq("id", event.id).execute()

    return ft.Container(
        content=Calendar(response.data, add_event=add_event, remove_event=remove_event, update_event=update_event),
        expand=True,
    )

if __name__ == "__main__":
    ft.app(target=build_view_calendar)
