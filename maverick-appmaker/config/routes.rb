Rails.application.routes.draw do
  resources :apps do
    resources :flows do
      resources :panels
    end
  end
  # post '/apps/:app_id/flows/:flow_id/panels/:panel_id/generate_sql_query', to: "panels#generate_sql_query"
  root "apps#index"
  # Define your application routes per the DSL in https://guides.rubyonrails.org/routing.html

  # Defines the root path route ("/")
  # root "articles#index"
end
