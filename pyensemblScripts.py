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
# Colors
PC = pyensembl.PC

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
                                      help = "Search entries "
                                      "for a given species or strain")
    sp_search.add_argument("species", metavar = "SPECIES", type = str,
                           help = "Query string for the species or strain")
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
    # Look for database files
    files = [x for x in os.listdir(DB_FOLDER) if x.startswith(".pyensembl-bacteria-species.")]
    files.sort()
    if len(files) > 0:
        dbFile = files[-1]
        print(PC.G + "Database file used: %s" % dbFile + PC.E)
    else :
        print(PC.F + "No database file found.\nRun \"pyensembl refresh\" first." + PC.E)
        sys.exit()
    # Perform the search
    species = pyensembl.loadJson(os.path.join(DB_FOLDER, dbFile))
    species = [x for x in species["species"] if args.species.lower() in x["name"].lower()]
    print(PC.G + "Species found: %i" % len(species) + PC.E)
    spNames = [x["name"] for x in species]
    spNames.sort()
    for sp in spNames:
        print(PC.Y + "    " + sp + PC.E)
        
### ** Main Refresh

def main_refresh(args, stdout, stderr):
    if args.check:
        # Look for database files
        files = [x for x in os.listdir(DB_FOLDER) if x.startswith(".pyensembl-bacteria-species.")]
        print(PC.G + "Database files found in %s (%i)" % (DB_FOLDER, len(files)) + PC.E)
        for f in files:
            print(PC.Y + "    " + f + PC.E)
    if not args.check:
        # Download information using REST
        speciesData = pyensembl.downloadBacteriaSpecies()
        dbFile = os.path.join(DB_FOLDER, ".pyensembl-bacteria-species." +
                              pyensembl.fileTimestamp())
        pyensembl.saveJson(speciesData, dbFile)
