import time
import uuid
import unittest
import json
from opensearchpy import helpers, OpenSearch, TransportError
from flask import current_app as app
from unittest.mock import Mock, patch
import numpy as np

from app.main import db
from app.test.base import BaseTestCase
from app.main.lib.shared_models.shared_model import SharedModel
from unittest.mock import patch
from app.main.model.audio import Audio
from app.main.lib.shared_models.audio_model import AudioModel
from app.main.lib import redis_client
TEST_EMBEDDING = [0.02537091076374054, 0.14412401616573334, -0.013707341626286507, 0.035001955926418304, 0.06516401469707489, 0.06645793467760086, 0.013244744390249252, -0.05431090295314789, -0.05248243361711502, 0.16576412320137024, 0.04719928279519081, 0.08532586693763733, -0.058140337467193604, 0.34069377183914185, -0.002619129605591297, -0.1991289258003235, -0.007370054256170988, 0.19620764255523682, 0.06237252801656723, -0.04475881904363632, -0.052009761333465576, -0.04347680136561394, 0.007334447465837002, -0.06966383755207062, -0.07865776866674423, 0.004215184599161148, 0.121464803814888, 0.0467362254858017, -0.06093596667051315, 0.02486894465982914, 0.3012259602546692, -0.0027068560011684895, -0.030927583575248718, -0.1375606656074524, 0.10729026049375534, 0.018338674679398537, -0.05300144478678703, 0.035471148788928986, -0.20091980695724487, 0.014179457910358906, 0.3481976389884949, 0.020274801179766655, 0.0018653376027941704, 0.0914345383644104, -0.11325767636299133, -0.25501805543899536, 0.06575058400630951, 0.12477008998394012, -0.13627633452415466, -0.04129289835691452, 0.02583225630223751, 0.2673092484474182, -0.1487998068332672, 0.049232564866542816, 0.34900224208831787, -0.1724003702402115, -0.08649541437625885, -0.16533051431179047, 0.0034198863431811333, 0.07117055356502533, 0.015578127466142178, 0.09183154255151749, -0.024066409096121788, 0.04296422749757767, 0.007689141668379307, 0.05011913180351257, 0.48612093925476074, -0.002129840664565563, -0.13494345545768738, -0.07959745824337006, 0.055321887135505676, 0.10866454243659973, 0.003982161171734333, 0.04757089167833328, 0.06926750391721725, -0.29120758175849915, -0.0030267303809523582, 8.659530431032181e-05, -0.016103550791740417, -0.013067571446299553, -0.13672097027301788, 0.06206212937831879, -0.0748116672039032, 0.16224558651447296, -0.09824760258197784, 0.09166797995567322, 0.022078165784478188, 0.012346267700195312, -0.1684945821762085, -0.07415011525154114, 0.2822607755661011, -0.05768199265003204, 0.07241274416446686, -0.05020619183778763, 0.02512241154909134, 0.02240893244743347, 0.062828928232193, 0.14586102962493896, 0.009585399180650711, 0.001362822949886322, -0.13039134442806244, -0.0016827136278152466, -0.05146288871765137, 0.06161820888519287, 0.059749536216259, 0.00917733646929264, 0.030715376138687134, -0.3215716481208801, 0.053636688739061356, 0.045824963599443436, 0.2479085624217987, -0.04259314015507698, -0.061405837535858154, 0.2000066637992859, 0.03967494145035744, -0.05145803838968277, 0.08905410021543503, -0.05383775383234024, -0.16746610403060913, 0.08951856940984726, -0.05684755742549896, 0.03783491626381874, -0.05575256422162056, -0.01696639508008957, 0.09885580837726593, 0.12313386797904968, -0.08064521849155426, -0.07530079782009125, -0.029482685029506683, 0.11024484038352966, -0.05627257749438286, -0.08248034119606018, -0.056693121790885925, -0.0031391670927405357, 0.022082306444644928, -0.16404055058956146, 0.03670206293463707, 0.041126981377601624, -0.10353367030620575, 0.19320932030677795, 0.019303178414702415, -0.03181290626525879, -0.10264457762241364, -0.032091982662677765, -0.1051267609000206, -0.0020635100081562996, -0.0022523687221109867, -0.08336733281612396, 0.04636789858341217, 0.057960137724876404, 0.08486993610858917, 0.17920774221420288, -0.33907657861709595, -0.04302056506276131, 0.15348456799983978, 0.08046513795852661, -0.05292341485619545, -0.08844828605651855, -0.09841413795948029, -0.08220598846673965, -0.03130720555782318, -0.10854649543762207, 0.009097438305616379, 0.10730461776256561, 0.12832564115524292, -0.0797344371676445, 0.182969331741333, -0.2027251124382019, 0.15642550587654114, -0.041848041117191315, 0.09238139539957047, 0.06655462086200714, -0.0779763013124466, 0.0711202397942543, 0.06242763251066208, 0.03508594632148743, -0.501676082611084, -0.002488253638148308, -0.09762413799762726, -0.04987851157784462, -0.05935855582356453, 0.18217316269874573, 0.028053874149918556, 0.11839695274829865, -0.026810921728610992, 0.05655436962842941, 0.16428007185459137, 0.07051224261522293, -0.01129025500267744, -0.07031390815973282, 0.038731202483177185, 0.05256303399801254, -0.03127909451723099, 0.014975192956626415, -0.043813157826662064, 0.015049063600599766, -0.14778287708759308, 0.3431599736213684, -0.005516083911061287, 0.038537271320819855, -0.028923174366354942, -0.10412909090518951, 0.09697943925857544, -0.07368891686201096, -0.13936090469360352, -0.017086690291762352, -0.013082458637654781, -0.09873013198375702, 0.054681867361068726, 0.13046713173389435, 0.13939614593982697, 0.03219131752848625, 0.00343277957290411, -0.0649285763502121, -0.011796548031270504, -0.13673430681228638, 0.08814384043216705, 0.08568902313709259, -0.014534007757902145, 0.10199956595897675, -0.03367357328534126, -0.018765615299344063, 0.0888487696647644, 0.030498836189508438, -0.1296345293521881, 0.08775979280471802, -0.02638973668217659, -0.027115508913993835, 0.08143982291221619, 0.0856306180357933, -0.03904366120696068, 0.1178208589553833, 0.09215237945318222, 0.01817522943019867, -0.09122122824192047, -0.25192075967788696, -0.0025615915656089783, -0.08590662479400635, 0.1629449427127838, -0.057395145297050476, 0.02259792387485504, 0.03722165524959564, -0.010589413344860077, 0.07164692878723145, 0.3066202402114868, -0.01403727289289236, -0.04406745731830597, -0.008837014436721802, -0.07037828862667084, -0.05169210582971573, 0.052700258791446686, 0.0778391882777214, -0.005023400764912367, -0.01477598212659359, 0.0902605876326561, 0.16356728971004486, -0.12620723247528076, 0.119113989174366, -0.08385884761810303, -0.07000541687011719, 0.13879750669002533, 0.06429379433393478, -0.03976581618189812, -0.16176234185695648, -0.07461363077163696, 0.020881569012999535, 0.23179718852043152, -0.12305279821157455, 0.034290675073862076, 0.04314017295837402, -0.04238716885447502, 0.03374053165316582, -0.04057180508971214, -0.07465510815382004, -0.027374109253287315, -0.020321156829595566, -0.14975064992904663, -0.05107520893216133, -0.07696080952882767, -0.0009968671947717667, 0.04474473372101784, 0.08992260694503784, -0.06712459772825241, 0.06630776822566986, -0.030159395188093185, -0.10869680345058441, -0.11919915676116943, -0.17923641204833984, -0.024947231635451317, -0.04011044651269913, -0.02986730821430683, 0.0012389845214784145, 0.009246927686035633, 0.016303347423672676, -0.010947410948574543, -0.0004700981080532074, 0.07178070396184921, 0.01879064552485943, 0.013456234708428383, 0.14524206519126892, 0.030236560851335526, -0.02995057962834835, -0.12200143933296204, 0.011315906420350075, -0.1310195028781891, 0.1372310370206833, 0.03368866816163063, -0.26138439774513245, 0.025431234389543533, 0.10869722068309784, 0.05526931583881378, 0.028030680492520332, -0.00709895696491003, 0.1644946038722992, -0.008952474221587181, 0.045740582048892975, -0.09966389834880829, -0.038365062326192856, -0.005820239894092083, 0.0695662647485733, 0.10416896641254425, -0.024526501074433327, -0.04170447215437889, -0.0654788464307785, -0.13509204983711243, 0.087185338139534, 0.05783521384000778, -0.023421576246619225, -0.0985737293958664, -0.1528509557247162, -0.002876346930861473, 0.11252746731042862, -0.08852416276931763, -0.07361768186092377, -0.12574104964733124, -0.07362733781337738, 0.03404182940721512, -0.03131967782974243, -0.09927935898303986, 0.0731954425573349, -0.012522652745246887, -0.1404901146888733, 0.08169828355312347, -0.19257265329360962, -0.09545747935771942, 0.0018997061997652054, 0.30539044737815857, 0.03650631010532379, -0.2454720437526703, 0.016808025538921356, -0.02490060403943062, 0.009813779033720493, 0.0522051639854908, -0.12270733714103699, 0.04678839072585106, -0.030956890434026718, -0.09326930344104767, 0.03018069639801979, 0.20345206558704376, 0.152109295129776, -0.10719567537307739, 0.044989462941884995, -0.06738286465406418, -0.04416991397738457, 0.06339416652917862, 0.04256817698478699, 0.10097813606262207, 0.14754672348499298, -0.05146140605211258, -0.039928559213876724, -0.07499262690544128, 0.01647130586206913, 0.027623755857348442, 0.015505538322031498, 0.0318794809281826, 0.18611565232276917, 0.09391216188669205, -0.15115098655223846, 0.22291302680969238, -0.0711141899228096, -0.08748221397399902, -0.12462995946407318, -0.05667521059513092, 0.03696715086698532, 0.01950675994157791, 0.05205093324184418, -0.03583093732595444, -0.016746122390031815, -0.16304606199264526, -0.01961861178278923, 0.009879546239972115, -0.10713739693164825, -0.07763954997062683, 0.10511482506990433, 0.05870126932859421, -0.00523056834936142, 0.09288904815912247, 0.040175482630729675, 0.0782988891005516, -0.035858165472745895, 0.08046222478151321, -0.0989396870136261, -0.05152665823698044, -0.056968096643686295, 0.023944340646266937, 0.07257086038589478, -0.24581372737884521, -0.05164909362792969, -0.06239117681980133, 0.18144933879375458, 0.0349668525159359, -0.06402310729026794, -0.06635291129350662, -0.029842311516404152, 0.06578555703163147, -0.11294735968112946, -0.008892704732716084, -0.08440466970205307, -0.04750542715191841, -0.15347325801849365, -0.04981758072972298, 0.0037585198879241943, 0.04098815470933914, 0.08311119675636292, -0.10454528033733368, -0.03403598815202713, -0.009495059959590435, 0.13818702101707458, 0.07781055569648743, -0.03283096104860306, 0.08070573955774307, -0.025247780606150627, -0.03681982308626175, 0.057447269558906555, 0.055999208241701126, 0.08387625962495804, 0.09137067198753357, -0.09880639612674713, -0.1159106194972992, 0.004327467642724514, -0.06007562577724457, 0.11313144862651825, 0.18407867848873138, -0.019694384187459946, 0.07195024192333221, 0.1625886708498001, -0.060112617909908295, -0.13918454945087433, -0.09627020359039307, 0.09283843636512756, 0.053530722856521606, 0.09021905064582825, -0.03000117652118206, -0.01117345318198204, 0.04522938281297684, -0.03340967744588852, 0.2562655806541443, 0.02503146417438984, 0.02744886837899685, 0.05252760648727417, 0.18569858372211456, 0.32205843925476074, -0.057340849190950394, 0.13735361397266388, -0.06338537484407425, 0.10604717582464218, 0.07122714817523956, 0.32458919286727905, 0.08434467762708664, -0.014665283262729645, -0.05745268613100052, -0.06356792896986008, -0.011974096298217773, 0.10612200945615768, -0.11452727019786835, -0.011953390203416348, -0.052537720650434494, -0.35822293162345886, 0.3774245083332062, 0.024699196219444275, -0.04209441319108009, -0.18047025799751282, -0.10209169238805771, 0.026147177442908287, -0.03861386328935623, -0.07206010073423386, 0.07519310712814331, -0.09908917546272278, -0.020711135119199753, 0.007229332812130451, -0.001597030321136117, 0.02832939848303795, -0.05709546059370041, -0.11839232593774796, -0.1222495585680008, 0.12064091116189957, 0.09759324789047241, -0.11553465574979782, -0.07961006462574005, -0.28111037611961365, 0.02689402922987938, -0.09432223439216614, 0.019710347056388855, 0.0002807299606502056, -0.025272918865084648, 0.038521189242601395, -0.004203370772302151, 0.013692151755094528, 0.06903356313705444, -0.07003206014633179, 0.15057885646820068, 0.11030421406030655, 0.11006708443164825, -0.054223183542490005, 0.04911644011735916, -0.10609858483076096, 0.008592106401920319, -0.0062067243270576, 0.08257198333740234, 0.1480412781238556, -0.0717809870839119, 0.11372383683919907, 0.01463585440069437, 0.03439546376466751, -0.024517327547073364, -0.02563106268644333, -0.004179127514362335, -0.0720820277929306, -0.2003721296787262, 0.02016180194914341, 0.10654407739639282, 0.020841369405388832, 0.00882712285965681, 0.10467993468046188, 0.023352578282356262, 0.043582890182733536, 0.12182028591632843, 0.21881237626075745, 0.09945045411586761, -0.06317570805549622, -0.012470033019781113, 0.015721280127763748, 0.24013543128967285, -0.034864384680986404, 0.00400135200470686, -0.085032619535923, 0.10288774967193604, 0.02128634974360466, 0.05131254717707634, 0.053360797464847565, 0.09305281937122345, 0.0965166985988617, 0.06534170359373093, 0.036645859479904175, -0.07461575418710709, -0.1735968291759491, -0.05923863872885704, -0.20511938631534576, -0.00850694254040718, -0.4299125373363495, -0.06980200856924057, -0.05291181802749634, -0.1373322457075119, 0.020103849470615387, -0.020942138507962227, 0.012998731806874275, -0.001948293298482895, 0.04434487968683243, 0.23224185407161713, 0.07672680169343948, -0.029112260788679123, 0.025976181030273438, 0.07983095943927765, 0.022311531007289886, -0.08160354197025299, 0.004317501559853554, 0.03285597264766693, 0.01149295549839735, 0.1654084324836731, 0.03205054625868797, -0.015278731472790241, 0.03269533812999725, -0.11608333885669708, -0.11424101144075394, 0.11962299048900604, -0.001129710115492344, -0.02141176536679268, 0.06958864629268646, 0.045666590332984924, 0.27815791964530945, -0.06272298097610474, 0.14777502417564392, 0.09809857606887817, -0.1570918709039688, -0.008920835331082344, -0.09215539693832397, 0.13959679007530212, 0.02075675129890442, 0.05034048110246658, 0.11860141158103943, -0.09497466683387756, -0.1031079888343811, -0.05765848606824875, 0.04962430149316788, 0.01600678637623787, -0.1209292933344841, -0.04576015844941139, 0.037512023001909256, -0.00010843528434634209, -0.07182782143354416, -0.08310272544622421, -0.17773957550525665, -0.004558751825243235, 0.16890846192836761, -0.01794707402586937, -0.020448381081223488, -0.041982874274253845, -0.021183600649237633, -0.046009745448827744, -0.19426551461219788, -0.08381566405296326, -0.04327947646379471, -0.11045600473880768, 0.148170605301857, -0.059749774634838104, 0.01919037103652954, 0.01902671344578266, -0.09038849174976349, 0.1103670746088028, -0.14616359770298004, 0.10131926834583282, -0.01778235286474228, 0.012552394531667233, 0.006466265302151442, 0.03241812437772751, 0.11668127775192261, 0.05157840996980667, 0.0310125183314085, -0.013051541522145271, -0.02214495837688446, -0.10240590572357178, -0.13244476914405823, -0.04818994551897049, 0.1781781017780304, 0.087042897939682, -0.08918170630931854, -0.11065610498189926, 0.08503603935241699, 0.005775831174105406, -0.019522037357091904, -0.13015490770339966, 0.11930814385414124, -0.033441659063100815, -0.0309203639626503, 0.08477157354354858, -0.03911957889795303, -0.025544658303260803, -0.07434310019016266, -0.05370403826236725, 0.07687976956367493, 0.09012692421674728, 0.050922736525535583, -0.188390851020813, -0.14020472764968872, -0.12199529260396957, 0.023874986916780472, -0.04643715173006058, 0.07003121078014374, 0.031231286004185677, 0.13200363516807556, -0.01566615328192711, -0.08556234836578369, -0.004927341360598803, -0.24548161029815674, -0.0063619548454880714, -0.10463286936283112, -0.028088869526982307, 0.347121924161911, -0.160556823015213, 0.05691935867071152, -0.010154478251934052, 0.1540493667125702, -0.12434209883213043, -0.210264652967453, 0.04947035014629364, -0.032636940479278564, -0.05657530948519707, -0.051591482013463974, 0.051725421100854874, -0.04523289203643799, 0.1812276542186737, -0.05899140238761902, 0.3575742840766907, -0.044510096311569214, 0.05458342283964157, -0.12906154990196228, 0.0488046258687973, -0.04230339452624321, -0.31768494844436646, 0.07670441269874573, -0.018132418394088745, -0.10642766952514648, 0.06678644567728043, -0.17398467659950256, 0.09847372770309448, 0.04683662950992584, -0.2477765679359436, -0.053890909999608994, 0.08163920789957047, 0.12757349014282227, -0.05038313567638397, -0.035816311836242676, -0.022769391536712646, -0.008687367662787437, -0.0014297841116786003, -0.024464428424835205, -0.09576714783906937, 0.162383034825325, 0.12889713048934937, -0.05441683158278465, -0.15533077716827393, -0.04692191630601883, 0.026149149984121323, 0.09322920441627502, -0.0021579135209321976, 0.15366174280643463, 0.143022358417511, 0.10776479542255402, -0.10245905816555023, -0.12517578899860382, -0.019255224615335464, -0.15177251398563385, -0.1383628249168396, 0.042740464210510254, 0.12772023677825928, 0.053558349609375, 0.09411708265542984, -0.1778920292854309, 0.017515845596790314, 0.19943587481975555, -0.09455756098031998, 0.03164178133010864, -0.06579870730638504, 0.05490874499082565, -0.0664810836315155, 0.012670662254095078, -0.011597240343689919, 0.15593433380126953, 0.1041531190276146, -0.13616420328617096, 0.010493840090930462, -0.014603850431740284, 0.17918699979782104, 0.021734943613409996, -0.13266527652740479, -0.07586095482110977, -0.02174500748515129, 0.09551297128200531, 0.03267138451337814, -0.0234953872859478, 0.05214712768793106, -0.08145228773355484, 0.03710713982582092, -0.12780220806598663, 0.0012545203790068626, 0.01739080436527729, 0.02523917704820633, 0.011966507881879807]
class TestSyncSimilarityBlueprint(BaseTestCase):
    def setUp(self):
        super().setUp()
        first_print = 49805440634311326
        self.model = AudioModel()

    def tearDown(self): # done in our pytest fixture after yield
        db.session.remove()
        db.drop_all()

    def test_text_basic_http_responses_with_doc_id(self):
        text = 'This is some sample text to test with'
        team_id = str(uuid.uuid4())
        with patch('requests.post') as mock_post_request:
            r = redis_client.get_client()
            r.delete(f"text_1c63abe0-aeb4-4bac-8925-948b69c32d0d")
            r.lpush(f"text_1c63abe0-aeb4-4bac-8925-948b69c32d0d", json.dumps({"body": {"result": TEST_EMBEDDING}}))
            mock_response = Mock()
            mock_response.text = json.dumps({
                'message': 'Message pushed successfully',
                'queue': 'paraphrase_multilingual__Model',
                'body': {
                    'callback_url': 'http://alegre:3100/presto/receive/add_item/text',
                    'id': "1c63abe0-aeb4-4bac-8925-948b69c32d0d",
                    'text': text,
                    'raw': {
                        'doc_id': "1c63abe0-aeb4-4bac-8925-948b69c32d0d",
                        'text': text,
                    }
                }
            })
            mock_post_request.return_value = mock_response
            response = self.client.post('/similarity/sync/text', data=json.dumps({
                'text': text,
                'doc_id': "1c63abe0-aeb4-4bac-8925-948b69c32d0d",
                'context': {
                    'team_uuid': team_id,
                },
                'models': ['elasticsearch', 'paraphrase-multilingual-mpnet-base-v2'],
                'min_es_score': 0.1
            }), content_type='application/json')
        time.sleep(5)
        response = self.client.post('/similarity/sync/text', data=json.dumps({
            'text': text,
            'context': {
                'team_uuid': team_id,
            },
            'models': ['elasticsearch'],
            'min_es_score': 0.0
        }), content_type='application/json')
        result = json.loads(response.data.decode())
        self.assertIn('model_paraphrase-multilingual-mpnet-base-v2', sorted(result["result"][0].keys()))
        self.assertEqual(result["result"][0]['text'], text)
        self.assertEqual(result["result"][0]['contexts'][0], {'team_uuid': team_id})

    def test_text_basic_http_responses(self):
        text = 'This is some sample text to test with'
        team_id = str(uuid.uuid4())
        with patch('requests.post') as mock_post_request:
            r = redis_client.get_client()
            r.delete(f"text_1c63abe0-aeb4-4bac-8925-948b69c32d0d")
            r.lpush(f"text_1c63abe0-aeb4-4bac-8925-948b69c32d0d", json.dumps({"body": {"result": TEST_EMBEDDING}}))
            mock_response = Mock()
            mock_response.text = json.dumps({
                'message': 'Message pushed successfully',
                'queue': 'paraphrase_multilingual__Model',
                'body': {
                    'callback_url': 'http://alegre:3100/presto/receive/add_item/text',
                    'id': "1c63abe0-aeb4-4bac-8925-948b69c32d0d",
                    'text': text,
                    'raw': {
                        'doc_id': "1c63abe0-aeb4-4bac-8925-948b69c32d0d",
                        'text': text,
                    }
                }
            })
            mock_post_request.return_value = mock_response
            response = self.client.post('/similarity/sync/text', data=json.dumps({
                'text': text,
                'context': {
                    'project_media_uuid': team_id,
                    'team_uuid': team_id,
                },
                'models': ['elasticsearch', 'paraphrase-multilingual-mpnet-base-v2'],
                'min_es_score': 0.1
            }), content_type='application/json')
        time.sleep(5)
        response = self.client.post('/similarity/sync/text', data=json.dumps({
            'text': text,
            'context': {
                'team_uuid': team_id,
            },
            'models': ['elasticsearch'],
            'min_es_score': 0.0
        }), content_type='application/json')
        result = json.loads(response.data.decode())
        self.assertIn('model_paraphrase-multilingual-mpnet-base-v2', sorted(result["result"][0].keys()))
        self.assertEqual(result["result"][0]['text'], text)
        self.assertEqual(result["result"][0]['contexts'][0], {'project_media_uuid': team_id, 'team_uuid': team_id})

    def test_audio_basic_http_responses_with_doc_id(self):
        url = 'file:///app/app/test/data/test_audio_1.mp3'
        with patch('requests.post') as mock_post_request:
            r = redis_client.get_client()
            r.delete(f"audio_1c63abe0-aeb4-4bac-8925-948b69c32d0d")
            r.lpush(f"audio_1c63abe0-aeb4-4bac-8925-948b69c32d0d", json.dumps({"body": {"result": {"hash_value": [1,2,3]}}}))
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
            response = self.client.post('/similarity/sync/audio', data=json.dumps({
                'url': url,
                'doc_id': "1c63abe0-aeb4-4bac-8925-948b69c32d0d",
                'context': {
                    'team_id': 1,
                }
            }), content_type='application/json')
        result = json.loads(response.data.decode())
        self.assertEqual(sorted(result["result"][0].keys()), ['chromaprint_fingerprint', 'context', 'doc_id', 'id', 'model', 'score', 'url'])
        self.assertEqual(result["result"][0]['doc_id'], '1c63abe0-aeb4-4bac-8925-948b69c32d0d')
        self.assertEqual(result["result"][0]['url'], 'file:///app/app/test/data/test_audio_1.mp3')
        self.assertEqual(result["result"][0]['context'], [{'team_id': 1}])

    def test_audio_basic_http_responses(self):
        url = 'http://example.com/blah.mp3'
        with patch('requests.post') as mock_post_request:
            r = redis_client.get_client()
            r.delete(f"audio_1c63abe0-aeb4-4bac-8925-948b69c32d0d")
            r.lpush(f"audio_1c63abe0-aeb4-4bac-8925-948b69c32d0d", json.dumps({"body": {"result": {"hash_value": [1,2,3]}}}))
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
            response = self.client.post('/similarity/sync/audio', data=json.dumps({
                'url': url,
                'project_media_id': 1,
                'context': {
                    'team_id': 1,
                }
            }), content_type='application/json')
        result = json.loads(response.data.decode())
        self.assertEqual(sorted(result["result"][0].keys()), ['chromaprint_fingerprint', 'context', 'doc_id', 'id', 'model', 'score', 'url'])
        self.assertEqual(result["result"][0]['url'], 'http://example.com/blah.mp3')
        self.assertEqual(result["result"][0]['context'], [{'team_id': 1}])

    def test_image_basic_http_responses_with_doc_id(self):
        url = 'file:///app/app/test/data/lenna-512.jpg'
        with patch('requests.post') as mock_post_request:
            with patch('app.main.lib.image_similarity.execute_command') as mock_db_response:
                mock_db_response.return_value = [(1, "1c63abe0-aeb4-4bac-8925-948b69c32d0d", 49805440634311326, 'http://example.com/lenna-512.png', [{'team_id': 1}], 1.0)]
                r = redis_client.get_client()
                r.delete(f"image_1c63abe0-aeb4-4bac-8925-948b69c32d0d")
                r.lpush(f"image_1c63abe0-aeb4-4bac-8925-948b69c32d0d", json.dumps({"body": {"hash_value": 49805440634311326}}))
                mock_response = Mock()
                mock_response.text = json.dumps({
                    'message': 'Message pushed successfully',
                    'queue': 'image__Model',
                    'body': {
                        'callback_url': 'http://alegre:3100/presto/receive/add_item/image',
                        'id': "1c63abe0-aeb4-4bac-8925-948b69c32d0d",
                        'url': 'http://example.com/lenna-512.png',
                        'text': None,
                        'raw': {
                            'doc_id': "1c63abe0-aeb4-4bac-8925-948b69c32d0d",
                            'url': 'http://example.com/lenna-512.png'
                        }
                    }
                })
                mock_post_request.return_value = mock_response
                response = self.client.post('/similarity/sync/image', data=json.dumps({
                    'url': url,
                    'doc_id': "1c63abe0-aeb4-4bac-8925-948b69c32d0d",
                    'context': {
                        'team_id': 1,
                    }
                }), content_type='application/json')
        result = json.loads(response.data.decode())
        self.assertEqual(sorted(result["result"][0].keys()), ['context', 'doc_id', 'id', 'model', 'phash', 'score', 'url'])
        self.assertEqual(result["result"][0]['doc_id'], '1c63abe0-aeb4-4bac-8925-948b69c32d0d')
        self.assertEqual(result["result"][0]['url'], 'http://example.com/lenna-512.png')
        self.assertEqual(result["result"][0]['context'], [{'team_id': 1}])

    def test_image_basic_http_responses(self):
        url = 'http://example.com/lenna-512.png'
        with patch('requests.post') as mock_post_request:
            with patch('app.main.lib.image_similarity.execute_command') as mock_db_response:
                mock_db_response.return_value = [(1, "1c63abe0-aeb4-4bac-8925-948b69c32d0d", 49805440634311326, 'http://example.com/lenna-512.png', [{'team_id': 1}], 1.0)]
                r = redis_client.get_client()
                r.delete(f"image_1c63abe0-aeb4-4bac-8925-948b69c32d0d")
                r.lpush(f"image_1c63abe0-aeb4-4bac-8925-948b69c32d0d", json.dumps({"body": {"hash_value": 49805440634311326}}))
                mock_response = Mock()
                mock_response.text = json.dumps({
                    'message': 'Message pushed successfully',
                    'queue': 'image__Model',
                    'body': {
                        'callback_url': 'http://alegre:3100/presto/receive/add_item/image',
                        'id': "1c63abe0-aeb4-4bac-8925-948b69c32d0d",
                        'url': 'http://example.com/lenna-512.png',
                        'text': None,
                        'raw': {
                            'doc_id': "1c63abe0-aeb4-4bac-8925-948b69c32d0d",
                            'url': 'http://example.com/lenna-512.png',
                        }
                    }
                })
                mock_post_request.return_value = mock_response
                response = self.client.post('/similarity/sync/image', data=json.dumps({
                    'url': url,
                    'project_media_id': 1,
                    'context': {
                        'team_id': 1,
                    }
                }), content_type='application/json')
        result = json.loads(response.data.decode())
        self.assertEqual(sorted(result["result"][0].keys()), ['context', 'doc_id', 'id', 'model', 'phash', 'score', 'url'])
        self.assertEqual(result["result"][0]['url'],'http://example.com/lenna-512.png')
        self.assertEqual(result["result"][0]['context'], [{'team_id': 1}])

    def test_video_basic_http_responses_with_doc_id(self):
        url = 'file:///app/app/test/data/chair-19-sd-bar.mp4'
        with patch('requests.post') as mock_post_request:
            with patch('app.main.lib.shared_models.video_model.VideoModel.execute_command') as mock_db_response:
                with patch('app.main.lib.shared_models.video_model.tmkpy.query') as mock_query:
                    with patch('app.main.lib.shared_models.video_model.VideoModel.tmk_file_exists', ) as mock_video_file_exists:
                        mock_video_file_exists.return_value = True
                        mock_query.return_value = (1.0,)
                        mock_db_response.return_value = [(1, "Y2hlY2stcHJvamVjdF9tZWRpYS02Mzc2ODQtdmlkZW8", 'http://example.com/chair-19-sd-bar.mp4', "f4cf", "78f84604-f4cf-4044-a261-5fdf0ac44b63", [{'team_id': 1}], [-1363.0159912109375, 252.60726928710938, 652.66552734375, 48.47494888305664, -12.226404190063477, -62.87214279174805, -11.51701545715332, -13.31611442565918, -2.3773577213287354, -9.220880508422852, 30.38682746887207, -10.805936813354492, 17.883710861206055], True)]
                        r = redis_client.get_client()
                        r.delete(f"video_Y2hlY2stcHJvamVjdF9tZWRpYS02Mzc2ODQtdmlkZW8")
                        r.lpush(f"video_Y2hlY2stcHJvamVjdF9tZWRpYS02Mzc2ODQtdmlkZW8", json.dumps({"body": {"folder": "f4cf", "filepath": "78f84604-f4cf-4044-a261-5fdf0ac44b63", "hash_value": [-1363.0159912109375, 252.60726928710938, 652.66552734375, 48.47494888305664, -12.226404190063477, -62.87214279174805, -11.51701545715332, -13.31611442565918, -2.3773577213287354, -9.220880508422852, 30.38682746887207, -10.805936813354492, 17.883710861206055]}}))
                        r.delete(f"audio_Y2hlY2stcHJvamVjdF9tZWRpYS02Mzc2ODQtdmlkZW8")
                        r.lpush(f"audio_Y2hlY2stcHJvamVjdF9tZWRpYS02Mzc2ODQtdmlkZW8", json.dumps({"body": {"hash_value": [1,2,3]}}))
                        mock_response = Mock()
                        mock_response.text = json.dumps({
                            'message': 'Message pushed successfully',
                            'queue': 'video__Model',
                            'body': {
                                'callback_url': 'http://alegre:3100/presto/receive/add_item/video',
                                'id': "Y2hlY2stcHJvamVjdF9tZWRpYS02Mzc2ODQtdmlkZW8",
                                'url': 'http://example.com/chair-19-sd-bar.mp4',
                                'text': None,
                                'raw': {
                                    'doc_id': "1c63abe0-aeb4-4bac-8925-948b69c32d0d",
                                    'url': 'http://example.com/chair-19-sd-bar.mp4',
                                }
                            }
                        })
                        mock_post_request.return_value = mock_response
                        response = self.client.post('/similarity/sync/video', data=json.dumps({
                            'url': url,
                            'doc_id': "Y2hlY2stcHJvamVjdF9tZWRpYS02Mzc2ODQtdmlkZW8",
                            'context': {
                                'team_id': 1,
                            }
                        }), content_type='application/json')
        result = json.loads(response.data.decode())
        self.assertEqual(sorted(result["result"][0].keys()), ['context', 'doc_id', 'filename', 'filepath', 'folder', 'model', 'score', 'url'])
        self.assertEqual(result["result"][0]['doc_id'], 'Y2hlY2stcHJvamVjdF9tZWRpYS02Mzc2ODQtdmlkZW8')
        self.assertEqual(result["result"][0]['url'], 'http://example.com/chair-19-sd-bar.mp4')
        self.assertEqual(result["result"][0]['context'], [{'team_id': 1}])

    def test_video_basic_http_responses(self):
        url = 'http://example.com/chair-19-sd-bar.mp4'
        with patch('requests.post') as mock_post_request:
            with patch('app.main.lib.shared_models.video_model.VideoModel.execute_command') as mock_db_response:
                with patch('app.main.lib.shared_models.video_model.tmkpy.query') as mock_query:
                    with patch('app.main.lib.shared_models.video_model.VideoModel.tmk_file_exists', ) as mock_video_file_exists:
                        mock_video_file_exists.return_value = True
                        mock_query.return_value = (1.0,)
                        mock_db_response.return_value = [(1, "Y2hlY2stcHJvamVjdF9tZWRpYS02Mzc2ODQtdmlkZW8", 'http://example.com/chair-19-sd-bar.mp4', "f4cf", "78f84604-f4cf-4044-a261-5fdf0ac44b63", [{'team_id': 1}], [-1363.0159912109375, 252.60726928710938, 652.66552734375, 48.47494888305664, -12.226404190063477, -62.87214279174805, -11.51701545715332, -13.31611442565918, -2.3773577213287354, -9.220880508422852, 30.38682746887207, -10.805936813354492, 17.883710861206055], True)]
                        r = redis_client.get_client()
                        r.delete(f"video_Y2hlY2stcHJvamVjdF9tZWRpYS02Mzc2ODQtdmlkZW8")
                        r.lpush(f"video_Y2hlY2stcHJvamVjdF9tZWRpYS02Mzc2ODQtdmlkZW8", json.dumps({"body": {"folder": "f4cf", "filepath": "78f84604-f4cf-4044-a261-5fdf0ac44b63", "hash_value": [-1363.0159912109375, 252.60726928710938, 652.66552734375, 48.47494888305664, -12.226404190063477, -62.87214279174805, -11.51701545715332, -13.31611442565918, -2.3773577213287354, -9.220880508422852, 30.38682746887207, -10.805936813354492, 17.883710861206055]}}))
                        r.delete(f"audio_Y2hlY2stcHJvamVjdF9tZWRpYS02Mzc2ODQtdmlkZW8")
                        r.lpush(f"audio_Y2hlY2stcHJvamVjdF9tZWRpYS02Mzc2ODQtdmlkZW8", json.dumps({"body": {"hash_value": [1,2,3]}}))
                        mock_response = Mock()
                        mock_response.text = json.dumps({
                            'message': 'Message pushed successfully',
                            'queue': 'video__Model',
                            'body': {
                                'callback_url': 'http://alegre:3100/presto/receive/add_item/video',
                                'id': "Y2hlY2stcHJvamVjdF9tZWRpYS02Mzc2ODQtdmlkZW8",
                                'url': 'http://example.com/chair-19-sd-bar.mp4',
                                'text': None,
                                'raw': {
                                    'doc_id': "Y2hlY2stcHJvamVjdF9tZWRpYS02Mzc2ODQtdmlkZW8",
                                    'url': 'http://example.com/chair-19-sd-bar.mp4'
                                }
                            }
                        })
                        mock_post_request.return_value = mock_response
                        response = self.client.post('/similarity/sync/video', data=json.dumps({
                            'url': url,
                            'project_media_id': 1,
                            'context': {
                                'team_id': 1,
                            }
                        }), content_type='application/json')
        result = json.loads(response.data.decode())
        self.assertEqual(sorted(result["result"][0].keys()), ['context', 'doc_id', 'filename', 'filepath', 'folder', 'model', 'score', 'url'])
        self.assertEqual(result["result"][0]['url'],'http://example.com/chair-19-sd-bar.mp4')
        self.assertEqual(result["result"][0]['context'], [{'team_id': 1}])

if __name__ == '__main__':
    unittest.main()