import tempfile
import unittest

import json
from flask import current_app as app
import redis
from sqlalchemy import text
from unittest.mock import Mock, patch

from app.main import db
from app.test.base import BaseTestCase
from app.main.lib.shared_models.shared_model import SharedModel
from app.main.lib.shared_models.audio_model import AudioModel
from app.main.model.audio import Audio
import urllib.error
import urllib.request

class SharedModelStub(SharedModel):
  model_key = 'audio'

  def load(self):
    pass

  def respond(self, task):
    return task

first_print = [-248655731, -231870068, -230690420, -482429284, -478234963, -503476625, -520316369, -521361138, 1634511886, 1647109134, 1647046702, 1646940206, 1646924078, -500563482, -496367961, -471202139, -474282347, -476481849, -510101945, -510069497, -526854905, -237050874, -251730922, -251792089, -503463131, -513949140, -513949140, -1587752392, -1250138600, -180474360, -181522936, -194113975, -261353745, -253227346, -189264210, -188938850, -251825010, -251861834, -797121369, 1366287511, 1898902657, 1932452993, 1932452993, 1936651425, 1928253859, -491814237, -487750941, -496401919, -500657663, -500657643, -483876315, -517414355, -534219217, -529853138, -521597906, -524744474, -459335514, -255973226, -255973242, 1908283526, 1925055878, 1929249159, 1392390532, 1383981188, 1378656532, 1915527460, 1915527212, 1915528248, 1903135752, 1885837336, 1894160408, -253321943, -253326037, -262747077, -263193126, -262311942, -159482198, -151365974, -152489301, -152554837, -228052277, -232251189, -231202597, -243569493, -253069157, -257238902, -257242230, -521302374, -529751382, -517430614, -482831830, -483884501, -479492807, -534139591, -534190021, -534124501, -513115153, -479590737, -487980369, -486931793, -487062593, -488087363, -513253323, -529931243, -529865723, -521475067, -521475065, -252982986, -253179866, -260519706, -514274074, -472199258, -493164874, -1564809486, -1561472269, -1569918447, -1574116603, -1574113276, -1557204988, -483728380, -517313481, -528802706, -520549138, -1600584530, -1600453442, -1583800134, -1281875782, -1292339717, -1293328695, -1292907831, -1292969380, -1276199332, -504392116, -533941748, -533945844, -517414116, -517410760, -483794904, -496311256, -496351175, -487962599, -470136709, -1577427462, -1598339078, -1600568581, -1600634279, -1330097415, -1325833495, -1317312771, -1275466019, -1293353515, -1297496649, -1293171465, -1301552649, -1305742569, -1557473769, -1607807481, -1603604985, -1595314665, -1595378138, -1603522266, -1603522330, -1606676314, -1606479681, -262794049, -205121403, -225572412, 1921977028, 1921870556, -225678721, -224598210, -226713298, -231886802, -231829186, -248598194, -265641530, -265582649, -265579009, -265554513, -534022993, -521585489, -525845329, -525849169, -257413713, -207016049, -219666481, -228034567, -232229591, -232196807, -232008440, -244654327, -253043191, -253041137, -1268125170, -1272393170, -1272425938, -1271376338, -1267184018, -1531426306, -1514481442, -1497699122, -1497636658, -1493655458, -1502040008, -1503018952, -1506029256, -1489472728, -1525145048, -1541863896, -1542898072, -1538704408, -456451591, -459404918, -459388790, -172701558, -139158390, -156983158, -152723318, -161046278, -164192018, -164175634]

class TestAudioSimilarityBlueprint(BaseTestCase):
    def setUp(self):
        super().setUp()
        first_print = [-248655731, -231870068, -230690420, -482429284, -478234963, -503476625, -520316369, -521361138, 1634511886, 1647109134, 1647046702, 1646940206, 1646924078, -500563482, -496367961, -471202139, -474282347, -476481849, -510101945, -510069497, -526854905, -237050874, -251730922, -251792089, -503463131, -513949140, -513949140, -1587752392, -1250138600, -180474360, -181522936, -194113975, -261353745, -253227346, -189264210, -188938850, -251825010, -251861834, -797121369, 1366287511, 1898902657, 1932452993, 1932452993, 1936651425, 1928253859, -491814237, -487750941, -496401919, -500657663, -500657643, -483876315, -517414355, -534219217, -529853138, -521597906, -524744474, -459335514, -255973226, -255973242, 1908283526, 1925055878, 1929249159, 1392390532, 1383981188, 1378656532, 1915527460, 1915527212, 1915528248, 1903135752, 1885837336, 1894160408, -253321943, -253326037, -262747077, -263193126, -262311942, -159482198, -151365974, -152489301, -152554837, -228052277, -232251189, -231202597, -243569493, -253069157, -257238902, -257242230, -521302374, -529751382, -517430614, -482831830, -483884501, -479492807, -534139591, -534190021, -534124501, -513115153, -479590737, -487980369, -486931793, -487062593, -488087363, -513253323, -529931243, -529865723, -521475067, -521475065, -252982986, -253179866, -260519706, -514274074, -472199258, -493164874, -1564809486, -1561472269, -1569918447, -1574116603, -1574113276, -1557204988, -483728380, -517313481, -528802706, -520549138, -1600584530, -1600453442, -1583800134, -1281875782, -1292339717, -1293328695, -1292907831, -1292969380, -1276199332, -504392116, -533941748, -533945844, -517414116, -517410760, -483794904, -496311256, -496351175, -487962599, -470136709, -1577427462, -1598339078, -1600568581, -1600634279, -1330097415, -1325833495, -1317312771, -1275466019, -1293353515, -1297496649, -1293171465, -1301552649, -1305742569, -1557473769, -1607807481, -1603604985, -1595314665, -1595378138, -1603522266, -1603522330, -1606676314, -1606479681, -262794049, -205121403, -225572412, 1921977028, 1921870556, -225678721, -224598210, -226713298, -231886802, -231829186, -248598194, -265641530, -265582649, -265579009, -265554513, -534022993, -521585489, -525845329, -525849169, -257413713, -207016049, -219666481, -228034567, -232229591, -232196807, -232008440, -244654327, -253043191, -253041137, -1268125170, -1272393170, -1272425938, -1271376338, -1267184018, -1531426306, -1514481442, -1497699122, -1497636658, -1493655458, -1502040008, -1503018952, -1506029256, -1489472728, -1525145048, -1541863896, -1542898072, -1538704408, -456451591, -459404918, -459388790, -172701558, -139158390, -156983158, -152723318, -161046278, -164192018, -164175634]
        audio = Audio(chromaprint_fingerprint=first_print, doc_id="blah", url="http://blah.com", context=[{"blah": 1}])
        db.session.add(audio)
        db.session.commit()
        self.model = AudioModel('audio')

    def tearDown(self): # done in our pytest fixture after yield
        db.session.remove()
        db.drop_all()

    def test_basic_http_responses_with_doc_id(self):
        url = 'file:///app/app/test/data/test_audio_1.mp3'
        with patch('requests.post') as mock_post_request:
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
                        'url': 'http://example.com/blah.mp3'
                    }
                }
            })
            mock_post_request.return_value = mock_response
            response = self.client.post('/audio/similarity/', data=json.dumps({
                'url': url,
                'doc_id': "1c63abe0-aeb4-4bac-8925-948b69c32d0d",
                'context': {
                    'team_id': 1,
                }
            }), content_type='application/json')
        result = json.loads(response.data.decode())
        self.assertEqual(result['message'], "Message pushed successfully")

    def test_basic_http_responses(self):
        url = 'file:///app/app/test/data/test_audio_1.mp3'
        with patch('requests.post') as mock_post_request:
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
                        'url': 'http://example.com/blah.mp3'
                    }
                }
            })
            mock_post_request.return_value = mock_response
            response = self.client.post('/audio/similarity/', data=json.dumps({
                'url': url,
                'project_media_id': 1,
                'context': {
                    'team_id': 1,
                }
            }), content_type='application/json')
        result = json.loads(response.data.decode())
        self.assertEqual(result['message'], "Message pushed successfully")

    def test_callback_response(self):
        with patch('app.main.lib.similarity.callback_add_item') as mock_callback_add_item:
            with patch('app.main.lib.webhook.Webhook.return_webhook') as mock_post_request:
                mock_post_request.return_value = {'message': 'Message pushed successfully', 'queue': 'audio__Model', 'body': {'callback_url': 'http://alegre:3100/presto/receive/add_item/audio', 'id': "1c63abe0-aeb4-4bac-8925-948b69c32d0d", 'url': 'http://example.com/blah.mp3', 'text': None, 'raw': {'doc_id': "1c63abe0-aeb4-4bac-8925-948b69c32d0d", 'url': 'http://example.com/blah.mp3'}}}
                mock_callback_add_item.return_value = {"requested": {}, "result": {}, "success": True}
                response = self.client.post('/presto/receive/add_item/audio', data=json.dumps({
                    "body": {
                        "id": '123',
                        "callback_url": 'http://0.0.0.0:3100/presto/receive/add_item/audio',
                        "url": 'http://devingaffney.com/files/blah.mp3',
                        "text": None,
                        "raw": {
                            'doc_id': 123,
                            'url': 'http://example.com/files/blah.mp3'
                        },
                        "response": {
                            'hash_value': [-713337002, -1778428074, -1778560170, -1778560650]
                        }
                    }
                }), content_type='application/json')
        result = json.loads(response.data.decode())
        self.assertEqual(sorted(result.keys()), ['action', 'data', 'model_type'])
        self.assertEqual(result["action"], "add_item")
        self.assertEqual(result["model_type"], "audio")
        self.assertEqual(sorted(result["data"].keys()), ["requested", "result", "success"])

    def test_delete_by_doc_id(self):
        url = 'file:///app/app/test/data/test_audio_1.mp3'
        self.model.add({"url": url, 'doc_id': "Y2hlY2stcHJvamVjdF9tZWRpYS01NTQ1NzEtdmlkZW8", "context": {"has_custom_id": True}}).get("body")
        result = self.model.delete({"url": url, 'doc_id': "Y2hlY2stcHJvamVjdF9tZWRpYS01NTQ1NzEtdmlkZW8"})
        self.assertIsInstance(result, dict)
        self.assertEqual(sorted(result.keys()), ['requested', 'result'])
        self.assertEqual(sorted(result['requested'].keys()), ['doc_id', 'url'])
        self.assertEqual(sorted(result['result'].keys()), ['deleted', 'url'])
        #try to delete a item already deleted
        result = self.model.delete({'doc_id': "Y2hlY2stcHJvamVjdF9tZWRpYS01NTQ1NzEtdmlkZW8"})
        self.assertEqual(sorted(result.keys()), ['requested', 'result'])
        self.assertEqual(False, result['result']['deleted'])

    def test_add_by_doc_id(self):
        url = 'file:///app/app/test/data/test_audio_1.mp3'
        result = self.model.add({"url": url, 'doc_id': "Y2hlY2stcHJvamVjdF9tZWRpYS01NTQ1NzEtdmlkZW8", "context": {"has_custom_id": True}})
        self.assertIsInstance(result, dict)
        self.assertEqual(sorted(result.keys()), ['requested', 'result', 'success'])
        self.assertEqual(sorted(result['requested'].keys()), ['context', 'doc_id', 'url'])
        self.assertEqual(sorted(result['result'].keys()), ['url'])

    def test_search_by_doc_id(self):
        url = 'file:///app/app/test/data/test_audio_1.mp3'
        hash_key = "blah"
        audio = Audio(chromaprint_fingerprint=first_print, doc_id="Y2hlY2stcHJvamVjdF9tZWRpYS01NTQ1NzEtdmlkZW8", url=url, context=[{'blah': 1, 'has_custom_id': True, 'project_media_id': 12343}])
        db.session.add(audio)
        db.session.commit()
        with patch('app.main.lib.shared_models.audio_model.AudioModel.get_by_doc_id_or_url', ) as mock_get_by_doc_id_or_url:
            mock_get_by_doc_id_or_url.return_value = audio
            self.model.add({"url": url, 'doc_id': "Y2hlY2stcHJvamVjdF9tZWRpYS01NTQ1NzEtdmlkZW8", "context": {"blah": 1, "has_custom_id": True, 'project_media_id': 12343}}).get("body")
            result = self.model.search({"url": url, 'doc_id': "Y2hlY2stcHJvamVjdF9tZWRpYS01NTQ1NzEtdmlkZW8", "context": {"blah": 1, "has_custom_id": True, 'project_media_id': 12343}})
        self.assertIsInstance(result, dict)
        self.assertEqual(sorted(result["result"][0].keys()), ['chromaprint_fingerprint', 'context', 'doc_id', 'id', 'model', 'score', 'url'])
        self.assertEqual(result["result"][0]['doc_id'], 'Y2hlY2stcHJvamVjdF9tZWRpYS01NTQ1NzEtdmlkZW8')
        self.assertEqual(result["result"][0]['url'], url)
        self.assertEqual(result["result"][0]['context'], [{'blah': 1, 'has_custom_id': True, 'project_media_id': 12343}])

    def test_delete(self):
        url = 'file:///app/app/test/data/test_audio_1.mp3'
        self.model.add({"url": url, "project_media_id": 1, "raw": {"context": {'blah': 1, 'project_media_id': 1}}})
        result = self.model.delete({"url": url, "project_media_id": 1, "context": {'blah': 1, 'project_media_id': 1}})
        self.assertIsInstance(result, dict)
        self.assertEqual(sorted(result.keys()), ['requested', 'result'])
        self.assertEqual(sorted(result['requested'].keys()), ['context', 'project_media_id', 'url'])
        self.assertEqual(sorted(result['result'].keys()), ['deleted', 'url'])

    def test_add(self):
        url = 'file:///app/app/test/data/test_audio_1.mp3'
        result = self.model.add({"url": url, "project_media_id": 1})
        self.assertIsInstance(result, dict)
        self.assertEqual(sorted(result.keys()), ['requested', 'result', 'success'])
        self.assertEqual(sorted(result['requested'].keys()), ['project_media_id', 'url'])
        self.assertEqual(sorted(result['result'].keys()), ['url'])

    def test_add_wav(self):
        url = 'file:///app/app/test/data/sample.wav'
        result = self.model.add({"url": url, "project_media_id": 1})
        self.assertIsInstance(result, dict)
        self.assertEqual(sorted(result.keys()), ['requested', 'result', 'success'])
        self.assertEqual(sorted(result['requested'].keys()), ['project_media_id', 'url'])
        self.assertEqual(sorted(result['result'].keys()), ['url'])

    def test_search(self):
        url = 'file:///app/app/test/data/test_audio_1.mp3'
        hash_key = "blah"
        audio = Audio(chromaprint_fingerprint=first_print, doc_id="Y2hlY2stcHJvamVjdF9tZWRpYS01NTQ1NzEtdmlkZW8", url=url, context=[{'blah': 1, 'has_custom_id': True, 'project_media_id': 12343}])
        db.session.add(audio)
        db.session.commit()
        with patch('app.main.lib.shared_models.audio_model.AudioModel.get_by_doc_id_or_url', ) as mock_get_by_doc_id_or_url:
            mock_get_by_doc_id_or_url.return_value = audio
            self.model.add({"doc_id": "Y2hlY2stcHJvamVjdF9tZWRpYS01NTQ1NzEtdmlkZW8", "url": url, "project_media_id": 1, "context": {"blah": 1, 'project_media_id': 12343}}).get("body")
            result = self.model.search({"url": url, "project_media_id": 1, "context": {"blah": 1, 'project_media_id': 12343}})
        self.assertIsInstance(result, dict)
        self.assertEqual(sorted(result["result"][0].keys()), ['chromaprint_fingerprint', 'context', 'doc_id', 'id', 'model', 'score', 'url'])
        self.assertEqual(result["result"][0]['doc_id'], 'blah')
        self.assertEqual(result["result"][0]['url'], 'http://blah.com')
        self.assertEqual(result["result"][0]['context'], [{'blah': 1}])

    def test_respond_delete(self):
        url = 'file:///app/app/test/data/test_audio_1.mp3'
        self.model.add({"url": url, "id": 1, "raw": {"context": {'blah': 1, 'project_media_id': 12342}}})
        result = self.model.respond({"url": url, "project_media_id": 1, "command": "delete", "context": {'blah': 1, 'project_media_id': 12342}})
        self.assertIsInstance(result, dict)
        self.assertEqual(sorted(result.keys()), ['requested', 'result'])
        self.assertEqual(sorted(result['requested'].keys()), ['command', 'context', 'project_media_id', 'url'])
        self.assertEqual(sorted(result['result'].keys()), ['deleted', 'url'])

    def test_respond_add(self):
        url = 'file:///app/app/test/data/test_audio_1.mp3'
        result = self.model.respond({"body": {"url": url, "project_media_id": 1}, "command": "add"})
        self.assertIsInstance(result, dict)
        self.assertEqual(sorted(result.keys()), ['requested', 'result', 'success'])
        self.assertEqual(sorted(result['requested'].keys()), ['project_media_id', 'url'])
        self.assertEqual(sorted(result['result'].keys()), ['url'])

    def test_respond_search(self):
        url = 'file:///app/app/test/data/test_audio_1.mp3'
        hash_key = "blah"
        audio = Audio(chromaprint_fingerprint=first_print, doc_id="Y2hlY2stcHJvamVjdF9tZWRpYS01NTQ1NzEtdmlkZW8", url=url, context=[{'blah': 1, 'has_custom_id': True, 'project_media_id': 12343}])
        db.session.add(audio)
        db.session.commit()
        with patch('app.main.lib.shared_models.audio_model.AudioModel.get_by_doc_id_or_url', ) as mock_get_by_doc_id_or_url:
            mock_get_by_doc_id_or_url.return_value = audio
            self.model.respond({"command": "add", "body": {"threshold": 0.0, "doc_id": "Y2hlY2stcHJvamVjdF9tZWRpYS01NTQ1NzEtdmlkZW8", "url": url, "project_media_id": 1, "context": {"blah": 1, 'project_media_id': 12343}}})
            result = self.model.respond({"url": url, "project_media_id": 1, "command": "search", "context": {"blah": 1, 'project_media_id': 12343}})
        self.assertEqual(sorted(result["result"][0].keys()), ['chromaprint_fingerprint', 'context', 'doc_id', 'id', 'model', 'score', 'url'])
        self.assertEqual(result["result"][0]['doc_id'], 'blah')
        self.assertEqual(result["result"][0]['url'], 'http://blah.com')
        self.assertEqual(result["result"][0]['context'], [{'blah': 1}])


    def test_audio_model_search_by_context(self):
        url = 'file:///app/app/test/data/test_audio_1.mp3'
        context = [{'blah': 15, 'has_custom_id': True, 'project_media_id': 12343}]
        audio = Audio(chromaprint_fingerprint=first_print, doc_id="blah332", url=url, context=context)
        db.session.add(audio)
        db.session.commit()
        second_print = [-248655731, -231870068, -230690420, -482429284, -478234963, -503476625, -520316369, -521361138, 1634511886, 1647109134, 1647046702, 1646940206, 1646924078, -500563482, -496367961, -471202139, -474282347, -476481849, -510101945, -510069497, -526854905, -237050874, -251730922, -251792089, -503463131, -513949140, -513949140, -1587752392, -1250138600, -180474360, -181522936, -194113975, -261353745, -253227346, -189264210, -188938850, -251825010, -251861834, -797121369, 1366287511, 1898902657, 1932452993, 1932452993, 1936651425, 1928253859, -491814237, -487750941, -496401919, -500657663, -500657643, -483876315, -517414355, -534219217, -529853138, -521597906, -524744474, -459335514, -255973226, -255973242, 1908283526, 1925055878, 1929249159, 1392390532, 1383981188, 1378656532, 1915527460, 1915527212, 1915528248, 1903135752, 1885837336, 1894160408, -253321943, -253326037, -262747077, -263193126, -262311942, -159482198, -151365974, -152489301, -152554837, -228052277, -232251189, -231202597, -243569493, -253069157, -257238902, -257242230, -521302374, -529751382, -517430614, -482831830, -483884501, -479492807, -534139591, -534190021, -534124501, -513115153, -479590737, -487980369, -486931793, -487062593, -488087363, -513253323, -529931243, -529865723, -521475067, -521475065, -252982986, -253179866, -260519706, -514274074, -472199258, -493164874, -1564809486, -1561472269, -1569918447, -1574116603, -1574113276, -1557204988, -483728380, -517313481, -528802706, -520549138, -1600584530, -1600453442, -1583800134, -1281875782, -1292339717, -1293328695, -1292907831, -1292969380, -1276199332, -504392116, -533941748, -533945844, -517414116, -517410760, -483794904, -496311256, -496351175, -487962599, -470136709, -1577427462, -1598339078, -1600568581, -1600634279, -1330097415, -1325833495, -1317312771, -1275466019, -1293353515, -1297496649, -1293171465, -1301552649, -1305742569, -1557473769, -1607807481, -1603604985, -1595314665, -1595378138, -1603522266, -1603522330, -1606676314, -1606479681, -262794049, -205121403, -225572412, 1921977028, 1921870556, -225678721, -224598210, -226713298, -231886802, -231829186, -248598194, -265641530, -265582649, -265579009, -265554513, -534022993, -521585489, -525845329, -525849169, -257413713, -207016049, -219666481, -228034567, -232229591, -232196807, -232008440, -244654327, -253043191, -253041137, -1268125170, -1272393170, -1272425938, -1271376338, -1267184018, -1531426306, -1514481442, -1497699122, -1497636658, -1493655458, -1502040008, -1503018952, -1506029256, -1489472728, -1525145048, -1541863896, -1542898072, -1538704408, -456451591, -459404918, -459388790, -172701558, -139158390, -156983158, -152723318, -161046278, -164192018, -164175634]
        results = self.model.search_by_hash_value(second_print, 0.0, {"blah": 15})
        self.assertIsInstance(results[0], dict)
        self.assertEqual(sorted(results[0].keys()), ['chromaprint_fingerprint', 'context', 'doc_id', 'id', 'model', 'score', 'url'])
        self.assertEqual(results[0]['doc_id'], 'blah332')
        self.assertEqual(results[0]['url'], url)
        self.assertEqual(results[0]['score'], 1.0)
        self.assertEqual(results[0]['context'], context)

    def test_audio_model_confirmed_match(self):
        url1 = 'file:///app/app/test/data/test_audio_1.mp3'
        url2 = 'file:///app/app/test/data/test_audio_2.mp3'
        audio2 = Audio(chromaprint_fingerprint=first_print, doc_id="second_case", url=url2, context=[{'blah': 2, 'has_custom_id': True, 'project_media_id': 457}])
        #db.session.add(audio)
        db.session.add(audio2)
        db.session.commit()
        result = self.model.search({"body": {"url": url1, "raw": {"context": {"blah": 2}}, "threshold": 0.9}, "response": {"hash_value": [e-1 for e in first_print]}})#.get("body")
        second_case = [e for e in result["result"] if e["url"] == url2]
        self.assertGreater(len(second_case),0)
        second_case = second_case[0]
        self.assertIsInstance(second_case, dict)
        self.assertEqual(sorted(second_case.keys()), ['chromaprint_fingerprint', 'context', 'doc_id', 'id', 'model', 'score', 'url'])
        self.assertEqual(second_case['doc_id'], 'second_case')
        self.assertEqual(second_case['url'], url2)
        self.assertEqual(second_case['context'], [{'blah': 2, 'has_custom_id': True, 'project_media_id': 457}])
        self.assertGreater(second_case['score'], 0.90)

    def test_audio_model_confirmed_no_match(self):
        url1 = 'file:///app/app/test/data/test.mp3'
        url2 = 'file:///app/app/test/data/no_match_audio.mp3'
        audio2 = Audio(chromaprint_fingerprint=first_print, doc_id="second_case_no_match", url=url2, context=[{'blah': 3, 'has_custom_id': True, 'project_media_id': 1457}])
        #db.session.add(audio)
        db.session.add(audio2)
        db.session.commit()
        result = self.model.search({"body": {"url": url1, "raw": {"context": {"blah": 3}}}, "response": {"hash_value": [1,2,3]}})
        second_case = [e for e in result["result"] if e["url"] == url2][0]
        self.assertIsInstance(second_case, dict)
        self.assertEqual(sorted(second_case.keys()), ['chromaprint_fingerprint', 'context', 'doc_id', 'id', 'model', 'score', 'url'])
        self.assertEqual(second_case['doc_id'], 'second_case_no_match')
        self.assertEqual(second_case['url'], url2)
        self.assertEqual(second_case['context'], [{'blah': 3, 'has_custom_id': True, 'project_media_id': 1457}])
        self.assertLessEqual(second_case['score'], 0.1)

    def test_search_by_context(self):
        url = 'file:///app/app/test/data/test_audio_1.mp3'
        hash_key = "blah"
        audio = Audio(chromaprint_fingerprint=first_print, doc_id="blah32", url="http://blah.com", context=[{'blah': 16, 'has_custom_id': True, 'project_media_id': 12343}])
        db.session.add(audio)
        db.session.commit()
        results = self.model.search_by_context({"blah": 16})
        self.assertEqual(results[0]['doc_id'], 'blah32')
        self.assertEqual(results[0]['url'], "http://blah.com")
        self.assertEqual(results[0]['context'], [{'blah': 16, 'has_custom_id': True, 'project_media_id': 12343}])
        results = self.model.search_by_context({"blah": 2})
        self.assertEqual(results, [])

    def test_handle_save_error(self):
        with patch('app.main.lib.shared_models.audio_model.AudioModel.save', ) as mock:
            mock.return_value = False
            url = 'file:///app/app/test/data/test_audio_1.mp3'
            result = self.model.add({"url": url, 'doc_id': "Y2hlY2stcHJvamVjdF9tZWRpYS01NTQ1NzEtdmlkZW8", "context": {"has_custom_id": True}})
            self.assertIsInstance(result, dict)
            self.assertEqual(False, result['success'])

    def test_handle_http_error(self):
        with patch('app.main.lib.shared_models.audio_model.AudioModel.save', ) as mock:
            url = 'file:///app/app/test/data/test_audio_1.mp3'
            mock.side_effect = urllib.error.HTTPError(url, 420, "HTTP ERROR HAPPENED", None, None)
            result = self.model.add({"url": url, 'doc_id': "Y2hlY2stcHJvamVjdF9tZWRpYS01NTQ1NzEtdmlkZW8", "context": {"has_custom_id": True}})
            self.assertIsInstance(result, dict)
            self.assertEqual(False, result['success'])

if __name__ == '__main__':
  unittest.main()
