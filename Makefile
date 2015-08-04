### * Variables

PYTHON_MODULE=pyensembl

### * Help

help:
	@echo "Makefile for the $(PYTHON_MODULE) Python module                "
	@echo "                                                               "
	@echo "Type \"make <target>\" where <target> is one of the following: "
	@echo "                                                               "
	@echo "  install     Install the module                               "
	@echo "  uninstall   Uninstall the module                             "

### * Targets

### ** install
install:
	pip install --upgrade --user .

### ** uninstall
uninstall:
	pip uninstall -y $(PYTHON_MODULE)
