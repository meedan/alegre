import tempfile
import unittest
import json
from flask import current_app as app
import redis
from sqlalchemy import text
from unittest.mock import patch
import numpy as np
from app.main import db
from app.test.base import BaseTestCase
from app.main.lib.shared_models.shared_model import SharedModel
from app.main.lib.shared_models.video_model import VideoModel
IDENTICAL_HASH_VALUE = [-357.382354736328, 61.048038482666, 106.911338806152, 4.53206300735474, 99.7181549072266, -122.696632385254, 90.2344512939453, -119.207061767578, 84.9968948364258, -49.2294120788574, 35.1557846069336, -25.3716983795166, 15.0641832351685, -17.8254489898682, 34.9035758972168, -6.47979640960693, 119.227195739746, -46.2882423400879, -89.7401275634766, 6.94534063339233, -3.48892426490784, 16.7885608673096, -11.1589050292969, -15.4971990585327, -57.6075325012207, 5.88119840621948, 6.79322004318237, -12.0596580505371, 32.6723480224609, -17.3841667175293, 7.32003307342529, -1.60732471942902, 37.3134460449219, -49.6821479797363, 3.16386246681213, 18.7570724487305, 19.2003955841064, 36.1411476135254, -25.3016891479492, 21.4762344360352, -53.9192771911621, 1.74421346187592, 1.8689296245575, 3.48494839668274, 7.58257722854614, -10.1852722167969, -21.4605026245117, -5.93952941894531, 28.7332611083984, 12.2764663696289, 2.27048063278198, 18.9670085906982, 6.58284521102905, -10.1895627975464, -1.45506489276886, 20.8668327331543, -29.3482894897461, -22.9505290985107, -16.6381454467773, 3.68354225158691, -11.8042325973511, 7.93514776229858, -8.90903186798096, -2.18456339836121, 28.8004131317139, -8.79352378845215, -12.95068359375, -25.3456897735596, -13.4734983444214, -15.5795345306396, 12.3176641464233, -31.7205200195312, -18.4244060516357, -14.4510135650635, 0.768076479434967, 3.26324367523193, -7.05787038803101, -0.756913006305695, 6.47749042510986, 5.86581134796143, 11.7950420379639, -36.9168281555176, -3.98424053192139, 7.34958124160767, 0.122880347073078, -16.7488536834717, -15.0474987030029, -6.08682537078857, -12.6005115509033, 20.4392490386963, 23.1139469146729, -18.9848041534424, -9.89257144927979, 4.92085599899292, 14.6994066238403, 6.72391414642334, 43.6988983154297, -1.05358636379242, -41.5565872192383, 19.757568359375, -11.1086597442627, -11.0476264953613, -4.53783512115479, -6.30579423904419, 20.1801376342773, 9.87284660339355, -17.9698638916016, -25.7574596405029, 7.81379461288452, 10.0896759033203, 12.6637935638428, 4.79370164871216, -26.2449569702148, 58.4881858825684, -0.520525693893433, -18.7338981628418, 4.31249761581421, -11.0616655349731, 13.696457862854, -8.0511531829834, 14.6818885803223, -4.58296680450439, -3.85626316070557, 4.19312000274658, 15.5130825042725, 4.64683675765991, -7.18403959274292, -5.00755500793457, -19.029390335083, 38.5054244995117, 12.7239408493042, -16.3320198059082, 9.53040313720703, -9.63095378875732, -0.239765807986259, -2.83060336112976, -7.36025762557983, 21.5998783111572, 4.33530187606812, 4.86100292205811, 13.8889055252075, -12.2024669647217, -15.6399097442627, -1.30975329875946, 8.48544025421143, -1.31408584117889, 16.5008811950684, -10.7163915634155, -8.02544116973877, 14.9179725646973, -10.5991239547729, 3.89694094657898, 1.27230226993561, 6.77095222473145, -13.1522569656372, 3.77005815505981, -3.11301875114441, -5.86515092849731, -0.557926952838898, -2.92413353919983, 4.94868564605713, -9.76015090942383, -9.56889533996582, 12.5644330978394, -11.9232482910156, -3.30231046676636, 18.8015651702881, -3.40290188789368, -0.297612965106964, 2.73867917060852, -0.725655019283295, -3.39274978637695, 2.64247393608093, 0.927119731903076, -4.89454078674316, 0.778967142105103, -5.48416137695312, -6.98389768600464, 3.6161949634552, -9.40504932403564, -3.72525453567505, 13.4419946670532, 1.94832515716553, 2.40333938598633, -0.385334700345993, -2.61944508552551, 1.72993063926697, 3.236172914505, 2.60505723953247, -2.97915983200073, 3.77850818634033, 0.810816586017609, -0.101192250847816, -2.86220550537109, 0.795464992523193, -22.8118228912354, -7.42093181610107, 0.386918872594833, 6.35350561141968, 14.4288721084595, -2.50911927223206, -0.139989897608757, 3.32883644104004, -0.768213033676147, 0.275245815515518, 13.7912817001343, 2.50477933883667, -1.38079535961151, 1.63635587692261, 13.9923706054688, 7.89688777923584, -8.50043201446533, -16.956356048584, 3.38828921318054, 0.453727930784225, -5.00158357620239, 12.1938104629517, -1.00542330741882, -5.93750762939453, 9.98558235168457, 2.47782421112061, -0.416413754224777, 1.09579503536224, -3.01458239555359, 5.8245849609375, 8.10295104980469, 10.9622287750244, -0.520937860012054, -6.83755540847778, -7.75091743469238, -11.5412445068359, 5.5302267074585, 2.26544833183289, -2.52757787704468, 0.181061640381813, -3.85825181007385, -7.16098022460938, -2.01259899139404, 0.0691115036606789, -1.66724002361298, -1.72643053531647, 2.87876558303833, 2.23930907249451, 1.44282245635986, -3.44170069694519, -6.73639822006226, 1.04524910449982, 1.35849142074585, 9.6570930480957, -1.98249280452728, -8.31394004821777, -3.96410322189331, -4.09102439880371, -2.42169618606567, 6.6136736869812, 7.20264434814453]
class SharedModelStub(SharedModel):
  model_key = 'video'

  def load(self):
    pass

  def respond(self, task):
    return task

class TestVideoSimilarityBlueprint(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.model = VideoModel()

    def test_get_tempfile(self):
        self.assertIsInstance(self.model.get_tempfile(), tempfile._TemporaryFileWrapper)

    def test_load(self):
        self.model.load()
        self.assertIsInstance(self.model.directory, str)

    def test_delete_by_doc_id(self):
        url = 'file:///app/app/test/data/chair-19-sd-bar.mp4'
        self.model.load()
        with patch.object(self.model, 'download_file', return_value=None):
            self.model.add({"folder": "foo", "filepath": "bar", "result": {"hash_value": [1,2,3], "folder": "abcd", "filepath": "abcd-efgh"}, "url": url, 'doc_id': "Y2hlY2stcHJvamVjdF9tZWRpYS01NTQ1NzEtdmlkZW8", "context": {"has_custom_id": True}})
            result = self.model.delete({"url": url, 'doc_id': "Y2hlY2stcHJvamVjdF9tZWRpYS01NTQ1NzEtdmlkZW8", "context": {"has_custom_id": True}})
            self.assertIsInstance(result, dict)
            self.assertEqual(sorted(result.keys()), ['requested', 'result'])
            self.assertEqual(sorted(result['requested'].keys()), ['context', 'doc_id', 'url'])
            self.assertEqual(sorted(result['result'].keys()), ['deleted', 'url'])

    def test_add_by_doc_id(self):
        url = 'file:///app/app/test/data/chair-19-sd-bar.mp4'
        self.model.load()
        with patch.object(self.model, 'download_file', return_value=None):
            result = self.model.add({"folder": "foo", "filepath": "bar", "result": {"hash_value": [1,2,3], "folder": "abcd", "filepath": "abcd-efgh"}, "url": url, 'doc_id': "Y2hlY2stcHJvamVjdF9tZWRpYS01NTQ1NzEtdmlkZW8", "context": {"has_custom_id": True}})
            self.assertIsInstance(result, dict)
            self.assertEqual(sorted(result.keys()), ['requested', 'result', 'success'])
            self.assertEqual(sorted(result['requested'].keys()), ['context', 'doc_id', 'filepath', 'folder', 'hash_value', 'result', 'url'])
            self.assertEqual(sorted(result['result'].keys()), ['url'])

    def test_search_by_doc_id(self):
        url = 'file:///app/app/test/data/chair-19-sd-bar.mp4'
        self.model.load()
        hash_key = "blah"
        with patch('app.main.lib.shared_models.video_model.VideoModel.search_by_context', ) as mock_search_by_context:
            with patch('tmkpy.query', ) as mock_tmk_query:
                with patch.object(self.model, 'download_file', return_value=None):
                    with patch('app.main.lib.shared_models.video_model.VideoModel.tmk_file_exists', ) as mock_video_file_exists:
                        mock_video_file_exists.return_value = True
                        mock_tmk_query.return_value = (0.99,)
                        mock_search_by_context.return_value = [{"folder": "blah", "filepath": "12342", "context": [{'blah': 1, 'project_media_id': 12342}], "hash_value": IDENTICAL_HASH_VALUE}, {"folder": "blah", "filepath": "12343", "context": [{'blah': 1, 'project_media_id': 12343}], "hash_value": np.random.rand(256).tolist()}]
                        self.model.add({"folder": "foo", "filepath": "bar", "result": {"folder": "blah", "filepath": "12342", "hash_value": IDENTICAL_HASH_VALUE}, "url": url, 'doc_id': "Y2hlY2stcHJvamVjdF9tZWRpYS01NTQ1NzEtdmlkZW8", "context": {"blah": 1, "has_custom_id": True, 'project_media_id': 12343}})
                        result = self.model.search({"url": url, 'doc_id': "Y2hlY2stcHJvamVjdF9tZWRpYS01NTQ1NzEtdmlkZW8", "context": {"blah": 1, "has_custom_id": True, 'project_media_id': 12343}})
        self.assertIsInstance(result, dict)
        self.assertEqual(sorted(result["result"][0].keys()), ['context', 'doc_id', 'filename', 'filepath', 'folder', 'model', 'score', 'url'])
        self.assertEqual(result["result"][0], {'context': [{'blah': 1, 'project_media_id': 12342}], 'folder': 'blah', 'filepath': '12342', 'doc_id': None, 'url': None, 'filename': '/app/persistent_disk/blah/12342.tmk', 'score': 0.99, 'model': 'video'})

    def test_delete(self):
        url = 'file:///app/app/test/data/chair-19-sd-bar.mp4'
        self.model.load()
        with patch.object(self.model, 'download_file', return_value=None):
            self.model.add({"folder": "foo", "filepath": "bar", "result": {"folder": "abcd", "filepath": "edfg", "hash_value": [1,2,3]}, "url": url, "project_media_id": 1, "context": {'blah': 1, 'project_media_id': 12342}})
            result = self.model.delete({"url": url, "project_media_id": 1, "context": {'blah': 1, 'project_media_id': 12342}})
            self.assertIsInstance(result, dict)
            self.assertEqual(sorted(result.keys()), ['requested', 'result'])
            self.assertEqual(sorted(result['requested'].keys()), ['context', 'project_media_id', 'url'])
            self.assertEqual(sorted(result['result'].keys()), ['deleted', 'url'])

    def test_add(self):
        url = 'file:///app/app/test/data/chair-19-sd-bar.mp4'
        self.model.load()
        with patch.object(self.model, 'download_file', return_value=None):
            result = self.model.add({"folder": "foo", "filepath": "bar", "result": {"hash_value": [1,2,3], "folder": "abcd", "filepath": "efgh"}, "url": url, "project_media_id": 1})
            self.assertIsInstance(result, dict)
            self.assertEqual(sorted(result.keys()), ['requested', 'result', 'success'])
            self.assertEqual(sorted(result['requested'].keys()), ['filepath', 'folder', 'hash_value', 'project_media_id', 'result', 'url'])
            self.assertEqual(sorted(result['result'].keys()), ['url'])

    def test_search(self):
        url = 'file:///app/app/test/data/chair-19-sd-bar.mp4'
        self.model.load()
        hash_key = "blah"
        with patch('app.main.lib.shared_models.video_model.VideoModel.search_by_context', ) as mock_search_by_context:
            with patch('tmkpy.query', ) as mock_tmk_query:
                with patch.object(self.model, 'download_file', return_value=None):
                    with patch('app.main.lib.shared_models.video_model.VideoModel.tmk_file_exists', ) as mock_video_file_exists:
                        mock_video_file_exists.return_value = True
                        mock_tmk_query.return_value = (0.99,)
                        mock_search_by_context.return_value = [{"folder": "blah", "filepath": "12342", "context": [{'blah': 1, 'project_media_id': 12342}], "hash_value": IDENTICAL_HASH_VALUE}, {"folder": "blah", "filepath": "12343", "context": [{'blah': 1, 'project_media_id': 12343}], "hash_value": np.random.rand(256).tolist()}]
                        self.model.add({"folder": "foo", "filepath": "bar", "result": {"folder": "blah", "filepath": "12342", "hash_value": IDENTICAL_HASH_VALUE}, "url": url, "project_media_id": 1, "context": {"blah": 1, 'project_media_id': 12343}})
                        result = self.model.search({"url": url, "project_media_id": 1, "context": {"blah": 1, 'project_media_id': 12343}})
        self.assertIsInstance(result, dict)
        self.assertEqual(sorted(result["result"][0].keys()), ['context', 'doc_id', 'filename', 'filepath', 'folder', 'model', 'score', 'url'])
        self.assertEqual(result["result"][0], {'context': [{'blah': 1, 'project_media_id': 12342}], 'folder': 'blah', 'filepath': '12342', 'doc_id': None, 'url': None, 'filename': '/app/persistent_disk/blah/12342.tmk', 'score': 0.99, 'model': 'video'})

    def test_get_fullpath_files(self):
        self.model.load()
        self.assertIsInstance(self.model.get_fullpath_files([{"folder": "blah", "filepath": "foo"}]), list)
        with patch('os.listdir', ) as mock_list:
            with patch('os.path.isfile', ) as mock_is_file:
                with patch('os.path.exists', ) as mock_exists:
                    mock_list.return_value = ['/app/persistent_disk/blah/1.tmk']
                    mock_is_file.return_value = True
                    mock_exists.return_value = True
                    result = self.model.get_fullpath_files([{"folder": "blah", "filepath": "foo"}])
        self.assertEqual(result, ['/app/persistent_disk/blah/foo.tmk'])

    def test_search_by_context(self):
        url = 'file:///app/app/test/data/chair-19-sd-bar.mp4'
        with patch.object(self.model, 'download_file', return_value=None):
            self.model.load()
            self.model.add({"folder": "foo", "filepath": "bar", "result": {"folder": "abcd", "filepath": "edfg", "hash_value": [1,2,3]}, "url": url, "context": {"blah": 1 }})
            results = self.model.search_by_context({"blah": 1})
            self.assertEqual(results[0]['url'], url)
            self.assertEqual(results[0]['context'], [{"blah": 1}])
            results = self.model.search_by_context({"blah": 2})
            self.assertEqual(results, [])

if __name__ == '__main__':
  unittest.main()