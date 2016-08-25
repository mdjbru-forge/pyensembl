### * Description

# Entry points for the command line scripts

### * Wishlist

# pyensembl search "Escherichia coli" --index ensembl.index.html --download
# pyensembl search "Escherichia coli" > ecoli.index
# pyensembl search "Escherichia coli" -- download
# pyensembl search "Escherichia coli" -c

### * Setup

### ** Import

import os
import sys
import argparse
import random
import pyensembl as pyensembl

### ** Parameters

DB_FOLDER = "~"
DB_FOLDER = os.path.expanduser(DB_FOLDER)

### * Parser

def makeParser() :
    """Prepare the parser

    Returns:
        ArgumentParser: An argument parser

    """
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    ### ** Search and download EMBL files
    sp_search = subparsers.add_parser("search",
                                      help = "Search and download EMBL entries "
                                      "for a given species or strain")
    sp_search.add_argument("species", metavar = "SPECIES", type = str,
                           help = "Query string for the species or strain")
    sp_search.add_argument("-i", "--index", metavar = "HTMLFILE", type = str,
                           help = "Html index file from Ensembl (if not specified, "
                           "the program will download the page from "
                           "http://bacteria.ensembl.org/info/website/ftp/index.html)")
    sp_search.add_argument("-d", "--download", action = "store_true", 
                           help = "Download the EMBL files. If not specified, "
                           "just write the species accession numbers to stdout.")
    sp_search.add_argument("-o", "--outDir", metavar = "DIR", type = str,
                           default = ".", 
                           help = "Destination directory for downloading ("
                           "default: current directory)")
    sp_search.add_argument("-c", "--count", action = "store_true",
                           help = "Only send the record count to stdout, not "
                           "the full record information")
    sp_search.set_defaults(action = "search")
    ### ** Refresh bacteria info database
    sp_refresh = subparsers.add_parser("refresh",
                                       help = "Without any argument, Refresh the local "
                                       "information about "
                                       "available bacteria species in Ensembl")
    sp_refresh.add_argument("-c", "--check", action = "store_true",
                            help = "Check for existence of local information about "
                            "bacteria species in Ensembl")
    sp_refresh.set_defaults(action = "refresh")
    ### ** Return
    return parser
    
### * Mains

### ** Main entry point

def main(args = None, stdout = None, stderr = None) :
    """Main entry point

    Args:
        args (namespace): Namespace with script arguments, parse the command 
          line arguments if None
        stdout (file): Writable stdout stream (if None, use `sys.stdout`)
        stderr (file): Writable stderr stream (if None, use `sys.stderr`)

    """
    if args is None :
        parser = makeParser()
        args = parser.parse_args()
    if stdout is None :
        stdout = sys.stdout
    if stderr is None :
        stderr = sys.stderr
    dispatch = dict()
    dispatch["search"] = main_search
    dispatch["refresh"] = main_refresh
    dispatch[args.action](args, stdout, stderr)

### ** Main search

def main_search(args, stdout, stderr) :
    deleteIndex = False
    if args.index is None :
        # Download the index file from Ensembl
        tag = "".join([random.choice("0123456789abcdef") for x in range(6)])
        outFile = "tmp." + tag
        pyensembl.downloadUrl(pyensembl.ENSEMBL_INDEX_URL, outFile)
        args.index = outFile
        deleteIndex = True
    with open(args.index, "r") as fi :
        htmlContent = fi.read()
    EMBLmapping = pyensembl.EMBLspeciesIndex(html = htmlContent)
    if deleteIndex :
        os.remove(args.index)
    EMBLspecies = EMBLmapping.searchSpecies(args.species)
    EMBLtable = EMBLspecies.makeTable()
    EMBLcount = len(EMBLspecies)
    if args.count :
        stdout.write(str(EMBLcount) + "\n")
    else :
        stdout.write(EMBLtable)
    if args.download :
        EMBLspecies.downloadAll(outDir = args.outDir)

### ** Main Refresh

def main_refresh(args, stdout, stderr):
    if args.check:
        # Look for database files
        files = [x for x in os.listdir(DB_FOLDER) if x.startswith(".pyensembl-bacteria-species.")]
        PC = pyensembl.PC
        print(PC.G + "Database files found in %s (%i)" % (DB_FOLDER, len(files)) + PC.E)
        for f in files:
            print(PC.Y + "    " + f + PC.E)
    if not args.check:
        # Download information using REST
        speciesData = pyensembl.downloadBacteriaSpecies()
        dbFile = os.path.join(DB_FOLDER, ".pyensembl-bacteria-species." +
                              pyensembl.fileTimestamp())
        pyensembl.saveJson(speciesData, dbFile)
