namespace :meedan do
  task :error_codes do
    MeedanConstants::ErrorCodes::ALL.each do |name|
      puts name + ': ' + MeedanConstants::ErrorCodes.const_get(name).to_s
    end
  end
end
