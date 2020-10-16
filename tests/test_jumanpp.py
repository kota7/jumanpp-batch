#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import os
import sys
import re
import subprocess
from jumanpp_batch import jumanpp_batch, parse_outfiles
try:
    from tempfile import TemporaryDirectory
except:
    from tempfile import mkdtemp
    from shutil import rmtree
    class TemporaryDirectory:
        def __enter__(self):
            self.dirname = mkdtemp()
            return self.dirname

        def __exit__(self, type, value, traceback):
            rmtree(self.dirname)
if sys.version_info[0] == 2:
    import ushlex as shlex
else:
    import shlex
from parameterized import parameterized_class

def join_files(outfiles):
    o = b""
    for path in outfiles:
        with open(path, "rb") as f:
            o = o + f.read()
    return o
    
def compute_hash(outfiles):
    return hash(join_files(outfiles))

# Search for jumanpp command available on the system
# We search `jumanpp`, `jumanpp1`, `jumanpp2`
available_commands = []
for v in ("", 1, 2):
    command = "jumanpp" + str(v)
    try:
        p = subprocess.Popen([command, "-v"], stdout=subprocess.PIPE)
    except OSError:
        # command not exists
        continue
    o, _ = p.communicate()
    o = o.decode()
    if o.lower().startswith("juman++"):
        r = re.search(r"[0-9][\.0-9]+", o)
        if r:
            version = o[r.start():r.end()]
        available_commands.append((command, version))
class_params = [{"jumanpp_command": c, "jumanpp_ver": v} for c, v in available_commands]

# add `self.jumanpp_command` to the object dynamically
@parameterized_class(class_params)
class TestJumanpp(unittest.TestCase):

    def test_jumanpp(self):
        s = [u"すもももももももものうち",
             u"隣の客はよく柿食う客だ",
             u"犬も歩けば棒に当たる"]
        # obtain reference result
        p = subprocess.Popen([self.jumanpp_command], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        o, _ = p.communicate(u"\n".join(s).encode("utf8"))

        with TemporaryDirectory() as d:
            files = jumanpp_batch(s, jumanpp_command=self.jumanpp_command,
                                  outfile_base=os.path.join(d, "{}.txt"),
                                  check_interval=1)
            h2 = compute_hash(files)
        self.assertEqual(hash(o), h2)

    def test_jumanpp_with_id(self):
        s = [u"すもももももももものうち",
             u"隣の客はよく柿食う客だ",
             u"犬も歩けば棒に当たる"]
        ids = [1, 2, 3]
        # obtain reference result
        p = subprocess.Popen([self.jumanpp_command], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        x = [u"# {}\n{}".format(b, a) for a, b in zip(s, ids)]
        o, _ = p.communicate(u"\n".join(x).encode("utf8"))
        with TemporaryDirectory() as d:
            files = jumanpp_batch(s, ids, jumanpp_command=self.jumanpp_command,
                                  outfile_base=os.path.join(d, "{}.txt"),
                                  check_interval=1)
            h2 = compute_hash(files)
        self.assertEqual(hash(o), h2)

    def test_nproc_independence(self):
        s = [u"すもももももももものうち",
             u"隣の客はよく柿食う客だ",
             u"犬も歩けば棒に当たる"] * 19
        # setting len(s) not devisible by the num_procs
        # to test the consistency of input split
        with TemporaryDirectory() as d:
            files1 = jumanpp_batch(s, jumanpp_command=self.jumanpp_command,
                                   outfile_base=os.path.join(d, "p1_{}.txt"),
                                   num_procs=1, check_interval=1)
            files2 = jumanpp_batch(s, jumanpp_command=self.jumanpp_command,
                                   outfile_base=os.path.join(d, "p2_{}.txt"),
                                   num_procs=2, check_interval=1)
            files3 = jumanpp_batch(s, jumanpp_command=self.jumanpp_command, 
                                   outfile_base=os.path.join(d, "p4_{}.txt"),
                                   num_procs=4, check_interval=1)
            h1 = compute_hash(files1)
            h2 = compute_hash(files2)
            h3 = compute_hash(files3)
        self.assertEqual(h1, h2)
        self.assertEqual(h2, h3)

    def test_nproc_independence_with_id(self):
        s = [u"すもももももももものうち",
             u"隣の客はよく柿食う客だ",
             u"犬も歩けば棒に当たる"] * 17
        ids = list(range(len(s)))
        
        with TemporaryDirectory() as d:
            files1 = jumanpp_batch(s, ids, jumanpp_command=self.jumanpp_command,
                                   outfile_base=os.path.join(d, "p1_{}.txt"),
                                   num_procs=1, check_interval=1)
            files2 = jumanpp_batch(s, ids, jumanpp_command=self.jumanpp_command,
                                   outfile_base=os.path.join(d, "p2_{}.txt"),
                                   num_procs=2, check_interval=1)
            files3 = jumanpp_batch(s, ids, jumanpp_command=self.jumanpp_command,
                                   outfile_base=os.path.join(d, "p4_{}.txt"),
                                   num_procs=4, check_interval=1)
            h1 = compute_hash(files1)
            h2 = compute_hash(files2)
            h3 = compute_hash(files3)
        self.assertEqual(h1, h2)
        self.assertEqual(h2, h3)

    def test_nproc_larger_than_input_size(self):
        s = [u"すもももももももものうち",
             u"隣の客はよく柿食う客だ",
             u"犬も歩けば棒に当たる"]
        ids = list(range(len(s)))
        
        with TemporaryDirectory() as d:
            files1 = jumanpp_batch(s, jumanpp_command=self.jumanpp_command,
                                   outfile_base=os.path.join(d, "p1_{}.txt"),
                                   num_procs=1, check_interval=1)
            files2 = jumanpp_batch(s, jumanpp_command=self.jumanpp_command,
                                   outfile_base=os.path.join(d, "p4_{}.txt"),
                                   num_procs=4, check_interval=1)
            h1 = compute_hash(files1)
            h2 = compute_hash(files2)
        self.assertEqual(h1, h2)

# add `self.jumanpp_command` to the object dynamically
@parameterized_class(class_params)
class TestOutParser(unittest.TestCase):
    def test_token_attributes(self):
        # actual attributes depends on the dictionary and algorithm
        # we just test the number of attributes should equal (12 + 1)
        s = [u"先生とお友達", u"あいさつしよう", u"おはよう"]
        with TemporaryDirectory() as d:
            files = jumanpp_batch(s, jumanpp_command=self.jumanpp_command,
                                  outfile_base=os.path.join(d, "{}.txt"),
                                  num_procs=1, check_interval=1)
            for _, tokens in parse_outfiles(files):
                for token in tokens:
                    self.assertEqual(len(token), 13, msg=token)

    def test_surface(self):
        s = [u"すもももももももものうち",
             u"隣の客はよく柿食う客だ",
             u"犬も歩けば棒に当たる"]
        with TemporaryDirectory() as d:
            files = jumanpp_batch(s, jumanpp_command=self.jumanpp_command,
                                  outfile_base=os.path.join(d, "{}.txt"),
                                  num_procs=1, check_interval=1)
            s2 = []
            for _, tokens in parse_outfiles(files, format_func=lambda x: x.surface):
                s2.append("".join(tokens))
        self.assertEqual(len(s), len(s2))
        for a, b in zip(s, s2):
            self.assertEqual(a, b)

    def test_ids(self):
        s = [u"すもももももももものうち",
             u"隣の客はよく柿食う客だ",
             u"犬も歩けば棒に当たる"]
        ids = ["8", "7", "5"]
        with TemporaryDirectory() as d:
            files = jumanpp_batch(s, ids, jumanpp_command=self.jumanpp_command,
                                  outfile_base=os.path.join(d, "{}.txt"),
                                  num_procs=1, check_interval=1)
            ids2 = []
            s2 = []
            for i, tokens in parse_outfiles(files, format_func=lambda x: x.surface):
                print(tokens)
                ids2.append(i)
                s2.append("".join(tokens))
        self.assertEqual(len(s), len(s2))
        for a, b in zip(s, s2):
            self.assertEqual(a, b)
        
        # ID functionality works only with jumanpp ver.1
        # because comment printing function is dropped in ver.2
        if self.jumanpp_ver.startswith("1."):
            self.assertEqual(len(ids), len(ids2))
            for a, b in zip(ids, ids2):
                self.assertEqual(a, b)

    def test_poc_filter(self):
        # TODO. This test depends on juman++ algorithm
        #       perhaps not valid as a test for this package
        s = [u"すもももももももものうち",
             u"隣の客はよく柿食う客だ",
             u"犬も歩けば棒に当たる"]
        nouns = [[u"すもも", u"もも", u"もも", u"うち"],
                 [u"隣", u"客", u"柿", u"客"],
                 [u"犬", u"棒"]]
        with TemporaryDirectory() as d:
            files = jumanpp_batch(s, jumanpp_command=self.jumanpp_command,
                                  outfile_base=os.path.join(d, "{}.txt"),
                                  num_procs=1, check_interval=1)
            nouns2 = []
            for i, tokens in parse_outfiles(files, format_func=lambda x: x.surface,
                                            pos_filter=(u"名詞",)):
                nouns2.append(tokens)
        self.assertEqual(len(nouns), len(nouns2))
        for a, b in zip(nouns, nouns2):
            self.assertEqual(len(a), len(b))
            for c, d in zip(a, b):
                self.assertEqual(c, d)
                
        # verb, adjective, adverb
        ans = [[],
               [u"よく", u"食う"],
               [u"歩けば", u"当たる"]]
        with TemporaryDirectory() as d:
            files = jumanpp_batch(s, jumanpp_command=self.jumanpp_command,
                                  outfile_base=os.path.join(d, "{}.txt"),
                                  num_procs=1, check_interval=1)
            ans2 = []
            for i, tokens in parse_outfiles(files, format_func=lambda x: x.surface,
                                            pos_filter=(u"動詞", u"形容詞", "副詞")):
                ans2.append(tokens)
        self.assertEqual(len(ans), len(ans2))
        for a, b in zip(ans, ans2):
            self.assertEqual(len(a), len(b))
            for c, d in zip(a, b):
                self.assertEqual(c, d)


if __name__ == '__main__':
    unittest.main()

