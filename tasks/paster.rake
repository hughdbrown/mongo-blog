namespace :paster do
    desc "Run paster server"
    task :run do
      FileUtils.cd("src") do
        sh("python blog.py")
      end
    end
end

