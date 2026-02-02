import pandas as pd

excel_file = r'D:\project\pythonproject\work\AItest\prod-answer\docs\产品集技术参数V3.xlsx'

# Read first sheet
df = pd.read_excel(excel_file, sheet_name=0)

print('Shape:', df.shape)
print('\nColumns:')
for i, col in enumerate(df.columns):
    print(f'  Column {i}: {col}')

print('\nFirst 3 rows:')
print(df.head(3).to_string())
