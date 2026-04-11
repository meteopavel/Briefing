import os

import pandas as pd

from app.config import ACTS_DATA_FILE, TIMELOGS_DIR


def load_acts_data():
    dataframe = pd.read_excel(
        ACTS_DATA_FILE,
        dtype={
            'year': int,
            'month': str,
            'redmine_file': str,
            'total_amount': int,
            'act_num': int,
            'start_date': str,
            'end_date': str,
        },
    )

    dataframe['redmine_file'] = dataframe['redmine_file'].apply(
        lambda value: os.path.join(TIMELOGS_DIR, value)
    )
    return dataframe
