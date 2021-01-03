from pymongo import MongoClient
from pprint import pprint

client = MongoClient('127.0.0.1', 27017)

db = client['insta']
instagram = db.instagram

user = 'lisjonok4'

#Написать запрос к базе, который вернет список подписчиков только указанного пользователя

for subscriber in instagram.find({'subscription_username':user},{'subscriber_id':1,'subscriber_username':1,'_id':0}):
    pprint(subscriber)

#Написать запрос к базе, который вернет список профилей, на кого подписан указанный пользователь

for subscription in instagram.find({'subscriber_username':user},{'subscription_id':1,'subscription_username':1,'_id':0}):
    pprint(subscription)