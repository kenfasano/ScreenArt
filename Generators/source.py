from datetime import date, timedelta
import random

# Inherits directly from your new Generator base class
from .generator import Generator

class Source(Generator):
    """
    Intermediate base class for generators that fetch data based on dates.
    """
    def __init__(self):
        super().__init__()

    def get_random_date(self, min_year: int) -> date:
        start_date = date(min_year, 1, 1)
        current_date = date.today()
        delta = current_date - start_date
        num_days = delta.days

        random_days = random.randint(0, num_days)
        return start_date + timedelta(days=random_days)
