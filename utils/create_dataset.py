import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def sample(data, field_name, leave_percents=[0.5, 1, 0.5]):
    data = data.sort_values(by=field_name)
    strat_lengths = [int(len(data) * p / 100) for p in leave_percents]
    result = [
                data[: strat_lengths[0]],
                data[strat_lengths[0]: -strat_lengths[2]].sample(2 * strat_lengths[1]),
                data[-strat_lengths[2]:]
              ]
    return pd.concat(result)


fields_to_filter_by = ['Score', 'ViewCount', 'AnswerCount', 'FavoriteCount', 'CommentCount']
csv_data = pd.read_csv('../light_dump.csv')

subsets = []
for field in fields_to_filter_by:
    subsets.append(sample(csv_data, field))

dataset = pd.concat(subsets)
dataset = dataset.drop_duplicates()

dataset.to_csv('../dataset.csv', columns=['Id', 'AcceptedAnswerId'], index=False)
