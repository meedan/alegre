require 'rubypython'

class Api::V1::LanguagesController < Api::V1::BaseApiController

  include LanguagesDoc

  def classify
    if params[:text].blank?
      render_parameters_missing
    else

	str = params[:text].to_s
	#@language =  DYSL.classifyNOT(str).rubify
	p "MLG !!!!!!!!!!"
	p STOPWORDS_PATH
	@language =  DYSL.classify(str,STOPWORDS_PATH).rubify
	render_success 'language', @language
    end
  end

  def classify3
    wl = WhatLanguage.new(:english, :german, :french, :spanish, :portuguese)
    if params[:text].blank?
      render_parameters_missing
    else
      @language = wl.language(params[:text].to_s)
      render_success 'language', @language
    end
  end
end
