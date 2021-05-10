# -*- coding: utf-8 -*-
"""
Python script to get weekly flyer data
"""


import os
import re
import inflect
import pandas as pd
from datetime import date
from utils import post_text, right_item, Weight, search, Labeled_image, detect_text_url
import logging
from string import Template
import datetime
from google.cloud import storage


ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) # This is your Project Root
os.environ["GOOGLE_APPLICATION_CREDENTIALS"]=ROOT_DIR+"my-project.json"

storage_client = storage.Client()
bucketFolder = 'shopofia_db_bucket' #'gs://shopofia_db_bucket'
bucket = storage_client.get_bucket(bucketFolder)


def grocery_list():
  Baking=sorted(['baking powder','bread crumbs','bread','cake','cake icing','chocolate chips','flour','shortening','sugar','yeast',
                 'bagel','bun','donut','pie','pita'])
  Fruits=sorted(['apple', 'apricot','banana','berry','melon','strawberry','blackberry','cherry','grapefruit','mango','kiwi','orange','papaya','passion fruit'
  ,'peach','pear','pea','pineapple','plum','watermelon','raspberry','blueberry','grape','tangerine','pomegranate'])
  Diary=sorted(['egg','cheese','yogurt','milk','whipped cream','sour cream','cottage cheese','butter','margarine'])
  Vegetables=sorted(['asparagus','avocado','bean','broccoli','brussels sprout','cabbage','corn','cucumber','carrot','cauliflower'
          ,'celery','eggplant','lemon','lettuce','mushroom','potato','onion','garlic',
          'tomato','green pepper','asparagus','parsley','oregano','thyme','rosemary','basil','lavender','pepper','spinach','squash','zucchini'])
  Meat=sorted(['bacon','beef','burger','chicken','ground beef','ham','pork','hot dogs','turkey','sausage','steak','tenderloin','sirloin'])
  Seafood=sorted(['catfish','crab','lobster','mussel','oyster','salmon','tilapia','trout','tuna'])
  Cheese=sorted(['blue cheese','cheddar','cottage cheese','cream cheese','feta','goat cheese','mozzarella','parmesan','provolone',
                 'ricotta','sandwich slices','swiss cheese'])
  Fridge_items=sorted(['bagel','chip dip','english muffin','egg','fruite juice','hummus','tofu','tortillas','butter'])
  Sauces=sorted(['bbq sauce','gravy','honey','hot sauce','jam','ketchup','mayonnaise','pasta sauce','relish','salad dressing',
                 'syrup','steak sauce'])
  Spices=sorted(['basil','black pepper','cliantro','cinnamon','garlic','ginger','mint','oregano','paprika','parsley','red pepper'
  ,'salt','spice mix','vanilla'])
  Others=sorted(['cereal','coffee','instant potato','mac cheese','oil','olive oil','pancake','pasta','peanut butter','pickle',
                 'rice','tea','vegetable oil','vinegar'])
  Beverages=sorted(['beer','club soda','tonic','juice','soda pop','coke','pepsi','water'])
 
  All=Baking+Vegetables+Fruits+Diary+Meat+Seafood+Cheese+Fridge_items+Sauces+Spices+Others+Beverages

  # testing search function
  search_result = search('Milk','l6a3r7', 'en-ca')
  columns = list(search_result[0].keys())

  # Convert the product list to dataframe
  query_results=list()
  df=pd.DataFrame()
  for items in All:
    try:
      final_dict = {key:[] for key in columns}
      keys = final_dict.keys()
      query_results=search(items,'l6a3r7', 'en-ca')
      for q in query_results:
        for key in keys:
            final_dict[key].append(q[key])
      final_dict2=pd.DataFrame(final_dict)
      df=df.append(final_dict2)
      row=final_dict2.shape[0]
      df.index=range(df.shape[0])
      df.loc[df.shape[0]-row:,'product']=items
    except:
      continue

  df_sort=df.sort_values(['merchant_name'])
  mechant_name=df_sort.merchant_name.unique()
  df_sort["current_price"] = df_sort["current_price"].apply(pd.to_numeric)
  df_sort2=df_sort[df_sort.current_price>0]
  # Select the grocery sores from the merchant list

  food_store=[]
  for x in mechant_name:
    if 'food' in x.lower():
      food_store.append(x)
    if 'supermarket' in x.lower():
      food_store.append(x)
    if 'superstore' in x.lower():
      food_store.append(x)
    if 'mart' in x.lower():
      food_store.append(x)
    if 'fresh' in x.lower():
      food_store.append(x)
    if x in ['Walmart','Zehrs','Starsky','Sobeys','Price Chopper','No Frills','Longos','Real Canadian Superstore','Giant Tiger',
             'Shoppers Drug Mart','T&T Supermarket','Metro','Loblaws','Healthy Planet','Giant Tiger']:
      food_store.append(x)

  df_sort_food=df_sort2[df_sort2.merchant_name.isin(food_store)]
  df_sort_food.index=range(df_sort_food.shape[0])
  df_sort_food2=df_sort_food.drop_duplicates()


  df_sort_food2['labels']=df_sort_food2['clean_image_url'].apply(lambda x:Labeled_image(str(x)))


  # Filter for relevant photos
  for i in df_sort_food2.index:
    df_sort_food2.loc[i,'Relevant']=pd.Series(df_sort_food2.loc[i,'labels']).isin(['Fruit','Fish','Meat','Vegetable','Ingredient','Dairy','Oil','Bread','Beef', 'Veal',  'Steak','Beverage']+All).any()

  df_sort_food2=df_sort_food2[df_sort_food2.Relevant==True]

  for i in df_sort_food2.index:
    if df_sort_food2.loc[i,"Relevant"]==True:
      try:
        df_sort_food2.loc[i,"ocr_name"]=detect_text_url(df_sort_food2.loc[i,"clean_image_url"])
      except:
        df_sort_food2.loc[i,"ocr_name"]=['unidentified']

  df_sort_food2['vagetables']=[any([i == 'Vegetable' for i in (x)]) for x in df_sort_food2.labels ]
  df_sort_food2['fruit']=[any([i == 'Fruit' for i in (x)]) for x in df_sort_food2.labels ]
  df_sort_food2['meat']=[any([i == 'Meat' for i in (x)]) for x in df_sort_food2.labels ]
  df_sort_food2['veal']=[any([i == 'Veal' for i in (x)]) for x in df_sort_food2.labels ]
  df_sort_food2['meat_chicken']=[any(re.findall('chicken',x, re.IGNORECASE))  for x in df_sort_food2.ocr_name ]
  df_sort_food2['meat_steak']=[any(re.findall('steak',x, re.IGNORECASE))  for x in df_sort_food2.ocr_name ]
  df_sort_food2['meat_ground']=[any(re.findall('ground',x, re.IGNORECASE))  for x in df_sort_food2.ocr_name ]
  df_sort_food2['meat_tenderloin']=[any(re.findall('tenderloin',x, re.IGNORECASE))  for x in df_sort_food2.ocr_name ]
  df_sort_food2['meat_serloin']=[any(re.findall('sirloin',x, re.IGNORECASE))  for x in df_sort_food2.ocr_name ]
  df_sort_food2['rice']=[any(re.findall('rice',x, re.IGNORECASE))  for x in df_sort_food2.ocr_name ]
  df_sort_food2['bread']=[any(re.findall('bread',x, re.IGNORECASE))  for x in df_sort_food2.ocr_name ]
  df_sort_food2['milk']=[any(re.findall('milk',x, re.IGNORECASE))  for x in df_sort_food2.ocr_name ]
  df_sort_food2['egg']=[any(re.findall('egg',x, re.IGNORECASE))  for x in df_sort_food2.ocr_name ]
  df_sort_food2['yogurt']=[any(re.findall('yogurt',x, re.IGNORECASE))  for x in df_sort_food2.ocr_name ]
  df_sort_food2['butter']=[any(re.findall('butter',x, re.IGNORECASE))  for x in df_sort_food2.ocr_name ]
  df_sort_food2['oil']=[any(re.findall('oil',x, re.IGNORECASE))  for x in df_sort_food2.ocr_name ]
  df_sort_food2['cheese']=[any(re.findall('cheese',x, re.IGNORECASE))  for x in df_sort_food2.ocr_name ]
  df_sort_food2['pasta']=[any(re.findall('pasta',x, re.IGNORECASE))  for x in df_sort_food2.ocr_name ]

  # df_sort_food2['All']= df_sort_food2[['milk','egg','butter','yogurt','pasta','oil','cheese','vagetables','fruit','meat','veal','rice','bread']].any(axis='columns')
  for item in All:
    df_sort_food2[item]=[any(re.findall(item,x, re.IGNORECASE))  for x in df_sort_food2.ocr_name ]

  df_sort_food2['All']= df_sort_food2[All+['vagetables','fruit','meat','veal']].any(axis='columns')

  df_sort_food2=df_sort_food2[df_sort_food2['All']==True]

  for i in df_sort_food2.index:
    list_weight1=Weight(df_sort_food2.ocr_name[i],df_sort_food2.loc[i,"product"])
    list_weight2=Weight(df_sort_food2.name[i],df_sort_food2.loc[i,"product"])
    product=df_sort_food2.loc[i,'product'].lower()
    if(len(list_weight1[0])>len(list_weight2[0])):
      list_weight=list_weight1
    else :
      list_weight=list_weight2
    if len(list_weight[0])==0 and len(list_weight[1])==0 :
      df_sort_food2.loc[i,'weight']='NaN'
    elif len(list_weight[0])==0 and len(list_weight[1])>=1 :
      df_sort_food2.loc[i,'weight']=1
    elif len(list_weight[0])>=1 and len(list_weight[1])==0 :
      df_sort_food2.loc[i,'weight']=right_item(list_weight,product)
    elif len(list_weight[0])>=1 and len(list_weight[1])>=1 :
      df_sort_food2.loc[i,'weight']=right_item(list_weight,product)  

  for i in df_sort_food2.index:
    df_sort_food2.loc[i,'weight_num']=0  
    df_sort_food2.loc[i,'price_100']=0  
    df_sort_food2.loc[i,'weight2']=0
    try:
      if df_sort_food2.loc[i,'weight']== 1:
        df_sort_food2.loc[i,'weight_num']=1  
      elif not any(re.findall('/', df_sort_food2.loc[i,'weight'])) and df_sort_food2.loc[i,'weight'][-2:].lower() == 'kg' :
        df_sort_food2.loc[i,'weight2']=float(re.findall("[-+]?\d*\.\d+|\d+",df_sort_food2.loc[i,'weight'][:-2])[0])*1000
      elif any(re.findall('/', df_sort_food2.loc[i,'weight'])) and df_sort_food2.loc[i,'weight'][-2:].lower() == 'kg' :
        df_sort_food2.loc[i,'price_100']=float(re.findall("[-+]?\d*\.\d+|\d+",df_sort_food2.loc[i,'weight'][:-3])[0] )/10
      elif not any(re.findall('/', df_sort_food2.loc[i,'weight'])) and df_sort_food2.loc[i,'weight'][-1].lower()=='g' and df_sort_food2.loc[i,'weight'][-2:].lower() != 'kg':  
        df_sort_food2.loc[i,'weight2']=float(re.findall("[-+]?\d*\.\d+|\d+",df_sort_food2.loc[i,'weight'][:-1])[0] )
      elif df_sort_food2.loc[i,'weight'][-1].lower()=='l' and df_sort_food2.loc[i,'weight'][-2:].lower()=='ml':
        df_sort_food2.loc[i,'weight2']=float(re.findall("[-+]?\d*\.\d+|\d+",df_sort_food2.loc[i,'weight'][:-2])[0] )
      elif df_sort_food2.loc[i,'weight'][-1].lower()=='l' and df_sort_food2.loc[i,'weight'][-2:].lower()!='ml':
        df_sort_food2.loc[i,'weight2']=float(re.findall("[-+]?\d*\.\d+|\d+",df_sort_food2.loc[i,'weight'][:-1])[0] )*1000
      elif not any(re.findall('/', df_sort_food2.loc[i,'weight'])) and df_sort_food2.loc[i,'weight'][-2:].lower() == 'lb':
        df_sort_food2.loc[i,'weight2']=float(re.findall("[-+]?\d*\.\d+|\d+",df_sort_food2.loc[i,'weight'][:-2])[0] )*453.592
      elif any(re.findall('/', df_sort_food2.loc[i,'weight'])) and df_sort_food2.loc[i,'weight'][-2:].lower() == 'lb':
        df_sort_food2.loc[i,'price_100']=float(re.findall("[-+]?\d*\.\d+|\d+",df_sort_food2.loc[i,'weight'][:-2])[0] )/4.53592
      elif df_sort_food2.loc[i,'weight'][-2:].lower() == 'oz':
        df_sort_food2.loc[i,'weight2']=float(re.findall("[-+]?\d*\.\d+|\d+",df_sort_food2.loc[i,'weight'][:-2])[0] )*28.3495
      elif df_sort_food2.loc[i,'weight'][-4:].lower() == 'pack':
        df_sort_food2.loc[i,'weight_num']=float(re.findall("[-+]?\d*\.\d+|\d+",df_sort_food2.loc[i,'weight'])[0] )  
    except:
      df_sort_food2.loc[i,'weight2']=0
    if df_sort_food2.loc[i,'price_100']==0:
      df_sort_food2.loc[i,'price_100']=df_sort_food2.loc[i,'current_price']/(df_sort_food2.loc[i,'weight2']/100)

  df_sort_food2=post_text(df_sort_food2)
  df_sort_food2 = df_sort_food2.astype({"price_100": float})
#   df_agg = df_sort_food2.groupby(['merchant_name','product'],observed=True)['merchant_name','product','current_price','weight2','weight_num','price_100','clean_image_url'].agg({'current_price':min})
  df_agg =df_sort_food2.loc[df_sort_food2.groupby(['merchant_name','product']).current_price.idxmin()][['merchant_name','product','current_price','weight2','weight_num','price_100','clean_image_url']]
#   df_agg.columns = df_agg.columns.droplevel(0)
  df_agg = df_agg.reset_index()
  df_agg_price_sum=df_agg.groupby(['merchant_name']).agg({'current_price':sum}).rename(index=str, columns={"current_price": "Price_sum"})
  df_agg_price_sum = df_agg_price_sum.reset_index()
  df_agg_price_mean=df_agg[['product','price_100']].groupby(['product']).median().rename(index=str, columns={"price_100": "price_100_median"})
  df_agg_price_mean = df_agg_price_mean.reset_index()
  df_final=df_agg.merge(df_agg_price_sum,on='merchant_name')
  df_final=df_final.merge(df_agg_price_mean,on='product')
  df_final2=df_final[['product','merchant_name']].groupby(['merchant_name']).count()*100/len(df_sort_food2["product"].unique())
  df_final2 = df_final2.rename(columns={"product": "Percentage_list"}).reset_index()
  df_final3=df_final.merge(df_final2, on='merchant_name')
  df_final3=df_final3.sort_values('Percentage_list',ascending=False)
  today = date.today()
  df_final3['snapshot_date']=today
  df_sort_food2['snapshot_date']=today
  return (df_final3,df_sort_food2[['merchant_name','product','current_price','weight2','weight_num','price_100','clean_image_url','labels','ocr_name','name']] )
# (item_list,data)=grocery_list()
# pd.set_option('max_colwidth', 200)
# today = date.today()
# item_list.to_csv('weekly_list_'+str(today)+'.csv')


def main(data, context):
  """Triggered from a message on a Cloud Pub/Sub topic.
  Args:
      data (dict): Event payload.
      context (google.cloud.functions.Context): Metadata for the event.
  """
  try:
    current_time = datetime.datetime.utcnow()
    log_message = Template('Cloud Function was triggered on $time')
    logging.info(log_message.safe_substitute(time=current_time))

    try:
      today = date.today()
      (item_list, item_list2) = grocery_list()

      file_name = 'weekly_list_' + str(today) + '.csv'
      # blob = bucket.blob(bucketFolder + '/' + file_name)
      blob = bucket.blob('historic' + '/' +file_name)
      blob.upload_from_string(item_list2.to_csv(), 'text/csv')

      file_name_current = 'weekly_list.csv'
      # blob = bucket.blob(bucketFolder + '/' + file_name_current)
      blob_current = bucket.blob(file_name_current)
      blob_current.upload_from_string(item_list2.to_csv(), 'text/csv')


    except Exception as error:
      log_message = Template('Query failed due to '
                             '$message.')
      logging.error(log_message.safe_substitute(message=error))

  except Exception as error:
    log_message = Template('$error').substitute(error=error)
    logging.error(log_message)


if __name__ == '__main__':
  main('data', 'context')