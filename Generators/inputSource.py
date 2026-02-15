from . import base 
from datetime import date, timedelta
import random
from typing import Any # Import Any for flexible dicts

DEFAULT_FILE_COUNT = 3

class InputSource(base.Base):
    def __init__(self, config: dict[str, Any], sub_config_key: str):
        super().__init__(config, sub_config_key)

    def get_random_date(self, min_year: int) -> date:
        start_date = date(min_year, 1, 1)
        current_date = date.today()
        delta = current_date - start_date
        num_days = delta.days

        # Generate a random number of days within the range
        random_days = random.randint(0, num_days)

        # Add the random number of days to the start date to get a random date
        random_date = start_date + timedelta(days=random_days)

        return random_date
