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
import ftplib
import urllib

### ** Parameters

DB_FOLDER = "~"
DB_FOLDER = os.path.expanduser(DB_FOLDER)
# Colors
PC = pyensembl.PC
# EnsemblBacteria
FTP_GENBANK_ROOT = "pub/bacteria/current/genbank/"

### * Parser

def makeParser() :
    """Prepare the parser

    Returns:
        ArgumentParser: An argument parser

    """
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    ### ** Refresh bacteria info database
    sp_refresh = subparsers.add_parser("refresh",
                                       help = "Without any argument, Refresh the local "
                                       "information about "
                                       "available bacteria species in Ensembl")
    sp_refresh.add_argument("-c", "--check", action = "store_true",
                            help = "Check for existence of local information about "
                            "bacteria species in Ensembl")
    sp_refresh.set_defaults(action = "refresh")
    ### ** Search among species
    sp_search = subparsers.add_parser("search",
                                      help = "Search entries "
                                      "for a given species or strain")
    sp_search.add_argument("species", metavar = "SPECIES", type = str,
                           help = "Query string for the species or strain")
    sp_search.add_argument("-g", "--genomes", action = "store_true", 
                           help = "Retrieve information about genomes")
    # sp_search.add_argument("-o", "--outDir", metavar = "DIR", type = str,
    #                        default = ".", 
    #                        help = "Destination directory for downloading ("
    #                        "default: current directory)")
    # sp_search.add_argument("-c", "--count", action = "store_true",
    #                        help = "Only send the record count to stdout, not "
    #                        "the full record information")
    sp_search.set_defaults(action = "search")
    ### ** Get genome information
    sp_genome = subparsers.add_parser("genomes",
                                      help = "Retrieve genomes information, based either "
                                      "on a table containing species information or on a "
                                      "NCBI Taxon Id")
    sp_genome.add_argument("-f", "--file", metavar = "SPECIES_TABLE", type = str,
                           help = "Tab-separated file containing species information")
    sp_genome.add_argument("-t", "--taxonName", metavar = "NCBI_TAXID", type = str,
                           help = "NCBI taxon identifier (e.g. \"Serratia\", "
                           "\"Enterobacteriaceae\"). Information about all available "
                           "genomes beneath this node will be retrieved.")
    sp_genome.set_defaults(action = "genomes")
    ### ** Download genome data
    sp_download = subparsers.add_parser("download",
                                        help = "Download sequence data for a list of "
                                        "genomes")
    sp_download.add_argument("-g", "--genomeList", metavar = "GENOMES_TABLE",
                             type = str, help = "Tab-separated file containing genomes "
                             "information", nargs = 1)
    sp_download.add_argument("-f", "--format", metavar = "FORMAT", type = str,
                             choices = ["genbank"], nargs = 1,
                             help = "Format to retrieve (only \"genbank\" "
                             "implemented for now)")
    sp_download.add_argument("-d", "--dir", metavar = "DEST_DIR", type = str,
                             default = ".",
                             help = "Destination directory")
    sp_download.set_defaults(action = "download")
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
    dispatch["refresh"] = main_refresh
    dispatch["search"] = main_search
    dispatch["genomes"] = main_genomes
    dispatch["download"] = main_download
    dispatch[args.action](args, stdout, stderr)
    
### ** Main refresh

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
        
### ** Main search

def main_search(args, stdout, stderr) :
    # Look for database files
    files = [x for x in os.listdir(DB_FOLDER) if x.startswith(".pyensembl-bacteria-species.")]
    files.sort()
    if len(files) > 0:
        dbFile = files[-1]
        stderr.write(PC.G + "Database file used: %s" % dbFile + PC.E + "\n")
    else :
        stderr.write(PC.F + "No database file found.\nRun \"pyensembl refresh\" first." + PC.E + "\n")
        sys.exit()
    # Perform the search
    species = pyensembl.loadJson(os.path.join(DB_FOLDER, dbFile))
    species = [x for x in species["species"] if args.species.lower() in x["name"].lower() or
               args.species.lower() in x["display_name"].lower()]
    stderr.write(PC.G + "Species found: %i" % len(species) + PC.E + "\n")
    stdout.write(pyensembl.dumpEnsemblInfoSpecies(species))
    
### ** Main genomes

def main_genomes(args, stdout, stderr):
    if (args.file is None and args.taxonName is None):
        stderr.write(PC.F + "Provide either a table of species or a taxon name.\n" +
                     "Type \"pyensembl genomes -h\" for help.\n" + PC.E)
        sys.exit()
    if (args.file is not None and args.taxonName is not None):
        stderr.write(PC.F + "Provide either a table of species or a taxon name " +
                     "(but not both).\n" +
                     "Type \"pyensembl genomes -h\" for help.\n" + PC.E)
        sys.exit()
    if args.file is not None:
        # Load the species info
        info = []
        with open(args.file, "r") as fi:
            header = fi.next().strip().split("\t")
            for line in fi:
                if line.strip() != "":
                    info.append(dict(zip(header, line.strip().split("\t"))))
        stderr.write(PC.G + "Found %i species in %s" % (len(info), args.file) +
                     PC.E + "\n")
        genomes = []
        for sp in info:
            genomes.append(pyensembl.retrieveGenomeInfo(sp["name"]))
    elif args.taxonName is not None:
        genomes = pyensembl.retrieveGenomesTaxonName(args.taxonName)
        stderr.write(PC.G + "Genomes found for %s: %i" % (args.taxonName, len(genomes)) +
                     "\n" + PC.E)
    # Write the output
    stdout.write(pyensembl.dumpEnsemblInfoGenomes(genomes))

### ** Main download

def main_download(args, stdout, stderr):
    # Load genome information
    info = []
    with open(args.genomeList[0], "r") as fi:
        header = fi.next().strip().split("\t")
        for line in fi:
            if line.strip() != "":
                info.append(dict(zip(header, line.strip().split("\t"))))
    stderr.write(PC.G + "%i genomes found" % len(info) + PC.E + "\n")
    # Download the genome data
    # Probably not portable way, but should work for now
    # http://stackoverflow.com/questions/111954/using-pythons-ftplib-to-get-a-directory-listing-portably
    ftp = ftplib.FTP()
    ftp.connect("ftp.ensemblgenomes.org")
    ftp.login() # Anonymous login
    for i, genome in enumerate(info):
        collection = genome["dbname"].split("_collection")[0] + "_collection"
        ftpPath = FTP_GENBANK_ROOT + "/" + collection + "/" + genome["species"]
        ftpDir = []
        ftp.dir(ftpPath, ftpDir.append)
        ftpDir = [x.split(" ")[-1] for x in ftpDir]
        # Keep only files of interest
        ftpDir = [x for x in ftpDir if x not in ["CHECKSUMS", "README"] and "plasmid" not in x]
        # Download
        # http://stackoverflow.com/questions/11573817/how-to-download-a-file-via-ftp-with-python-ftplib
        for target in ftpDir:
            stderr.write(PC.G + "Retrieving %s (%i/%i)" % (genome["species"], i+1, len(info)) + PC.E)
            fo = open(os.path.join(args.dir, target), "w")
            target = (FTP_GENBANK_ROOT + "/" +
                     collection + "/" + genome["species"] + "/" + target)
            ftp.retrbinary("RETR %s" % target, fo.write)
            fo.close()
            stderr.write("    " + PC.B + "done" + PC.E + "\n")
