namespace :lapis do
  namespace :docker do
    task :run do
      puts %x(./docker/run.sh)
    end

    task :shell do
      puts %x(./docker/shell.sh)
    end
  end
end
