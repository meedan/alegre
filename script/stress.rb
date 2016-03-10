#!/usr/bin/env ruby
require File.dirname(__FILE__) + '/../config/environment'
require 'rubypython'
require 'literate_randomizer'

while true do
  str = LiterateRandomizer.sentence
  language = Alegre::Dysl.new.try_to_classify(str)
  puts str
  puts language.inspect
  puts '-------------------------------------------------------------------'
end
