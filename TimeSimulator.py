import datetime


class TimeSimulator:
    def __init__(self, initial_time):
        self.current_time = initial_time

    def advance_time(self, seconds):
        self.current_time += datetime.timedelta(seconds=seconds)

    def get_current_time(self):
        return self.current_time