require 'mlg_mt'

class Api::V1::MtController < Api::V1::BaseApiController
  include MtDoc

  before_filter :start_mt

  def index
    text, from, to = params[:text], params[:from], params[:to]
    languages = @mt.languages

    if text.blank? || from.blank? || to.blank?
      render_error 'Please provide text, source language and target language', 'MISSING_PARAMETERS'
    
    elsif !languages.include?(from) || !languages.include?(to)
      render_error 'Language not supported', 'INVALID_VALUE'

    else
      @translation = @mt.translate(text, from, to)
      render_success 'mt', @translation
    end
  end

  def languages
    @languages = @mt.languages
    render_success 'languages', @languages
  end

  private

  def start_mt
    @mt = Mlg::Mt.new
  end
end
