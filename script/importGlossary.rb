require File.dirname(__FILE__) + '/../config/environment'
require 'csv'
require 'alegre_client'
require 'optparse'

def add_term(channel_id, term, lang1, definition, dst_term, dst_lang, dst_definition, host, alegre_token)
  #lang = BRIDGE_CONFIG['supported_language_fallbacks'][dst_lang] || dst_lang
  term = { 
    term: term,
    lang: lang1, 
    definition: definition,
    translations: [
      { lang: dst_lang, definition: dst_definition, term: dst_term }
    ],  
    context: { page_id: channel_id, 'data_source' => 'glossary' }
  }
  req = AlegreClient::Request.post_glossary_term(host, { data: term.to_json, should_replace: 0 }, alegre_token)
  req['type'] === 'success'
end


#ruby importGlossary.rb -f 'import.csv' -h 'http://localhost:3000' -t '658a12f0dafd1c6dd0905d4e9848fb30'


options = {:host => nil, :csv => nil, :token => nil}

parser = OptionParser.new do|opts|
  opts.banner = "Usage: importGlossary.rb [options]"

  opts.on('-f', '--file import.csv', 'CSV file') do |csv|
    options[:csv] = csv;
  end

  opts.on('-h', '--host http://localhost:3000', 'Alegre host and port') do |host|
    options[:host] = host;
  end

  opts.on('-a', '--token Alegre Token', 'Token') do |token|
    options[:token] = token;
  end
end

parser.parse!

if options[:csv] == nil
  print "Enter CSV file: "
    options[:csv] = gets.chomp
end


if options[:token] == nil
  print "Enter Alegre's token: "
    options[:token] = gets.chomp
end

if options[:host] == nil
  print "Enter Alegre's host: "
    options[:host] = gets.chomp
end

csvFile = CSV.read(options[:csv].to_s, headers:true)
host = options[:host] 
alegre_token = options[:token] 
definition=''

csvFile.each do |row|
  add_term(row['Page ID'] , row['Source Term'] , row['Source Language'][0..1].upcase  , definition, row['Target Term'], row['Target Language'][0..1].upcase , row['Target Definition'],  host, alegre_token)
end
