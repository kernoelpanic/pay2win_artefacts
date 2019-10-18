FILE ?= markov_chain

LATEX ?= pdflatex

.PHONY: all
all: $(FILE).pdf convert clean 

.PHONY: $(FILE).pdf
$(FILE).pdf: $(FILE).tex
	$(LATEX) $(FILE).tex

convert:
	convert -density 300 $(FILE).pdf -quality 90 $(FILE).png

clean:
	-rm -f $(FILE).aux $(FILE).log 
	-rm -f $(FILE).bbl $(FILE).blg
	-rm -f $(FILE).nav $(FILE).out
	-rm -f $(FILE).toc $(FILE).snm
	-rm -f $(FILE).idx


