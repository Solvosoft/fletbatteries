class Event:
    def __init__(self, id, title, date, start_time, end_time, color="blue"):
        self.id = id
        self.title = title
        self.date = date
        self.start_time = start_time
        self.end_time = end_time
        self.color = color