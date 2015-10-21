namespace :meedan do
  namespace :api_keys do

    task delete_expired: :environment do
      puts "There are #{ApiKey.count} keys. Going to remove the expired ones..."
      ApiKey.destroy_all('expire_at < ?', Time.now)
      puts "Done! Now there are #{ApiKey.count} keys."
    end

    task create: :environment do
      api_key = ApiKey.create!
      puts "Created a new API key with access token #{api_key.access_token} and that expires at #{api_key.expire_at}"
    end
  end
end
