#encoding: utf-8 
require 'rubypython'
require 'retriable'

class Api::V1::LanguagesController < Api::V1::BaseApiController

  include LanguagesDoc

  def identification
    if params[:text].blank?
      render_parameters_missing
    else
      str = params[:text].to_s
      if params[:languages].blank?
        langs = "[]"
      else
        langs = params[:languages].to_s
      end
      Retriable.retriable do
        @language = Alegre::LangId.new.classify(str,langs)
      end
      render_success 'language', @language
    end
  end

  def sample
    if params[:text].blank? or params[:language].blank?
      render_parameters_missing
    else
      str = params[:text].to_s
      lang = params[:language].to_s
      Retriable.retriable do
        @ret = Alegre::LangId.new.add_sample(str, lang)
      end
      if @ret
        render_success 'success', @ret
      else
        render_error('Could not add', 'INVALID_VALUE', status = 400)
      end
    end
  end

  def delete_sample
    if params[:text].blank? or params[:language].blank?
      render_parameters_missing
    else
      str = params[:text].to_s
      lang = params[:language].to_s
      Retriable.retriable do
        @ret = Alegre::LangId.new.delete_sample(str, lang)
      end
      if @ret
        render_success 'success', @ret
      else
        render_error('Could not delete', 'INVALID_VALUE', status = 400)
      end
    end
  end

  def language
    Retriable.retriable do
      @list = Alegre::LangId.new.list_languages
    end
    render_success 'language', @list
  end


  def normalize
    if params[:text].blank?
      render_parameters_missing
    else
      str = params[:text].to_s
      @text = Alegre::LangId.new.normalize(str)
      render_success 'text', @text
    end
  end

end
