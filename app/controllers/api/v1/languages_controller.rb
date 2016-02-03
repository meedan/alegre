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
      Retriable.retriable do
        @language = Mlg::Dysl.new.try_to_classify(str)
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
        @ret = Mlg::Dysl.new.add_sample(str, lang)
      end
      render_success 'success', @ret
    end
  end

  def language
    Retriable.retriable do
      @list = Mlg::Dysl.new.list_languages
    end
    render_success 'language', @list
  end
end
