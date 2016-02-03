#encoding: utf-8 
require 'rubypython'

class Api::V1::TmController < Api::V1::BaseApiController

  include TMDoc

  def tuple
    if params[:data].blank?
      render_parameters_missing
    else
      str = params[:data].to_s
      render_success 'tuple', '@language'
    end
  end

  def language
    render_success 'language', '@list'
  end

  def source
    render_success 'source', '@list'
  end

end
