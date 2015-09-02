# Written usingn resources from:
# https://packaging.python.org/en/latest/distributing.html#working-in-development-mode
# https://github.com/pypa/sampleproject/blob/master/setup.py

from setuptools import setup, find_packages

setup(name = "pyensembl",
      version = "0.0.2",
      py_modules = ["pyensembl", "pyensemblScripts"],
      entry_points =  {
          "console_scripts" : [
              "pyensembl=pyensemblScripts:main"
          ]
      }
)
