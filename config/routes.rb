require 'api_constraints'

Rails.application.routes.draw do
  namespace :api, defaults: { format: 'json' } do
    scope module: :v1, constraints: ApiConstraints.new(version: 1, default: true) do
      get 'languages/identification', to: 'languages#identification'
      post 'languages/sample', to: 'languages#sample'
      get 'languages/language', to: 'languages#language'
    end
  end
end
