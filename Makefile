DIR = .
INPUTS = $(shell find $(DIR) -name *.ipynb)
OUTPUTS = $(patsubst $(DIR)/%.ipynb,$(DIR)/%.html,$(INPUTS))

all: $(OUTPUTS)

check:
	@echo $(DIR)
	@echo $(INPUTS)
	@echo $(OUTPUTS)

%.html: %.ipynb
	./process-nb $<
