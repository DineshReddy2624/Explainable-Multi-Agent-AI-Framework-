import sys
import os
import io
import pandas as pd

sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/..'))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from services.agents.dataset_chat_agent import DatasetChatAgent

agent = DatasetChatAgent()
df1 = pd.read_csv('../datasets/original/1_customer_demographics_raw.csv')
df2 = pd.read_csv('../datasets/original/2_e_commerce_transactions_raw.csv')
analysis1 = {'filename': '1_customer_demographics_raw.csv'}
analysis2 = {'filename': '2_e_commerce_transactions_raw.csv'}

prompts = [
    ('1. Dataset Explanation', 'What is this dataset about?'),
    ('2. Dataset Summary', 'Summarize dataset'),
    ('3. Schema Inspection', 'List columns'),
    ('4. Show Dataset', 'Show complete table'),
    ('5. Show Rows', 'Show first 10 rows'),
    ('6. Show Columns', 'Show Age column'),
    ('7. Count', 'How many customers?'),
    ('8. Unique Values', 'How many unique Customer_ID?'),
    ('9. Missing Values', 'Show missing values'),
    ('10. Duplicates', 'Show duplicate rows'),
    ('11. Filtering', 'Show income > 80000'),
    ('12. Sorting', 'Show highest customer'),
    ('13. Grouping', 'Average spending by Category'),
    ('14. Statistics', 'Show statistics'),
    ('15. Correlation', 'Show correlation'),
    ('16. Outlier Detection', 'Show outliers'),
    ('17. General Conversation', 'What is Python?')
]

for cat, p in prompts:
    df_used = df2 if 'Category' in p or 'spending' in p else df1
    an_used = analysis2 if 'Category' in p or 'spending' in p else analysis1
    res = agent.process_chat_query(df_used, an_used, [], p)
    print(f"=== [{cat}] Prompt: \"{p}\" ===")
    print(res['text'])
    print("-" * 50)
