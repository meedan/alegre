#encoding: utf-8 
require 'rubypython'

class Api::V1::LanguagesController < Api::V1::BaseApiController

  include LanguagesDoc

  def identification
    if params[:text].blank?
      render_parameters_missing
    else
    	str = params[:text].to_s
    	@language =  DYSL.classifyReturnAll(str,STOPWORDS_PATH).rubify
    	render_success 'language', @language
    end
  end

  def sample
    if params[:text].blank? or params[:language].blank?
      render_parameters_missing
    else
    	str = params[:text].to_s
    	lang = params[:language].to_s
    	@ret = DYSL.add_sample(str, lang, MODEL_FILE).rubify
    	render_success 'success', @ret
    end
  end

  def language
  	@list =  DYSL.listLanguages().rubify
  	render_success 'language', @list
  end

end
