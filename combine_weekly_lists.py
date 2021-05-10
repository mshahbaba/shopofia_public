import pandas as pd
from os import listdir
from os.path import isfile, join
import datetime, calendar


# this is the path to a folder which has weekly list csv files, here 'files' folder
mypath = '/Users/mahdishahbaba/shopofia-db-bucket/files/'

def get_last_friday(sanpshot_dt):
    lastFriday = datetime.datetime.strptime(sanpshot_dt, '%Y-%m-%d')#.date()

    oneday = datetime.timedelta(days=1)

    while lastFriday.weekday() != calendar.FRIDAY:
        lastFriday -= oneday

    return lastFriday.strftime("%D")


onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]

df_list = []
for f in onlyfiles:
    df_list.append(pd.read_csv(mypath+f))


result = pd.concat(df_list, ignore_index=True, axis=0)

result.loc[:,'snapshot_date'] = result.loc[:,'snapshot_date'].apply(get_last_friday)

result = result.drop(['Unnamed: 0', 'index'], axis=1)

result.loc[:,'shopofia'] = 1
print(result.columns)

print(result['snapshot_date'].unique())


# path to the final file
result.to_csv(r'/Users/mahdishahbaba/shopofia-db-bucket/output/weekly_list_combined.csv', index=False)

# just to test the function, you can ignore the following
sanpshot_dt = str(datetime.date.today())
print(get_last_friday(sanpshot_dt))