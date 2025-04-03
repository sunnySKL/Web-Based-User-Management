TEXFILE = special_circumstance.tex
PDFFILE = special_circumstance.pdf

all: $(PDFFILE)

$(PDFFILE): $(TEXFILE)
	pdflatex -output-directory $(dir $(TEXFILE)) $(TEXFILE)
	pdflatex -output-directory $(dir $(TEXFILE)) $(TEXFILE)

clean:
	rm -f $(PDFFILE) *.aux *.log *.out
