#encoding: utf-8 
require 'rubypython'

class Api::V1::GlossaryController < Api::V1::BaseApiController

  include GlossaryDoc

  def term
    if params[:text].blank?
      render_parameters_missing
    else
	str = params[:data].to_s
	#@language =  DYSL.classifyReturnAll(str,STOPWORDS_PATH).rubify
	p str
	render_success 'term', '@language'
    end
  end


end
