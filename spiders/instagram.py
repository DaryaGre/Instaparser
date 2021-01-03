import scrapy
from scrapy.http import HtmlResponse
import re
import json
from urllib.parse import urlencode
from copy import deepcopy
from instaparser.items import InstaparserItem

class InstagramSpider(scrapy.Spider):
    name = 'instagram'
    allowed_domains = ['instagram.com']
    start_urls = ['https://www.instagram.com/']

    inst_login_link = 'https://www.instagram.com/accounts/login/ajax/'
    inst_login = 'redlisa2020'
    inst_password = '#PWD_INSTAGRAM_BROWSER:10:1609518573:AZdQAJDHcmp2GycJ2wA4KGXjBTVrn2brvnSoP1PvwvBehI8I3GOT/va6njUG/ZqaP4fxGhezKLjTSAB9JF5GHbZjTZMfKprNpQlY5+uq0IAYHcpbxwzFtyQ4qkClSOu+FdngmNqmm114fS19'

    parse_users = ['lisjonok4', 'brightangel93']
    graphql_url = 'https://www.instagram.com/graphql/query/?'
    #подписчики
    subscriber_hash = 'c76146de99bb02f6415203be841dd25a'
    #подписки
    subscription_hash ='d04b0a864b4b54837c0d870b0e77e076'

    def parse(self, response:HtmlResponse):
        csrf_token = self.fetch_csrf_token(response.text)
        yield scrapy.FormRequest(
            self.inst_login_link,
            method='POST',
            callback= self.user_login,
            formdata={'username': self.inst_login, 'enc_password':self.inst_password},
            headers= {'X-CSRFToken':csrf_token}
        )

    def user_login(self, response:HtmlResponse):
        j_data = response.json()
        if j_data['authenticated']:
            for parse_user in self.parse_users:
                yield response.follow(
                    f'/{parse_user}',
                    callback= self.user_data_parse,
                    cb_kwargs={'username':parse_user}
                )

    def user_data_parse(self, response:HtmlResponse, username):
        user_id = self.fetch_user_id(response.text, username)
        variables = {'id': user_id,"include_reel":'true',"fetch_mutual":'false', 'first': 12}

        url_posts = f'{self.graphql_url}query_hash={self.subscriber_hash}&{urlencode(variables)}'
        yield response.follow(
            url_posts,
            callback=self.user_subscriber_parse,
            cb_kwargs={'username':username,
                       'user_id': user_id,
                       'variables': deepcopy(variables)}
        )


        url_posts = f'{self.graphql_url}query_hash={self.subscription_hash}&{urlencode(variables)}'
        yield response.follow(
            url_posts,
            callback=self.user_subscription_parse,
            cb_kwargs={'username': username,
                       'user_id': user_id,
                       'variables': deepcopy(variables)}
        )

    def user_subscription_parse(self, response:HtmlResponse, username, user_id, variables):
        j_data = response.json()
        page_info = j_data.get('data').get('user').get('edge_follow').get('page_info')
        if page_info.get('has_next_page'):
            variables['after'] = page_info.get('end_cursor')

            url_posts = f'{self.graphql_url}query_hash={self.subscription_hash}&{urlencode(variables)}'
            yield response.follow(
                url_posts,
                callback=self.user_subscription_parse,
                cb_kwargs={'username': username,
                           'user_id': user_id,
                           'variables': deepcopy(variables)}
            )
        posts = j_data.get('data').get('user').get('edge_follow').get('edges')
        for post in posts:
            item = InstaparserItem(
                user_id = user_id,
                subscription_id=post.get('node').get('id'),
                subscription_username=post.get('node').get('username'),
                subscriber_id=user_id,
                subscriber_username=username,
                full_name=post.get('node').get('full_name'),
                profile_pic_url=post.get('node').get('profile_pic_url'),
                post_data=post.get('node')
            )
            yield item

    def user_subscriber_parse(self, response:HtmlResponse, username, user_id, variables):
        j_data = response.json()
        page_info = j_data.get('data').get('user').get('edge_followed_by').get('page_info')
        if page_info.get('has_next_page'):
            variables['after'] = page_info.get('end_cursor')

            url_posts = f'{self.graphql_url}query_hash={self.subscriber_hash}&{urlencode(variables)}'
            yield response.follow(
                url_posts,
                callback=self.user_subscriber_parse,
                cb_kwargs={'username': username,
                           'user_id': user_id,
                           'variables': deepcopy(variables)}
            )

        posts = j_data.get('data').get('user').get('edge_followed_by').get('edges')
        for post in posts:
            item = InstaparserItem(
                user_id=user_id,
                subscription_id = user_id,
                subscription_username = username,
                subscriber_id = post.get('node').get('id'),
                subscriber_username= post.get('node').get('username'),
                full_name = post.get('node').get('full_name'),
                profile_pic_url = post.get('node').get('profile_pic_url'),
                post_data = post.get('node')
            )
            yield item


    # #Получаем токен для авторизации
    def fetch_csrf_token(self, text):
        matched = re.search('\"csrf_token\":\"\\w+\"', text).group()
        return matched.split(':').pop().replace(r'"', '')


    # # Получаем id желаемого пользователя
    def fetch_user_id(self, text, username):
        matched = re.search(
            '{\"id\":\"\\d+\",\"username\":\"%s\"}' % username, text
        ).group()
        return json.loads(matched).get('id')