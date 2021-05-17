.PHONY: init
init:
	# Create conda env
	conda env create -f environment.yml -p env

.PHONY: up
up:
	# Update conda env
	conda env update -f environment.yml -p env --prune

.PHONY: rm
rm:
	# Remove conda env
	conda deactivate
	rm -rf env
