#! /usr/bin/python
"""
Pretty print TeXcount output
"""


import argparse
import os
import shlex
import subprocess
import time

class Colours(object):
    """
    ANSI code from https://wiki.archlinux.org/index.php/Color_Bash_Prompt
    Change '\e' to '\x1b'
    """

    # Reset
    Reset = '\x1b[0m'       # Text Reset

    # Regular Colors
    Black = '\x1b[0;30m'        # Black
    Red = '\x1b[0;31m'          # Red
    Green = '\x1b[0;32m'        # Green
    Yellow = '\x1b[0;33m'       # Yellow
    Blue = '\x1b[0;34m'         # Blue
    Purple = '\x1b[0;35m'       # Purple
    Cyan = '\x1b[0;36m'         # Cyan
    White = '\x1b[0;37m'        # White

    # Bold
    BBlack = '\x1b[1;30m'       # Black
    BRed = '\x1b[1;31m'         # Red
    BGreen = '\x1b[1;32m'       # Green
    BYellow = '\x1b[1;33m'      # Yellow
    BBlue = '\x1b[1;34m'        # Blue
    BPurple = '\x1b[1;35m'      # Purple
    BCyan = '\x1b[1;36m'        # Cyan
    BWhite = '\x1b[1;37m'       # White

    # Underline
    UBlack = '\x1b[4;30m'       # Black
    URed = '\x1b[4;31m'         # Red
    UGreen = '\x1b[4;32m'       # Green
    UYellow = '\x1b[4;33m'      # Yellow
    UBlue = '\x1b[4;34m'        # Blue
    UPurple = '\x1b[4;35m'      # Purple
    UCyan = '\x1b[4;36m'        # Cyan
    UWhite = '\x1b[4;37m'       # White

    # Background
    On_Black = '\x1b[40m'       # Black
    On_Red = '\x1b[41m'         # Red
    On_Green = '\x1b[42m'       # Green
    On_Yellow = '\x1b[43m'      # Yellow
    On_Blue = '\x1b[44m'        # Blue
    On_Purple = '\x1b[45m'      # Purple
    On_Cyan = '\x1b[46m'        # Cyan
    On_White = '\x1b[47m'       # White

    # High Intensity
    IBlack = '\x1b[0;90m'       # Black
    IRed = '\x1b[0;91m'         # Red
    IGreen = '\x1b[0;92m'       # Green
    IYellow = '\x1b[0;93m'      # Yellow
    IBlue = '\x1b[0;94m'        # Blue
    IPurple = '\x1b[0;95m'      # Purple
    ICyan = '\x1b[0;96m'        # Cyan
    IWhite = '\x1b[0;97m'       # White

    # Bold High Intensity
    BIBlack = '\x1b[1;90m'      # Black
    BIRed = '\x1b[1;91m'        # Red
    BIGreen = '\x1b[1;92m'      # Green
    BIYellow = '\x1b[1;93m'     # Yellow
    BIBlue = '\x1b[1;94m'       # Blue
    BIPurple = '\x1b[1;95m'     # Purple
    BICyan = '\x1b[1;96m'       # Cyan
    BIWhite = '\x1b[1;97m'      # White

    # High Intensity backgrounds
    On_IBlack = '\x1b[0;100m'   # Black
    On_IRed = '\x1b[0;101m'     # Red
    On_IGreen = '\x1b[0;102m'   # Green
    On_IYellow = '\x1b[0;103m'  # Yellow
    On_IBlue = '\x1b[0;104m'    # Blue
    On_IPurple = '\x1b[0;105m'  # Purple
    On_ICyan = '\x1b[0;106m'    # Cyan
    On_IWhite = '\x1b[0;107m'   # White


class Tree(object):
    """
    Tree object for storing TeXcount output
    """

    def __init__(self, level, name):
        self.counts = {"text" : 0,
                       "headers" : 0,
                       "captions" : 0}
        self.totals = {"text" : 0,
                       "headers" : 0,
                       "captions" : 0}
        self.level = level
        self.name = name
        self.children = []

    def set_counts(self, counts):
        """
        Set counts for this level of the tree
        """
        self.counts["text"] = counts["text"]
        self.counts["headers"] = counts["headers"]
        self.counts["captions"] = counts["captions"]

    def update_totals(self, counts):
        """
        Update totals at this level
        """
        self.totals["text"] += counts["text"]
        self.totals["headers"] += counts["headers"]
        self.totals["captions"] += counts["captions"]

    def add_child(self, node):
        """
        Add subtree
        """
        self.children.append(node)


def level_cmp(level1, level2):
    """
    Comparison function for TeXcount levels
    """

    levels = ["Subsubsection", "Subsection", "Section", "Chapter", "Part",
              "Document"]
    level1 = levels.index(level1)
    level2 = levels.index(level2)

    return cmp(level1, level2)


def level_lt(level1, level2):
    """
    Convenience function for LT level comparisons
    """

    return level_cmp(level1, level2) == -1


def parseTeXcount(tc_output):
    """
    Read TeXcount output into a list
    """

    tc_data = []

    for line in tc_output:
        line = line.strip()

        if not line:
            continue

        if line[0].isdigit():
            line_data = line.split()
            count_data = line_data[0].split("+")
            counts = {"text" : int(count_data[0]),
                      "headers" : int(count_data[1]),
                      "captions" : int(count_data[2])}
            level = line_data[2].strip(":_")
            if level == "top":
                level = "Document"
                name = args.target
            else:
                name = " ".join(line_data[3:]).split("}")[0]
            tc_data.append({"counts" : counts, "level" : level, "name" : name})

    return tc_data


def buildTree(data):
    """
    Convet TeXcount output list to a tree
    """

    if not data:
        return (None, None)

    top_data = data[0]
    name = top_data["name"]
    level = top_data["level"]
    counts = top_data["counts"]
    tree = Tree(level, name)
    tree.set_counts(counts)
    tree.update_totals(counts)

    data = data[1:]

    while data and level_lt(data[0]["level"], level):
        sub_tree, data = buildTree(data)
        tree.add_child(sub_tree)
        tree.update_totals(sub_tree.totals)

    return tree, data


def printTree(tree, args, level=0):
    """
    Print TeXcount output tree
    """

    indent = " " * args.indent * level
    level_str = tree.level
    name_str = tree.name
    counts_str = ", ".join([str(i) for i in tree.counts.values()])
    totals_str = ", ".join([str(i) for i in tree.totals.values()])

    add_totals = (counts_str != totals_str)
    if add_totals:
        counts_str = "(" + counts_str + ")"

    if tree.level == "Chapter":
        print

    if args.colour:

        level_cols = {"Subsubsection" : Colours.Cyan,
                      "Subsection" : Colours.ICyan,
                      "Section" : Colours.IBlue,
                      "Chapter" : Colours.IGreen,
                      "Part" : Colours.Yellow,
                      "Document" : Colours.IPurple}

        level_str = level_cols[tree.level] + level_str + Colours.Reset
        counts_str = Colours.IYellow + counts_str + Colours.Reset
        totals_str = Colours.BRed + totals_str + Colours.Reset

    if add_totals:
        out_str = "{0}{1} {2}\t{3}\t{4}".format(indent, level_str,
                                                name_str, counts_str,
                                                totals_str)
    else:

        out_str = "{0}{1} {2}\t{3}".format(indent, level_str, name_str,
                                           counts_str)

    print out_str

    for sub_tree in tree.children:
        printTree(sub_tree, args, level + 1)


def printHeader(args):
    """
    Print header explaining columns
    """

    level = "Level"
    title = "Title"
    count = "(text, cap, head)"
    total = "total_text, total_cap, total_head"
    sep = "-" * 65

    if args.colour:
        level = Colours.IPurple + level + Colours.Reset
        count = Colours.IYellow + count + Colours.Reset
        total = Colours.BRed + total + Colours.Reset
        sep = Colours.White + sep + Colours.Reset

    header = "{0} {1} {2}\t{3}".format(level, title, count, total)

    print
    print sep
    print header
    print sep
    print


def logTree(tree, logpath):
    """
    Log counts to file
    """

    cur_date = time.strftime("%Y-%m-%d")
    cur_time = time.strftime("%H:%M:%S")
    name = tree.name
    level = tree.level
    text = tree.totals["text"]
    headers = tree.totals["headers"]
    captions = tree.totals["captions"]
    total = text + headers + captions

    if not os.path.isfile(logpath):
        head_line = ["Date", "Time", "Name", "Level", "Text", "Headers",
                     "Captions", "Total"]
        head_line = "\t".join(head_line) + "\n"
        with open(logpath, "w") as logfile:
            logfile.write(head_line)

    log_line = [cur_date, cur_time, name, level, str(text), str(headers),
                str(captions), str(total)]
    log_line = "\t".join(log_line) + "\n"

    with open(logpath, "a") as logfile:
        logfile.write(log_line)

    for sub_tree in tree.children:
        logTree(sub_tree, logpath)


def getArgs():
    """
    Get arguments from the command line using argparse
    """

    parser = argparse.ArgumentParser(prog="prettytc",
                                     description="Pretty print TeXcount output",
                                     epilog="""Any additional, unkown,
                                               arguments will be passed to
                                               TeXcount""")
    parser.add_argument("target", help=".tex file to count")
    parser.add_argument("-i", "--indent", default=4, type=int,
                        help="number of spaces to indent levels")
    parser.add_argument("-c", "--colour", action="store_true",
                        help="whether to colour output")
    parser.add_argument("-l", "--logpath", type=str,
                        help="file to log counts to")
    args, unknown = parser.parse_known_args()
    tc_opts = " ".join(unknown)

    return args, tc_opts


if __name__ == "__main__":

    args, tc_opts = getArgs()

    cmd = shlex.split("texcount " + tc_opts + " " + args.target)

    tc_output = subprocess.check_output(cmd).split("\n")

    tc_data = parseTeXcount(tc_output)

    tc_tree = buildTree(tc_data)[0]

    printHeader(args)

    printTree(tc_tree, args)

    if args.logpath:
        logTree(tc_tree, args.logpath)
