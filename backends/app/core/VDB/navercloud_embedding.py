# -*- coding: utf-8 -*-

import http.client
import json
from dotenv import load_dotenv
import os
load_dotenv()

class NaverCloudEmbeddings:
    def __init__(self, host = None, api_key = None, request_id = None):
        self._host = os.getenv('NAVERCLOUD_HOST2') if not host else host
        self._api_key = os.getenv('NAVER_CLOVA_API_KEY2') if not api_key else api_key
        self._request_id = request_id

    def _send_request(self, completion_request):
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Authorization': self._api_key,
        }
        if self._request_id:
            headers['X-NCP-CLOVASTUDIO-REQUEST-ID'] = self._request_id

        conn = http.client.HTTPSConnection(self._host)
        conn.request('POST', '/v1/api-tools/embedding/v2', json.dumps(completion_request), headers)
        response = conn.getresponse()
        result = json.loads(response.read().decode(encoding='utf-8'))
        conn.close()
        return result

    def embed_query(self, text):
        request = {'text' : text }
        res = self._send_request(request)
        if res['status']['code'] == '20000':
            return res['result']
        else:
            return {'err_msg': 'Error ' + f"{res['status']['code']}"}
