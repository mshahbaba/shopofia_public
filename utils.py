import numpy as np
import re
import requests
from google.cloud.vision import types
from PIL import Image
from google.cloud import vision
import io
import inflect


def post_text(data):
    pack = ['ea.', 'each', 'ea', 'EACH', 'EA.', 'EA']
    LB = ['/lb', 'lb', 'LB', '/LB']
    KG = ['/kg', 'kg', 'KG', '/KG']
    G = ['/100 g', '/100g', '/100G', '/100 G']
    for i in data.index:
        if data.loc[i, 'post_price_text'] in pack:
            data.loc[i, 'weight_num'] = 1
        #       data.loc[i,'price_100']=float('Inf')
        if data.loc[i, 'post_price_text'] in LB:
            data.loc[i, 'weight_num'] = 0
            data.loc[i, 'price_100'] = data.loc[i, 'current_price'] / 4.53
        if data.loc[i, 'post_price_text'] in KG:
            data.loc[i, 'weight_num'] = 0
            data.loc[i, 'price_100'] = data.loc[i, 'current_price'] / 10
        if data.loc[i, 'post_price_text'] in G:
            data.loc[i, 'weight_num'] = 0
            data.loc[i, 'price_100'] = data.loc[i, 'current_price']
    return data


def right_item(weight,product):
    r=weight
    D=np.array(r[2][:])
    try:
      o=0
      list2=list(map(lambda x:x.lower(),list(D[:,0])))
      list1=list(map(lambda x:x.lower(),list(r[0])))
      if p.plural(product.lower()) in list2:
        prod=p.plural(product).lower()
      if product.lower() in list2:
        prod=product.lower()
      try:
        x=list2.index(prod)
      except:
        x=0
        o=1
      if len(r[0])>1:
        while o==0 and x<=len(list2)-2:
          x+=1
          if list2[x] in list1:
            o=1
        if len(r[0])==1 or(o==0):
          x=0
        out=list2[x]
      if len(r[0])==1:
        out=list1[0]
      if len(r[0])==0:
        out='NaN'
    except:
      out='NaN'
    return out


def Weight(name,product):
    p = inflect.engine()
    pattern1 = re.compile(r'((?:[0-9]*\s*Pack)'
      r'|(?:[0-9.]+/*\s*/*(?:g|G|KG|kG|Kg|K9|k9|kg|ML|mL|LB|lb|lB|Lb|L|oz)\b))' , re.IGNORECASE)
    pattern2 = re.compile(r'('+str(p.plural(product))
                        +r'|'  +str(p.singular_noun(product))
                        +r'|' + str(product) +r')', re.IGNORECASE)

    pattern3 = re.compile(r'('+str(p.plural(product))
    +r'|' + str(product)+r'|((?:[0-9]*\s*Pack)'
      r'|(?:[0-9.]+/*\s*(?:g|G|KG|kG|Kg|K9|k9|kg|ML|mL|LB|lb|lB|Lb|L|oz)\b)))'
                        , re.IGNORECASE)
    return (re.findall(pattern1, name),re.findall(pattern2, name),re.findall(pattern3, name))

def search(query, postal_code, locale):
    BASE_URL = 'https://flipp.com'
    BACKEND_URL = 'https://backflipp.wishabi.com/flipp'
    SEARCH_URL = '%s/items/search' % BACKEND_URL
    ITEM_URL = '%s/items/' % BACKEND_URL

    data = requests.get(
        SEARCH_URL,
        params = {
            'q': query,
            'postal_code': postal_code,
            'locale':locale
        }
    ).json()

    return [ x for x in data.get('items')]


def Labeled_image(url):
    # Instantiates a client
    try:
      client = vision.ImageAnnotatorClient()
      data = requests.get(url).content
      image = types.Image(content=data)
      img = Image.open(io.BytesIO(data))
      response = client.label_detection(image=image)
      labels = response.label_annotations
      Label_img = list()
      #   plt.imshow(img)
      #   plt.show()
      for label in labels:
          Label_img.append(label.description)
    except:
      Label_img=['unidentified']
    return Label_img


# OCR flyers for weight analysis
def detect_text_url(uri):
    try:
      """Detects text in the file located in Google Cloud Storage or on the Web.
      """
      client = vision.ImageAnnotatorClient()
      image = vision.types.Image()
      image.source.image_uri = uri

      response = client.text_detection(image=image)
      texts = response.text_annotations
    #     print('Texts:')
      return texts[0].description
    except:
      return 'error'
