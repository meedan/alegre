require 'api_constraints'

Rails.application.routes.draw do
  namespace :api, defaults: { format: 'json' } do
    scope module: :v1, constraints: ApiConstraints.new(version: 1, default: true) do
      get 'languages/identification', to: 'languages#identification'
      post 'languages/sample', to: 'languages#sample'
      get 'languages/language', to: 'languages#language'
      get 'glossary/terms', to: 'glossary#terms'
      post 'glossary/term', to: 'glossary#term'
      delete 'glossary/delete', to: 'glossary#delete'
      get 'dictionary/terms', to: 'dictionary#terms'
    end
  end
end
