# -----------------------------------------------------
# Lint tasks.
# -----------------------------------------------------
namespace "lint" do
  LINT_DIR="tasks/lint"

  desc "Run the pylint analysis tool."
  task :pylint => ["setup:lint"] do
    sh "pylint --rcfile=#{LINT_DIR}/pylintrc #{CLIENT_CODE_DIR}/*.py"
    notice("pyLint passed")
  end

  desc "Run the pep8 analysis tool."
  task :pep8 => ["setup:lint"] do
    sh "pep8 --repeat --count --ignore=E501 #{CLIENT_CODE_DIR}"
    notice("pep8 passed")
  end

  desc "Run coverage"
  task :pycoverage => ["setup:lint"] do
    #check_env_var(["WORKSPACE"])
    #
    FileUtils.cd(CLIENT_CODE_DIR) do
      output = File.join('.', "nosetests.xml")
      sh("nosetests -v --with-xunit --xunit-file=#{output} --with-coverage --cover-package=.")
    #  #sh("coverage xmli --omit=* --include=wgen/fssclient")
      notice("coverage passed")
    end
  end

  desc "Run pyflakes"
  task :pyflakes => ["setup:lint"] do
    sh("pyflakes #{CLIENT_CODE_DIR}")
    notice("pyflakes passed")
  end
end

desc "Run all code analysis tools."
task :lint => [
    "lint:pep8", 
    "lint:pylint",
    "lint:pycoverage",
    # pyflakes does not run in python 3+
    #"lint:pyflakes"
]
