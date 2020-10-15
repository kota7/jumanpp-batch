# -*- coding: utf-8 -*-

import os
import re
import math
import time
import subprocess
import sys
import warnings
from collections import namedtuple
from datetime import datetime, timedelta
from multiprocessing import cpu_count
import jaconv
# shlex does not work for unicode on python2
# use ushlex instead
if sys.version_info[0] == 2:
    import ushlex as shlex
else:
    import shlex
from logging import getLogger

logger = getLogger(__name__)

class Preprocessor:
    def __init__(self, zenkaku=("ascii", "digit", "kana"), hankaku=(),
                 merge_consec_spaces=True, strip_spaces=True, add_space="empty"):
        self.zenkaku = zenkaku
        self.hankaku = hankaku
        self.merge_consec_spaces = merge_consec_spaces
        self.strip_spaces = strip_spaces
        self.add_space = add_space
    
    def __call__(self, text):
        text = re.sub(r"[\r\n]+", u" ", text)
        if self.merge_consec_spaces:
            text = re.sub(r"\s+", u" ", text)
        if self.strip_spaces:
            text = text.strip()
        if (self.add_space == "all" or 
           (self.add_space == "empty" and len(text) == 0)):
            # add a space to avoid error due to empty input
            text = text + " "
        if len(self.zenkaku) > 0:
            kwargs = {"ascii": False, "digit": False, "kana": False}
            for v in self.zenkaku:
                kwargs[v] = True
            text = jaconv.h2z(text, **kwargs)
        if len(self.hankaku) > 0:
            kwargs = {"ascii": False, "digit": False, "kana": False}
            for v in self.hankaku:
                kwargs[v] = True
            text = jaconv.z2h(text, **kwargs)
        return text


def jumanpp_batch(texts, ids=None, num_procs=1,
                  preprocess="default",
                  outfile_base="jumanpp-result_{}.txt",
                  encoding="utf8",
                  jumanpp_command="jumanpp",
                  jumanpp_args=(),
                  check_interval=10,
                  show_progress=False):
    """
    Apply juman++ to batch inputs in parallel
    
    Args:
      texts: List of strings to be analyzed by juman++.
      ids: If not none, a list of IDs for the texts.
           Must be the same length as texts.
      num_procs: Integer. Number of parallel processes.
                 If nonpositive, set to the number of available CPUs.
      preprocess: Function str -> str, preprocessor for input texts.
                  If 'default', the processor will:
                  - convert '\\n' and '\\r' to a space
                  - merge consecutive spaces
                  - strip leading and trailing spaces
                  - add a space to the end (avoid error due to empty input) 
                  - convert hankaku to zenkaku
                  If None, no preprocessing is applied.
      outfile_base: Template for output file names.
                    It must contain a '{}', where a file number is inserted.
      encoding: Input and output text encoding. 
                It should be compatible to the juman++ software.
      jumanpp_command: Command name for juman++ software.
      jumanpp_args: Arguments to juman++ command.
      check_interval: Integer. 
                      Check the completion of analysis with this interval (in sec).
      show_progress: If true, analysis progress is reported on the console.
    
    Returns:
      List of output file paths.      
    """
    if num_procs < 1:
        num_procs = cpu_count()
    logger.debug("Number of processes: %s", num_procs)
    
    n = len(texts)
    n_each = int(math.ceil(1.0 * n / num_procs))
    # On python 2, we need to make sure the division computes in float
    # Otherwise the value could be rounded down automatically
    logger.debug("Total inputs: %s, inputs per proc: %s", n, n_each)
    
    if preprocess == "default":
        preprocess =  Preprocessor()
    if preprocess is not None:
        logger.debug("Preprocessing input texts")
        texts = [preprocess(t) for t in texts]
    if ids is not None:
        texts = [u"#{}\n{}".format(i,t) for t,i in zip(texts, ids)]

    procs = []
    n_finished = 0  # track the number of texts fed into jumanpp for debugging 
    for i in range(num_procs):
        i1 = n_each * i
        i2 = min(i1 + n_each, n)
        if i1 >= i2:
            # no more input
            break
        outfile = outfile_base.format(i+1)
        dirpath = os.path.abspath(os.path.dirname(outfile))
        assert not os.path.isfile(dirpath), "`{}` is a file".format(dirpath)
        if not os.path.isdir(dirpath):
            os.makedirs(dirpath)
            logger.debug("`%s` has been created", dirpath)
        infile = outfile + ".in"
        logger.debug("Writing texts %d to %d into `%s`", i1, i2, infile)
        with open(infile, "wb") as f:
            f.write(u"\n".join(texts[i1:i2]).encode(encoding))
        
        logger.info("Start juman++ job #%d. Outfile = `%s`", i+1, outfile)
        command = [jumanpp_command] + list(jumanpp_args)
        logger.debug("Command: `%s`", command)
        with open(infile, "rb") as f, open(outfile, "wb") as g:
            p = subprocess.Popen(command, stdin=f, stdout=g)
        logger.debug("Job #%d. Pid: %s", i+1, p.pid)
        procs.append({"proc": p, "infile": infile, "outfile": outfile, "count": (i2-i1)})
        
        n_finished += (i2 - i1)
        logger.debug("In total, %d / %d inputs have been fed into jumanpp", n_finished, n)
    assert n == n_finished, "Total texts analyzed is {}, where the input size is {}".format(n_finished, n)
    # wait until all procs finish
    finished = [False for _ in procs]
    start = {"t0": None, "n0": None}  # used by progress report
    while not all(finished):
        for i, p in enumerate(procs):
            if finished[i]:
                continue
            res = p["proc"].poll()
            if res is not None:
                logger.info("Job #%d done. Return code: %s", i+1, res)
                finished[i] = True
                p["proc"].communicate()  # kills the process
                os.remove(p["infile"])
            else:
                logger.debug("Job #%d is working (Return code is none)", i+1)
        if all(finished):
            if show_progress:
                print("All jos are completed.")
            break
        
        if show_progress:
            n_finished = [0] * len(procs)
            for i, p in enumerate(procs):
                if finished[i]:
                    n_finished[i] = p["count"]
                else:
                    with open(p["outfile"], "rb") as f:
                        for line in f:
                            if line.decode(encoding).strip() == "EOS":
                                n_finished[i] += 1
                logger.debug("Job #%d. Progress: %d/%d (%.1f%%)",
                             i+1, n_finished[i], p["count"], 100*n_finished[i]/p["count"])
            n_cur = sum(n_finished)
            t_cur = datetime.now()
            if start["t0"] is not None:
                velocity = (n_cur - start["n0"]) / (t_cur - start["t0"]).seconds
                remain = timedelta(seconds=round((n - n_cur) / velocity))
                etc = (t_cur + remain).strftime("%Y-%m-%d %H:%M:%S")
            else:
                velocity = 0.0
                remain = "???"
                etc = "???"
                start["t0"] = t_cur
                start["n0"] = n_cur
            print("Completed: %d/%d (%.1f%%) | %.1f per sec | ETC: %s (%s remaining)" % (
                  n_cur, n, 100*n_cur/n, velocity, etc, remain))
        time.sleep(check_interval)
        
    return [p["outfile"] for p in procs]


JumanppToken = namedtuple(
    "JumanppToken",
    "surface reading headword pos pos_id pos2 pos2_id " + \
    "infltype infltype_id inflform inflform_id info is_alternative")

def make_token(line):
    """
    Parse a juman++ output line into a token object
    
    Args:
      line: String, assumed to be a line froma juman++ output
    
    Returns:
      JumanppToken object
    """
    items = shlex.split(line)
    if items[0] == u"@":
        is_alternative = True
        items = items[1:]
    else:
        is_alternative = False
        
    if len(items) != 12 and line.find(u"\\") >= 0:
        # Edge case. When a sentence contains '\', 
        # the result line contains '\' in a way
        # it cannot be distinguished from escaping character
        # The length other than 12 signals that.
        # We will try treating '\' literally to see if 
        # we can get the length 12 by doing so.
        logger.debug("'%s' has %d items (expected 12)", line, len(items))
        logger.debug("We will try again with treating '\' literally")
        items = shlex.split(line.replace(u"\\", u"\\\\"))
        if items[0] == "@":
            is_alternative = True
            items = items[1:]
        else:
            is_alternative = False
        if len(items) == 12:
            logger.debug("Item length is now %d, which is good", len(items))
        else:
            logger.debug("Item length is now %d", len(items))

    if len(items) != 12:
        logger.warning(u"'%s' has %d items (expected 12)", line, len(items))
        message = u"'%s' has %d items (expected 12), skipped" % (line, len(items))
        if len(items) > 12:
            warnings.warn(message + u". Only the first 12 items are used")
            items = items[0:12]
        if len(items) < 12:
            warnings.warn(message + u". Padded with None")
            items += [None] * (12 - len(items))
    items.append(is_alternative)
    return JumanppToken(*items)

def parse_document(doc, 
                   format_func=None, pos_filter=None, filter_func=None,
                   skip_spaces=True, skip_last_space=True, skip_alternatives=True):
    """
    Parse juman++ result for a single sentence into tokens
    
    Args:
      doc: Str of juman++ result for a single sentence
      format_func: A function JumanppToken -> Object to retrieve 
                   necessary information from each token.
      pos_filter: Sequence of part-of-speech to keep.
      filter_func: A function JumanppToken -> Bool that indicates
                   if this token should be kept.
      skip_spaces: If true, skip tokens whose surface is a space (matches r'\\s')
      skip_last_space: If true, skip the last token if its surface is a space (matches r'\\s')
      skip_alsternatives: If true, skip alternative tokens (Starting with '@' in the output)
    
    Returns:
      List of tokens
    """
    if pos_filter is not None:
        pos_filter = set(pos_filter)
    
    lines = [line for line in doc.split(u"\n") \
             if line.strip() not in (u"", u"EOS")]
    tokens = [make_token(line) for line in lines]
    if len(tokens) < 1:
        # edge case with no token lines
        return []
    if skip_last_space:
        if re.match(r"\s$", tokens[-1].surface):
            tokens = tokens[:-1]
    
    def _filter(token):
        if skip_alternatives and token.is_alternative:
            return False
        if (pos_filter is not None) and (token.pos not in pos_filter):
            return False
        if (filter_func is not None) and (not filter_func(token)):
            return False
        if skip_spaces and re.match(r"\s$", token.surface):
            return False
        return True
    tokens = [token for token in tokens if _filter(token)]
    if format_func is not None:
        tokens = [format_func(token) for token in tokens]
    return tokens

def get_documents(outfile, include_eos=False, encoding="utf8"):
    """
    Iterate through texts from juman++ output file(s)
    Args:
      outfile: Str of a juman++ output file
      include_eos: Bool indicating if the EOS line should be kept
      encoding: character encoding of the file
    
    Returns:
      Generator of (id, juman++ result)
    """
    with open(outfile, "rb") as f:
        id_ = None
        doc = u""
        for line in f:
            line = line.decode(encoding)
            if line.strip() == u"":
                continue
            # find ID 
            if doc == "":
                r = re.match(r"#(.*) JUMAN\+\+", line)
                if r is not None:
                    id_ = r.group(1)
            if line.strip() == u"EOS":
                if include_eos:
                    doc += line
                yield (id_, doc)
                id_, doc = None, u""
            elif line[0] != "#":
                doc += line

def parse_outfiles(outfiles, encoding="utf8", show_progress=False,
                   format_func=None, pos_filter=None, filter_func=None,
                   skip_spaces=True, skip_last_space=True, skip_alternatives=True):
    """
    Parse juman++ output files into tokens
    
    Args:
      outfiles: Str or list of str of juman++ output file(s)
      encoding: Character encoding of the file
      show_progress: If true, report the progress at the beginning of each file
      format_func: A function JumanppToken -> Object to retrieve 
                   necessary information from each token.
      pos_filter: Sequence of part-of-speech to keep.
      filter_func: A function JumanppToken -> Bool that indicates
                   if this token should be kept.
      skip_spaces: If true, skip tokens whose surface is a space (matches r'\\s')
      skip_last_space: If true, skip the last token if its surface is a space (matches r'\\s')
      skip_alsternatives: If true, skip alternative tokens (Starting with '@' in the output)
    
    Returns:
      Generator of (id, tokens).
    """
    if type(outfiles) != list:
        outfiles = [outfiles]
    for f in outfiles:
        assert os.path.isfile(f), u"`{}` does not exist".format(f)
        
    t0 = datetime.now() # used by progress report
    for i, f in enumerate(outfiles):
        logger.info(u"Start parsing `%s`", f)
        if show_progress:
            t1 = datetime.now()
            if i > 0:
                sec_per_item = ((t1 - t0).seconds / i)
                remain = timedelta(seconds=(len(outfiles) - i) * sec_per_item)
            else:
                remain = "???"
            print(u"Working on %d/%d (%.1f%%): %s | Remaining: %s" % (
                i+1, len(outfiles), 100*(i+1)/len(outfiles), f, remain))
        for i, doc in get_documents(f, include_eos=False, encoding=encoding):
            tokens = parse_document(doc,
                                    format_func=format_func,
                                    pos_filter=pos_filter,
                                    filter_func=filter_func,
                                    skip_spaces=skip_spaces, 
                                    skip_last_space=skip_last_space,
                                    skip_alternatives=skip_alternatives)
            yield i, tokens