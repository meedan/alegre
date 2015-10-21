class ApiConstraints
  def initialize(options)
    @version = options[:version]
    @default = options[:default]
  end

  def matches?(req)
    @default || req.headers['Accept'].include?(ApiConstraints.accept(@version))
  end

  def self.accept(version = 1)
    "application/vnd.meedan.v#{version}"
  end
end
