#!/usr/bin/env ruby
require File.dirname(__FILE__) + '/../config/environment'
require 'rubypython'
require 'literate_randomizer'

while true do
  str = LiterateRandomizer.sentence
  language = DYSL.classifyReturnAll(str, STOPWORDS_PATH).rubify
  puts language.inspect
end
