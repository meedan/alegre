import os
import unittest
import json

from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from opensearchpy import OpenSearch, TransportError
import sqlalchemy
from sqlalchemy import text
from sqlalchemy.schema import DDL
from sqlalchemy_utils import database_exists, create_database
import json_logging
from rq import Connection, Worker

from app import blueprint
from app.main import create_app, db
from app.main.model import image
from app.main.lib.shared_models.shared_model import SharedModel
from app.main.lib.language_analyzers import init_indices
from app.main.lib.image_hash import compute_phash_int
from app.main.lib import redis_client
from PIL import Image

# Don't remove this line until https://github.com/tensorflow/tensorflow/issues/34607 is fixed
# (by upgrading to tensorflow 2.2 or higher)
import tensorflow as tf

config_name = os.getenv('BOILERPLATE_ENV', 'dev')
app = create_app(config_name)
app.register_blueprint(blueprint)
app.app_context().push()

manager = Manager(app)
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)

@manager.command
def test_simple_perl_function():
    fingerprint = [-1327875138,-1329980737,-1279583555,-1292363892,-1300745332,-1300750260,-1829818324,-1834151896,-1834008534,-1867652086,-794434550,-790106102,-798113782,-735230886,-735099670,-730956118,-721474904,-721667336,1417428680,1413234376,1413342796,2084484620,1962839597,882809639,899460134,1989977159,1920377027,1915125891,1915125891,572948627,572965027,573043617,582280929,1655987941,1655991876,1660184332,1669095692,-516013768,-532806888,-532802024,1626740344,1620512504,1620319898,1620322954,1619274394,1615079850,-486183766,-502866758,-480865142,-503938998,-525565939,-525561588,-521363172,-533944536,-517423316,-500516052,-496313876,-487928659,-492059474,-492027730,-487825218,-482483974,-532754118,-533839078,-533908726,1613508362,1613507099,-529634773,-525415893,-525366758,-441677110,-408119346,-403918578,1731112975,1714335806,-432087001,-432316379,-432529312,-499642272,-495320860,-486930460,-492171724,1621760516,1621768719,1626028558,1617439246,1613250414,1617432682,1617428714,1710960778,1640576138,1640506526,1908934079,831000509,898185661,394996109,378087823,378349959,378432935,383692710,316573506,1400340738,1348968707,1348969728,1344775184,1344640048,1362079792,1915724064,1916662752,-221724000,-225918299,-225918290,-494237714,-505434838,-532830182,-265377782,-265373686,-265361398,-529532902,-533982166,-532934614,-535297942,-514260566,-477429078,-477477208,-477111640,-509805928,-522933620,-267081084,-267082108,1880417217,1898975811,1915892275,1914839841,1919295776,1923481632,-223461376,1924058116,1907263748,1622129156,1626188300,1617271321,1613018922,1630318890,-483622870,-483606486,-532725462,-534899926,-534892997,-530699719,-526640600,-476292248,-1499984936,-1497885752,-1225248120,-42257783,-61181207,-1126534167,-1130733080,-1128602408,-1111889847,-1096173479,-1096115717,-1091912741,-1100437862,-1104633206,-1389833590,-1406614854,-1540669014,-1536532310,-1536547606,-1535432449,-1267058465,-184670003,-184670003,-721547835,1425998789,1421808279,1354695574,1354044310,1085552050,1089764786,1130667170,1378335874,1378268355,1378264129,1378189313,1915196721,1915207457,1646767653,1630514981,1613665589,1613398037,-534200281,-530034459,-529006363,-528797468,-262528539,-260432031,-251982287,-256963055,-189841917,-189846014,-726702590,-710109630,-693330238,-567505278,-701657470,-164984190,-164983934,-219571039,-223810400,1655202980,1650995340,1646862468,1646928260,1664754100,1614426532,1627063268,1622692404,1621684748,1621683724,1625877004,1617472009,1617541689,-471156437,-487942102,-487945158,-495282933,-434461749,-418798917,-452406615,-1526152535,-1526185288,-1492559960,-1504805464,-1365251928,-1364207559,-1364206567,-1498619637,-1476632310,-1485020918,-1518440342,-1535246102,-1535507286,-465958726,-465958758,-463586934,-455201845,-241281525,-207633911,-201551351,-231431671,-165370563,-161176531,-140213203,-189808513,-185712425,-730984266,-599908170,-595647306,-589481818,-590006106,-594200138,-537445754,1526012550,1517231750,1516974791,451486276,451420452,451682340,443293732,455925796,960012316,960016404,962109821,969449981,1032359101,1036556477,1011464381,873175221,873121941,807041207,823797941,857605287,847184039,846987413,847057493,854467108,850149940,849666564,816112140,811972104,808360456,808376840,808376841,811911979,820300010,849661162,850772185,850833608,844538056,839295208,839164136,839172328,843467912,1371937160,1350990488,1350986472,1356298984,1894800920,1885401609,1893773834,1956815370,1956815658,1952491306,1681168682,-468416470,-468219778,-468285234,-465660722,-449933234,-433335857,-433438227,-433441876,-429252188,-419946332,-424140628,-424140632,-290848520,-290840616,-273741239,-307996149,-303801830,-59975142,-64162294,-64429558,-47652342,-1351953814,-1409644950,-1426552085,-1426527525,-1160188213,-1166350645,-1099238709,-1082506551,-1216724053,-1226227285,-1226283861,-424121170,-222795602,-218597186,1916394686,1916761294,1916687438,1915617359,841359431,841352053,845423332,867447532,1891386092,1890534088,1890468552,1353675080,1353569288,1353708585,1352989738,-794531798,-253466326,-244975062,-181941702,-261648886,-251817462,1643950601,1643676168,1635287592,1631236648,1614455336,-532962008,-533146551,-535247669,1612235995,1611291835,1661607337,1649023657,1653226137,1653292684,1653159567,-490130802,-488967746,-472129362,-504782546,-504855777,-479686131,-500653556,-500653540,-500583896,-483724760,-529859288,-454391767,-453343109,-460683110,-460801894,-523721590,-532111158,-536284982,-469057286,-468041494,-415339287,-428987927,-1502709031,-1494332789,-1498723701,-1364599093,-1343687989,-1342639541,-1353125253,-1369709975,-1361550740,-1359468820,-1359401067,-1368782409,-1385558874,-332725082,-467073866,-467066722,-462872418,-454303586,1705946207,1739435021,1739368463,1726261519,2003090703,1898364223,1898896503,1898858999,1903040951,1903102901,1928268711,1928007335,1659524055,1651405057,1651359745,1651298352,1634525236,1617749300,1617657364,1617581572,1617822476,1617690940,1627144492,-526597656,-460403224,-460420375,-460539189,-460805558,-406275574,-435511782,-435514870,-434458086,-432430486,-416766742,-332864338,-462855010,-467136369,-449314676,-411434820,-486918996,-487711236,-491909556,-1297662388,-1314574754,-1331403042,-1331419458,-1867223378,-1865128218,-1873492250,-1877031966,-1870728894,-1334910973,-1251221504,-1217684480,-1238464208,-1238459904,-1238435264,-1238435136,-164962624,-160939292,-152554843,-152554843,-160816505,-227006553,-495432541,-512178014,-520181566,1626249218,1626258434,1617867778,1613144067,1613078545,1630315808,1647097120,1647887648,1645855012,1649098980,-498515796,-498577224,-431468104,-422871368,-439452935,-326206901,-325133814,-325190902,-325261286,-321363942,-331849717,-315027367,-282459672,-286653720,-290770323,-408411265,-443014838,-455596982,-523752214,-1312159574,-242333254,-242332790,-242693238,-203896438,-210193270,-247689078,-514031478,-511737638,-479293398,-479289297,-516956108,-516988924,-517332716,-265670364,-265681107,-265745553,-261551363,-202429699,-223465956,-760344052,-760409592,-760458744,-1834163640,-1834160391,-1048794390,-734094678,-734082390,-734115174,-734264694,-735833654,-731615144,-706453396,-676962068,-706322220,-706315068,-705299579,-671827289,-692802906,-151602258,-159990322,-164133426,-148527355,-181947884,-265903563,1613079061,1613025813,1613586999,1630500135,1664043055,-488028113,-475281153,-475346737,1656417487,1660592335,1658552523,1658437867,1657324393,1658377001,1650057769,1648026169,1646978313,1630137353,1613294601,1618988073,1625211945,1624916248,1616462088,1612198664,1631069704,1648045608,1652181736,-492877144,-493004101,-490964086,-507711350,-524758902,-1325797206,-1336254294,-1340464982,-1336270418,-254070018,-256171403,-240426444,-509057476,-504824292,-513218036,-517428468,-517297400,-482432744,-482505448,-484668408,-484651960,-516373031,-1591060821,-1607847250,-1602608466,-1535565138,-1260907890,-1265040690,-1265101603,-1262999508,-1767364564,-1767299044,-1767233528,-2039858168,-2039807928,-2039676584,-2035334167,-2018585878,-1800428886,-1796426054,-1871934886,-802317798,-802317602,-802243698,-802247794,-215374450,-232197698,-232210258,-232070994,-499457625,-495263065,-487918861,-1578437118,-1595281914,-1595349498,-1599547858,-1599540690,-1528278738,-1536667607,-1536663496,-1528171208,-1528115432,-1376073016,-1352992120,-1374819704,-1370702872,-1361794837,-1365994374,-1376464418,-1405688882,-1405689122,-1405717850,-1540488282,-1540422222,-1536358255,-1527965520,-1246947088,-1245889520,-1229118464,-1296161532,-222420212,-218214899,-218150370,-218314450,-243476434,-533149586,1614401790,1614606470,1612505222,1610924198,1611056038,1665553062,1648784066,1657152198,1652957710,1653940764,-225172952,-222556632,-254014936,-1336116648,-1340544520,-1327515400,-1262581624,-1262713717,-1129545526,-1112763910,-1074814230,-1104502038,-1104481558,-1104542994,-1104538642,-1372704282,-1351740058,-306377673,-325310193,-56874737,2123901709,1591421452,1448753692,1444545884,1444622556,1377304780,307773624,318349464,314227849,837458057,808356045,807897213,807902269,807776557,808755501,1882497837,1614710292,1613680132,1613430324,-516948444,-479404188,-475214236,-508768651,-458302778,-458298682,-319821114,-1402144538,-1402143642,-1402416026,-1402448786,-1402309522,-1402330779,-1511381404,-420788484,-420981060,-420976964,-429363304,-432509047,-432378742,-428189558,-487061318,-503838534,-252048246,-1326830453,-1326816055,-1326811784,-1330915800,-1263944152,-1263948260,-1263948275,-1247234545,-1251438034,-1255353818,-1590902490,-1607643034,-1607568130,-1607582610,-1595011730,-520222210,-503502454,-486790774,1650141322,1650133131,1918372009,1918373032,1925920168,1926960060,1929056861,1928016397,854155791,317219591,296677127,279879431,284088068,1349174020,1361658396,1361637928,1344840488,-253188824,-256272088,-256145144,-256075000,-256075256,-256599253,-503999190,-478822358,-499859414,-432246742,-465772246,-465640918,-463547846,-455161334,-304559606,-277288374,-281478450,-366425442,-1423289674,-1452650058,-1465225050,-1196805978,-1196805961,-1196810043,-1191564095,-1736823359,-1739051679,-1730663065,-1734859545,-1734860601,-1734709179,-1650801652,-1629830100,-1629760212,-1636258536,-1636257976,-1636258232,-1099330856,-1099329813,-1099389270,-1100438870,-1104620614,-1104625526,-30752630,-30744421,-47567719,-64345895,-60151605,-51770934,-190248598,-190050518,-190303942,-172416758,-172400370,-174464706,-174481362,-442978259,-438783892,-445075348,-449216264,-415526408,-417688968,-485846488,-519323096,-519388632,-519313880,-485986776,-480482520,-1562576856,-1564686295,-1547778981,-471187253,-528756533,-530919222,-523320342,-523348374,-523348374,-1588822455,-1559429559,-1555267976,-1570998680,-1571024312,-503573944,-453176632,-454151511,-458345558,-458280534,-454282102,-454280006,-177992534,-169354070,-190382902,-190530550,-190532342,-56319478,-51928550,-60382678,-64511190,-1121614486,-1087992598,-1367955222,-1359566597,-1363755831,-1094930360,-1099132856,-1103323064,-1103175320,-1103223832,-1103223828,-1099036756,-1075115099,-1079440458,-5698682,-559203962,-541251198,1475620274,1467250162,1463152706,1429315586,389128194,909353987,909288449,572689408,572687360,572686336,1663533088,1613201440,1613545508,1613512748,1613501736,1617763816,1626803177,1622482603,1622417066,1620850362,1692149386,1683304074,1691758234,-459928918,-457438790,-190314038,-139969462,-672455414,-731225330,-722803930,-727064286,-727142110,-189226974,-189161423,-169167856,-152396736,-227898176,-232092544,-232092544,-232078208,-232110159,-147974493,-198367581]
    from app.main.model.audio import Audio
    from sqlalchemy import text
    cmd = """
      SELECT audio_similarity_functions();
      SELECT * FROM (
        SELECT getscore(chromaprint_fingerprint, :chromaprint_fingerprint)
        AS score FROM audios
      ) f
      WHERE score <= :threshold
      ORDER BY score ASC
    """
    matches = db.session.execute(text(cmd), dict(**{
        'chromaprint_fingerprint': fingerprint,
        'threshold': 10000,
    }, **{})).fetchall()

@manager.command
def init_simple_perl_function():
  with app.app_context():
    sqlalchemy.event.listen(
      db.metadata,
      'before_create',
      DDL("""
        CREATE OR REPLACE LANGUAGE plperl;
      """)
    )
    # sqlalchemy.event.listen(
    #   db.metadata,
    #   'before_create',
    #   DDL("""
    #     DROP FUNCTION Test(integer[], integer[]);
    #   """)
    # )
    sqlalchemy.event.listen(
      db.metadata,
      'before_create',
      DDL("""
        CREATE OR REPLACE FUNCTION functions() RETURNS void
        AS $$
            $_SHARED{maxindex} = sub {
                my @x=@{ $_[0]; };
                $maxi = 0;
                for $i (1..scalar(@x)-1) {
                	if (@x[$i]>@x[$maxi]) {
                		$maxi = $i;
                	}
                }
                return $maxi;
            };
            $_SHARED{test2} = sub {
                my @x=@{ $_[0]; };
                my @y=@{ $_[1]; };
                return 0.8;
            };
        $$
        LANGUAGE plperl;
      """)
    )
    sqlalchemy.event.listen(
      db.metadata,
      'before_create',
      DDL("""
        CREATE OR REPLACE FUNCTION Test(integer[], integer[]) RETURNS float
        AS $$
            my @x=@{ $_[0]; };
            my @y=@{ $_[1]; };
            my $maxindex = $_SHARED{maxindex};
            return &$maxindex(\@x);
        $$
        LANGUAGE plperl;
      """)
    )
    db.create_all()



@manager.command
def init_perl_functions():
  with app.app_context():
    sqlalchemy.event.listen(
      db.metadata,
      'before_create',
      DDL("""
        CREATE OR REPLACE LANGUAGE plperl;
      """)
    )
    # DO NOT EDIT HERE.
    # Please see the reference implementations at /extra/audio_simliarity
    # Edit those implementations and ensure output is correct for the test data there.
    sqlalchemy.event.listen(
      db.metadata,
      'before_create',
      DDL("""
        CREATE OR REPLACE FUNCTION audio_similarity_functions() RETURNS void
        AS $$
            $_SHARED{correlation} = sub {
                my @x=@{ $_[0]; };
                my @y=@{ $_[1]; };
                my $len=scalar(@x);
                if (scalar(@x) > scalar(@y)) { 
                   $len = scalar(@y);
                }
                my $covariance = 0;
                my $i, my $bits, my $xor, my $convariance;
                for $i (0..$len-1) {
                   $bits=0;
                   $xor=(int($x[$i]) ^ int($y[$i]));
                   $bits=$xor;
                   $bits = ($bits & 0x55555555) + (($bits & 0xAAAAAAAA) >> 1);
                   $bits = ($bits & 0x33333333) + (($bits & 0xCCCCCCCC) >> 2);
                   $bits = ($bits & 0x0F0F0F0F) + (($bits & 0xF0F0F0F0) >> 4);
                   $bits = ($bits & 0x00FF00FF) + (($bits & 0xFF00FF00) >> 8);
                   $bits = ($bits & 0x0000FFFF) + (($bits & 0xFFFF0000) >> 16);
                   $covariance +=32 - $bits;
                }
                $covariance = $covariance / $len;
                return $covariance/32;
            };
            $_SHARED{crosscorrelation} = sub {
                my @x=@{ $_[0]; };
                my @y=@{ $_[1]; };
                my $offset=$_[2];
                my $min_overlap=$_[3]; #Defaults to span (20)
                if ($offset > 0) {
                    @x = @x[$offset..scalar(@x)-1]
                } if ($offset < 0) {
                    $offset *= -1;
                    @y = @y[$offset..scalar(@y)-1]
                }
                if (scalar(@x)<$min_overlap || scalar(@y) < $min_overlap) {
                    # Error checking in main program should prevent us from ever being
                    # able to get here.
                    return 0;
                 }
                my $correlation = $_SHARED{correlation};
                return &$correlation(\@x, \@y);
            };
            $_SHARED{compare} = sub {
                my @x=@{ $_[0]; };
                my @y=@{ $_[1]; };
                my $crosscorrelation = $_SHARED{crosscorrelation};
                my $span=$_[2];
                if ($span > scalar(@x) || $span > scalar(@y)){
                	$span=scalar(@x)>scalar(@y)? scalar(@y) : scalar(@x);
                	$span--;
                }
                my $min_overlap = $span;
                my @corr_xy, my $offset;
                for $offset (-1*$span..$span){
                	push @corr_xy, &$crosscorrelation(\@x, \@y, $offset, $min_overlap);
                }
                return @corr_xy;
            };
            $_SHARED{maxindex} = sub {
                my @x=@{ $_[0]; };
                my $maxi = 0;
                my $i;
                for $i (1..scalar(@x)-1) {
                	if ($x[$i]>$x[$maxi]) {
                		$maxi = $i;
                	}
                }
                return $maxi;
            };
        $$
        LANGUAGE plperl;
      """)
    )
    # DO NOT EDIT HERE.
    # Please see the reference implementations at /extra/audio_simliarity
    # Edit those implementations and ensure output is correct for the test data there.
    # This returns a similarity metric where 1.0 indicates a perfect match
    sqlalchemy.event.listen(
      db.metadata,
      'before_create',
      DDL("""
        CREATE OR REPLACE FUNCTION get_audio_chromaprint_score(integer[], integer[]) RETURNS float
        AS $$
            my @first=@{ $_[0]; };
            my @second=@{ $_[1]; };
            if (scalar(@first) > 0 && scalar(@second) > 0 && scalar(@first)*0.8 <= scalar(@second) && scalar(@first)*1.2 >= scalar(@second)) {
                my $span=20;
                my $compare = $_SHARED{compare};
                my @corr = &$compare(\@first, \@second, $span);
                my $maxindex = $_SHARED{maxindex};
                my $max_corr_index = &$maxindex(\@corr);
                return $corr[$max_corr_index]
            }
            return 0.0
        $$
        LANGUAGE plperl;
      """)
    )
    sqlalchemy.event.listen(
      db.metadata,
      'before_create',
      DDL("""
      CREATE EXTENSION IF NOT EXISTS vector;
      """)
    )
    db.create_all()

@manager.command
def run():
  """Runs the API server."""
  port = os.getenv('ALEGRE_PORT', 3100)
  if json_logging._current_framework is None:
    json_logging.init_flask(enable_json=True)
    json_logging.init_request_instrument(app)
  app.run(host='0.0.0.0', port=port, threaded=True)

@manager.command
def run_model():
  """Runs the model server."""
  if config_name == "test":
      model_config = json.load(open('./model_config_test.json')).get(app.config["MODEL_NAME"], {})
  else:
      model_config = json.load(open('./model_config.json')).get(app.config["MODEL_NAME"], {})
  SharedModel.start_server(
    model_config['class'],
    model_config['key'],
    model_config['options']
  )


@manager.command
def run_video_matcher():
  """Runs the video matcher."""
  VideoMatcher.start_server()

@manager.command
def init():
  """Initializes the service."""
  # Create ES indexes.
  es = OpenSearch(app.config['ELASTICSEARCH_URL'])
  try:
    if config_name == 'test':
      es.indices.delete(index=app.config['ELASTICSEARCH_SIMILARITY'], ignore=[400, 404])
    es.indices.create(index=app.config['ELASTICSEARCH_SIMILARITY'])
  except TransportError as e:
    # ignore already existing index
    if e.error == 'resource_already_exists_exception':
      pass
    else:
      raise
  es.indices.put_mapping(
    body=json.load(open('./elasticsearch/alegre_similarity.json')),
    # include_type_name=True,
    index=app.config['ELASTICSEARCH_SIMILARITY']
  )
  init_indices()
  # Create database.
  with app.app_context():
    if not database_exists(db.engine.url):
      create_database(db.engine.url)

    if config_name == 'test':
      db.drop_all()

    sqlalchemy.event.listen(
      db.metadata,
      'before_create',
      DDL("""
        CREATE OR REPLACE FUNCTION bit_count_image(value bigint)
        RETURNS double precision
        AS $$ SELECT 1.0-length(replace(value::bit(64)::text,'0',''))::float/length(value::bit(64)::text); $$
        LANGUAGE SQL IMMUTABLE STRICT;
      """)
    )
    sqlalchemy.event.listen(
      db.metadata,
      'before_create',
      DDL("""
         CREATE OR REPLACE FUNCTION bit_count_pdq(value bit(256))
         RETURNS double precision
         AS $$ SELECT 1.0-length(replace(value::text,'0',''))::float/length(value::text); $$
         LANGUAGE SQL IMMUTABLE STRICT;
       """)
    )
    sqlalchemy.event.listen(
      db.metadata,
      'before_create',
      DDL("""
        CREATE OR REPLACE FUNCTION bit_count_audio(value bit(128))
        RETURNS double precision
        AS $$ SELECT 1.0-length(replace(value::text,'0',''))::float/length(value::text); $$
        LANGUAGE SQL IMMUTABLE STRICT;
      """)
    )
    db.create_all()

@manager.command
def test(pattern='test*.py'):
  """Runs the unit tests."""
  tests = unittest.TestLoader().discover('app/test/', pattern=pattern)
  result = unittest.TextTestRunner(verbosity=2).run(tests)
  return 0 if result.wasSuccessful() else 1

@manager.command
def phash(path):
  """Computes the phash of a given image."""
  im = Image.open(path).convert('RGB')
  phash = compute_phash_int(im)
  print(phash, "{0:b}".format(phash), sep=" ")

@manager.command
def run_rq_worker():
  redis_server = redis_client.get_client()
  with Connection(redis_server):
      qs = ['default']
      w = Worker(qs)
      w.work()
if __name__ == '__main__':
  manager.run()
