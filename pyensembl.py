### * Description

# Retrieve Ensembl and EMBL bacterial genome files

### * Setup

### ** Import

import sys
import os
import subprocess
import time
from bs4 import BeautifulSoup

### ** Parameters

ENSEMBL_INDEX_URL = "http://bacteria.ensembl.org/info/website/ftp/index.html"

### * Functions

### ** downloadUrl(url, outFile = None)

def downloadUrl(url, outFile = None) :
    """Download the target of an url to an output file

    Args:
        url (str): URL address
        outFile (str): Path to the output file (if None, wget will determine 
          output file itself)

    Returns:
        int: Return code from wget

    """
    command = ["wget"]
    command += [url]
    if outFile is not None :
        command += ["-O", outFile]
    p = subprocess.Popen(command)
    return p.wait()

### ** parseHtmlToAccNum(htmlContent, previousData = None, stderr = None)

def parseHtmlToAccNum(htmlContent, previousData = None, stderr = None) :
    """Parse the content of the html index page from Ensembl into a mapping
    between species and accession numbers

    This parser seems to work fine with the page as it was retrieved from
    http://bacteria.ensembl.org/info/website/ftp/index.html
    on 2015-08-03.

    Args:
        htmlContent (str): Content of the html file
        previousData (dict): If another content was parsed before, the 
          resulting dictionary can be passed here for update
        stderr (file): Stderr stream to write warning messages (if None, use
          sys.stderr)

    Returns:
        dict: Dictionary mapping (species, accession number(s))

    """
    if stderr is None :
        stderr = sys.stderr
    if previousData is None :
        previousData = dict()
    content = BeautifulSoup(htmlContent, "html.parser")
    speciesRows = [x for x in content.find_all("tr") if len(list(x.children)) > 5]
    spAccMapping = dict()
    spAccMapping.update(previousData)
    for r in speciesRows :
        cells = r.find_all("td")
        if len(cells) > 0 :
            assert len(cells) == 9;
            species = cells[0].get_text()
            if "EMBL" in cells[4].get_text() :
                href = cells[4].find("a").get("href")
                accNum = href.split("/view/")[1].split("&display")[0]
                assert not spAccMapping.get(species, False)
                spAccMapping[species] = accNum
            else :
                if species == "" :
                    species = "???"
                try :
                    msg = ("No EMBL entry for species " + species + " (DNA "
                           "link: " + cells[1].find("a").get("href") + ")\n" )
                except :
                    msg = ("No EMBL entry for species " + species + " (row " +
                           str(r) + ")\n" )
                stderr.write(msg)
    return spAccMapping

### ** filterAccNumBySpecies(spAccMapping, species)

def filterAccNumBySpecies(spAccMapping, species) :
    """Filter a dictionary mapping species name to accession number for a 
    given species.

    The provided species name is converted to lower case and search in the keys
    of the dictionary, which are also converted to lower case and have 
    underscores replaced with space characters (so that "Escherichia coli" will
    match "escherichia_coli" for example).

    Args:
        spAccMapping (dict): Mapping between species names and accession 
          numbers (output from parseHtmlToAccNum)
        species (str): Query string

    Returns:
        dict: A subset of the original dictionary matching the query string

    """
    o = dict()
    species = species.lower()
    for (k, v) in spAccMapping.items() :
        if species in k.lower().replace("_", " ") :
            o[k] = v
    return o

### * Classes

### ** EMBLspeciesIndex

class EMBLspeciesIndex(object) :
    """Class containing the mapping between species and EMBL accessio numbers
    for downloading the species EMBL files
    """

    def __init__(self, html = None, table = None) :
        """HTML content (str) can be provided and will be parsed by the 
        parseIndexHtml method, or a tabular file content can also be provided.

        Args:
            html (str): Html content from an Ensembl index page
            table (str): Tabular content from a table file

        """
        self.mapping = dict()
        assert not (html is not None and table is not None)
        if html is not None :
            self.parseHtml(html)
        if table is not None :
            self.load(table)

    def __len__(self) :
        return len(self.mapping)
        
    def parseHtml(self, content) :
        """Parse an html content from an index page and add it to the current
        mapping

        Args:
            content (str): Html content of an index file from Ensembl
              (e.g. http://bacteria.ensembl.org/info/website/ftp/index.html)
        """
        self.mapping = parseHtmlToAccNum(content, self.mapping)

    def searchSpecies(self, species) :
        """Return a subset of the current mapping as a new instance after
        filtering for a query species using filterAccNumBySpecies()

        """
        o = EMBLspeciesIndex()
        mapping = filterAccNumBySpecies(self.mapping, species)
        o.mapping.update(mapping)
        return o

    def load(self, inFile) :
        """Load the content of a tabular file to update the current mapping

        Args:
            inFile (str): Path to the input file

        """
        o = dict()
        with open(inFile, "r") as fi :
            for line in fi :
                line = line.strip().split("\t")
                o[line[0]] = line[1]
        self.mapping.update(o)
    
    def write(self, outFile) :
        """Write the current mapping to a tabular file

        Args:
            outFile (str): Path to the output file

        """
        with open(outFile, "w") as fo :
            fo.write(self.makeTable())

    def makeTable(self) :
        """Produce a table for the current mapping

        """
        o = ""
        for (k, v) in self.mapping.items() :
            o += "\t".join([k, v]) + "\n"
        return o
                        
    def downloadAll(self, outDir = ".", force = False) :
        """Download all the EMBL records present in the mapping.

        Args:
            outDir (str): Path to the output directory (default: ".")
            force (bool): Download a file even if already present on disk?

        """
        for (k, v) in self.mapping.items() :
            outFile = os.path.join(outDir,
                                   ".".join([k, v]).replace(" ", "-").replace("/", "<SLASH>") +
                                   ".EMBL.gz")
            if not os.path.isfile(outFile) :
                url = "http://www.ebi.ac.uk/ena/data/view/" + v + "&display=text&download=gzip"
                downloadUrl(url, outFile)
                time.sleep(10)
