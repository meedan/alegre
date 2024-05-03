import unittest
import json
from opensearchpy import helpers, OpenSearch, TransportError
from flask import current_app as app
from unittest.mock import Mock, patch
import numpy as np
import redis

from app.main import db
from app.test.base import BaseTestCase
from app.main.lib.shared_models.shared_model import SharedModel
from unittest.mock import patch
from app.main.model.audio import Audio
from app.main.lib.shared_models.audio_model import AudioModel
class TestAsyncSimilarityBlueprint(BaseTestCase):
    def setUp(self):
        super().setUp()
        first_print = [-248655731, -231870068, -230690420, -482429284, -478234963, -503476625, -520316369, -521361138, 1634511886, 1647109134, 1647046702, 1646940206, 1646924078, -500563482, -496367961, -471202139, -474282347, -476481849, -510101945, -510069497, -526854905, -237050874, -251730922, -251792089, -503463131, -513949140, -513949140, -1587752392, -1250138600, -180474360, -181522936, -194113975, -261353745, -253227346, -189264210, -188938850, -251825010, -251861834, -797121369, 1366287511, 1898902657, 1932452993, 1932452993, 1936651425, 1928253859, -491814237, -487750941, -496401919, -500657663, -500657643, -483876315, -517414355, -534219217, -529853138, -521597906, -524744474, -459335514, -255973226, -255973242, 1908283526, 1925055878, 1929249159, 1392390532, 1383981188, 1378656532, 1915527460, 1915527212, 1915528248, 1903135752, 1885837336, 1894160408, -253321943, -253326037, -262747077, -263193126, -262311942, -159482198, -151365974, -152489301, -152554837, -228052277, -232251189, -231202597, -243569493, -253069157, -257238902, -257242230, -521302374, -529751382, -517430614, -482831830, -483884501, -479492807, -534139591, -534190021, -534124501, -513115153, -479590737, -487980369, -486931793, -487062593, -488087363, -513253323, -529931243, -529865723, -521475067, -521475065, -252982986, -253179866, -260519706, -514274074, -472199258, -493164874, -1564809486, -1561472269, -1569918447, -1574116603, -1574113276, -1557204988, -483728380, -517313481, -528802706, -520549138, -1600584530, -1600453442, -1583800134, -1281875782, -1292339717, -1293328695, -1292907831, -1292969380, -1276199332, -504392116, -533941748, -533945844, -517414116, -517410760, -483794904, -496311256, -496351175, -487962599, -470136709, -1577427462, -1598339078, -1600568581, -1600634279, -1330097415, -1325833495, -1317312771, -1275466019, -1293353515, -1297496649, -1293171465, -1301552649, -1305742569, -1557473769, -1607807481, -1603604985, -1595314665, -1595378138, -1603522266, -1603522330, -1606676314, -1606479681, -262794049, -205121403, -225572412, 1921977028, 1921870556, -225678721, -224598210, -226713298, -231886802, -231829186, -248598194, -265641530, -265582649, -265579009, -265554513, -534022993, -521585489, -525845329, -525849169, -257413713, -207016049, -219666481, -228034567, -232229591, -232196807, -232008440, -244654327, -253043191, -253041137, -1268125170, -1272393170, -1272425938, -1271376338, -1267184018, -1531426306, -1514481442, -1497699122, -1497636658, -1493655458, -1502040008, -1503018952, -1506029256, -1489472728, -1525145048, -1541863896, -1542898072, -1538704408, -456451591, -459404918, -459388790, -172701558, -139158390, -156983158, -152723318, -161046278, -164192018, -164175634]
        self.model = AudioModel('audio')

    def tearDown(self): # done in our pytest fixture after yield
        db.session.remove()
        db.drop_all()

    def test_audio_basic_http_responses_with_doc_id(self):
        url = 'file:///app/app/test/data/test_audio_1.mp3'
        with patch('requests.post') as mock_post_request:
            r = redis.Redis(host=app.config['REDIS_HOST'], port=app.config['REDIS_PORT'], db=app.config['REDIS_DATABASE'])
            r.delete(f"audio_1c63abe0-aeb4-4bac-8925-948b69c32d0d")
            r.lpush(f"audio_1c63abe0-aeb4-4bac-8925-948b69c32d0d", json.dumps({"response": {"hash_value": [1,2,3]}}))
            mock_response = Mock()
            mock_response.text = json.dumps({
                'message': 'Message pushed successfully',
                'queue': 'audio__Model',
                'body': {
                    'callback_url': 'http://alegre:3100/presto/receive/add_item/audio',
                    'id': "1c63abe0-aeb4-4bac-8925-948b69c32d0d",
                    'url': 'http://example.com/blah.mp3',
                    'text': None,
                    'raw': {
                        'doc_id': "1c63abe0-aeb4-4bac-8925-948b69c32d0d",
                        'callback_url': 'http://example.com/search_results',
                        'final_task': 'search',
                        'url': 'http://example.com/blah.mp3'
                    }
                }
            })
            mock_post_request.return_value = mock_response
            response = self.client.post('/similarity/async/audio', data=json.dumps({
                'url': url,
                'doc_id': "1c63abe0-aeb4-4bac-8925-948b69c32d0d",
                'callback_url': 'http://example.com/search_results',
                'context': {
                    'team_id': 1,
                }
            }), content_type='application/json')
        result = json.loads(response.data.decode())
        self.assertEqual(result['message'], "Message pushed successfully")

    def test_audio_basic_http_responses(self):
        url = 'file:///app/app/test/data/test_audio_1.mp3'
        with patch('requests.post') as mock_post_request:
            r = redis.Redis(host=app.config['REDIS_HOST'], port=app.config['REDIS_PORT'], db=app.config['REDIS_DATABASE'])
            r.delete(f"audio_1c63abe0-aeb4-4bac-8925-948b69c32d0d")
            r.lpush(f"audio_1c63abe0-aeb4-4bac-8925-948b69c32d0d", json.dumps({"response": {"hash_value": [1,2,3]}}))
            mock_response = Mock()
            mock_response.text = json.dumps({
                'message': 'Message pushed successfully',
                'queue': 'audio__Model',
                'body': {
                    'callback_url': 'http://alegre:3100/presto/receive/add_item/audio',
                    'id': "1c63abe0-aeb4-4bac-8925-948b69c32d0d",
                    'url': 'http://example.com/blah.mp3',
                    'text': None,
                    'raw': {
                        'doc_id': "1c63abe0-aeb4-4bac-8925-948b69c32d0d",
                        'callback_url': 'http://example.com/search_results',
                        'final_task': 'search',
                        'url': 'http://example.com/blah.mp3'
                    }
                }
            })
            mock_post_request.return_value = mock_response
            response = self.client.post('/similarity/async/audio', data=json.dumps({
                'url': url,
                'callback_url': 'http://example.com/search_results',
                'project_media_id': 1,
                'context': {
                    'team_id': 1,
                }
            }), content_type='application/json')
        result = json.loads(response.data.decode())
        self.assertEqual(result['message'], "Message pushed successfully")

if __name__ == '__main__':
    unittest.main()