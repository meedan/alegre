require File.join(File.expand_path(File.dirname(__FILE__)), '..', 'test_helper')

class AlegreLangidTest < ActiveSupport::TestCase
  test "should not crash if input is bad" do
    assert_nothing_raised do
      Alegre::LangId.new.classify(nil)
    end
  end

  # http://errbit.test.meedan.net/apps/5627efca8583c6ba53000086/problems/5752689e8583c6af52000329
  test "should not trigger 'value error' for Chinese input" do
    inputs = [
      'ふるさと納税HST/辻鐵工所 マフラー 品番：055-155 ダイハツ ミラ L710S（4WD）: automobile motorcar オートモービル モーターカー カー 車 自動車 車両 消音器 サイレンサー… https://t.co/rYVHIcHFfn #Test',
      '平成 27 年度 宇部市ふるさと納税報告書: 平成 27 年度. 宇部市ふるさと納税報告書. 宇部の木（第 26 回ＵＢＥビエンナーレ大賞作品）. 平成 28 年 6 月. 宇部市 総合政策部 政策企画課 ... https://t.co/3dnfc18mKy #Test',
      'ニコニコ動画の再生数を増やします。5000再生:1500円 10000再生:3000円 20000再生:6000円 詳しくはDMで　#niconico #ニコニコ #ニコ動画 #工作 #再生工作LIVE*Finals Cleveland v/s Warriors Game 2 …',
      'いま話題のワード：#uetokyo / ガンホー売却 / モハメド・アリ 死去 / #aniaca / #サタニック / 履正社 / #サカスプ / 雲雀恭弥セット / #ミリオンロック / Muhammad Ali',
      'ニコニコ動画の再生数を増やします。5000再生:1500円 10000再生:3000円 20000再生:6000円 詳しくはDMで　#niconico #ニコニコ #ニコ動画 #工作 #再生工作Muhammad Ali, Boxing Legend And Anti-War I…',
      'ニコニコ動画の再生数を増やします。5000再生:1500円 10000再生:3000円 20000再生:6000円 詳しくはDMで　#niconico #ニコニコ #ニコ動画 #工作 #再生工作Muhammad Ali, Boxing Legend And Anti-War I…',
      '観音寺市 返礼品６→７４品 2016年06月07日: 観音寺市は、ふるさと納税の返礼品を６品から７４品に大幅に拡大した。あん餅雑煮セットや空き家の管理を委託できるチケットなどユニークな品がそろう。 https://t.co/wDMqUSIueQ #Test',
      'Braun/電気シェーバー シリーズ3 3030s/3030sふるさと納税: Braun/電気シェーバー シリーズ3 3030s/3030s,ふるさと納税,激安大特価！,【新作入荷!!】 https://t.co/P1DER45g3p #Test',
      '【ふるさと納税】これまでもらったお米たち【山形県最上町/北海道沼田町/茨城県行方市】:… https://t.co/EDJUIQYaQe #Test'
    ]
    inputs.each do |input|
      assert_equal [], Alegre::LangId.new.classify(input)
    end
  end

  test "should classify Chinese Simplified" do
    assert_equal "ZH-CHS", Alegre::LangId.new.classify('这是一个测试').first.first
  end

  test "should classify Chinese Traditional" do
    assert_equal "ZH-CHT", Alegre::LangId.new.classify('這是一個測試').first.first
  end

  test "should classify Spanish" do
    assert_equal "ES", Alegre::LangId.new.classify('Este es un teste').first.first
  end

  test "should classify English" do
    assert_equal "EN", Alegre::LangId.new.classify('This is a test').first.first
  end

  test "should classify Portuguese" do
    assert_equal "PT", Alegre::LangId.new.classify('Isto é um teste').first.first
  end

  test "should classify Arabic" do
    assert_equal "AR", Alegre::LangId.new.classify('هذا اختبار').first.first
  end

  test "should classify French" do
    assert_equal "FR", Alegre::LangId.new.classify('c\'est un test').first.first
  end
end
