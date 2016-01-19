require 'api_constraints'

Rails.application.routes.draw do
  namespace :api, defaults: { format: 'json' } do
    scope module: :v1, constraints: ApiConstraints.new(version: 1, default: true) do
	get 'languages/identification', to: 'languages#identification'
	post 'languages/sample', to: 'languages#sample'
	get 'languages/language', to: 'languages#language'
	get 'glossary/terms', to: 'glossary#terms'
	post 'glossary/term', to: 'glossary#term'
	post 'glossary/delete', to: 'glossary#delete'
	post 'dictionary/execute', to: 'dictionary#execute'
	#post 'tm/tuple', to: 'tm#tuple'
	#get 'tm/tuple', to: 'tm#tuple'
	#get 'tm/language_tm', to: 'tm#language_tm'
	#get 'tm/source', to: 'tm#source'
    end
  end
end
