#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import os
import sys
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
from logging import getLogger


def join_files(outfiles):
    o = b""
    for path in outfiles:
        with open(path, "rb") as f:
            o = o + f.read()
    return o
    
def compute_hash(outfiles):
    return hash(join_files(outfiles))
    
class TestJumanpp(unittest.TestCase):
    def test_jumanpp(self):
        s = [u"すもももももももものうち",
             u"隣の客はよく柿食う客だ",
             u"犬も歩けば棒に当たる"]
        # obtain reference result
        p = subprocess.Popen(["jumanpp"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        o, _ = p.communicate(u"\n".join(s).encode("utf8"))

        with TemporaryDirectory() as d:
            files = jumanpp_batch(s, outfile_base=os.path.join(d, "{}.txt"),
                                  check_interval=1)
            h2 = compute_hash(files)
        self.assertEqual(hash(o), h2)

    def test_jumanpp_with_id(self):
        s = [u"すもももももももものうち",
             u"隣の客はよく柿食う客だ",
             u"犬も歩けば棒に当たる"]
        ids = [1, 2, 3]
        # obtain reference result
        p = subprocess.Popen(["jumanpp"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        x = [u"#{}\n{}".format(b, a) for a, b in zip(s, ids)]
        o, _ = p.communicate(u"\n".join(x).encode("utf8"))
        with TemporaryDirectory() as d:
            files = jumanpp_batch(s, ids, outfile_base=os.path.join(d, "{}.txt"),
                                  check_interval=1)
            h2 = compute_hash(files)
        self.assertEqual(hash(o), h2)
    
    def test_nproc_independence(self):
        s = [u"すもももももももものうち",
             u"隣の客はよく柿食う客だ",
             u"犬も歩けば棒に当たる"] * 50
        
        with TemporaryDirectory() as d:
            files1 = jumanpp_batch(s, outfile_base=os.path.join(d, "p1_{}.txt"),
                                   num_procs=1, check_interval=1)
            files2 = jumanpp_batch(s, outfile_base=os.path.join(d, "p2_{}.txt"),
                                   num_procs=2, check_interval=1)
            files3 = jumanpp_batch(s, outfile_base=os.path.join(d, "p4_{}.txt"),
                                   num_procs=4, check_interval=1)
            h1 = compute_hash(files1)
            h2 = compute_hash(files2)
            h3 = compute_hash(files3)
            #o1 = join_files(files1)
            #o2 = join_files(files2)
            #o3 = join_files(files3)
        #print(files1)
        #print(files2)
        #print(files3)
        #compare(o1.decode("utf8"), o2.decode("utf8"))
        #compare(o2.decode("utf8"), o3.decode("utf8"))
        #print(len(o1), len(o2), len(o3))
        #print(len(o1.decode("utf8")), len(o2.decode("utf8")), len(o3.decode("utf8")))
        self.assertEqual(h1, h2)
        self.assertEqual(h2, h3)

    def test_nproc_independence_with_id(self):
        s = [u"すもももももももものうち",
             u"隣の客はよく柿食う客だ",
             u"犬も歩けば棒に当たる"] * 20
        ids = list(range(len(s)))
        
        with TemporaryDirectory() as d:
            files1 = jumanpp_batch(s, ids, outfile_base=os.path.join(d, "p1_{}.txt"),
                                   num_procs=1, check_interval=1)
            files2 = jumanpp_batch(s, ids, outfile_base=os.path.join(d, "p2_{}.txt"),
                                   num_procs=2, check_interval=1)
            files3 = jumanpp_batch(s, ids, outfile_base=os.path.join(d, "p4_{}.txt"),
                                   num_procs=4, check_interval=1)
            h1 = compute_hash(files1)
            h2 = compute_hash(files2)
            h3 = compute_hash(files3)
        self.assertEqual(h1, h2)
        self.assertEqual(h2, h3)


class TestOutParser(unittest.TestCase):
    def test_token_attributes(self):
        s = [u"素敵な絵本"]
        ans = u"""
        素敵な すてきな 素敵だ 形容詞 3 * 0 ナ形容詞 21 ダ列基本連体形 3 "代表表記:素敵だ/すてきだ"
        絵本 えほん 絵本 名詞 6 普通名詞 1 * 0 * 0 "代表表記:絵本/えほん カテゴリ:人工物-その他;抽象物 ドメイン:文化・芸術;教育・学習"
        """.strip().split(u"\n")
        ans = [shlex.split(a.strip()) for a in ans]
        ans = [a + [False] for a in ans]  # is_alternative = true
        
        with TemporaryDirectory() as d:
            files = jumanpp_batch(s, outfile_base=os.path.join(d, "{}.txt"),
                                  num_procs=1, check_interval=1)
            for _, tokens in parse_outfiles(files):
                ans2 = tokens
            with open(files[0], "rb") as f:
                print(f.read().decode("utf8"))
        self.assertEqual(len(ans), len(ans2))
        for a, b in zip(ans, ans2):
            self.assertEqual(len(a), len(b))
            for c, d in zip(a, b):
                self.assertEqual(c, d)

    def test_surface(self):
        s = [u"すもももももももものうち",
             u"隣の客はよく柿食う客だ",
             u"犬も歩けば棒に当たる"]
        with TemporaryDirectory() as d:
            files = jumanpp_batch(s, outfile_base=os.path.join(d, "{}.txt"),
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
        ids = [8, 7, 5]
        with TemporaryDirectory() as d:
            files = jumanpp_batch(s, ids, outfile_base=os.path.join(d, "{}.txt"),
                                  num_procs=1, check_interval=1)
            ids2 = []
            s2 = []
            for i, tokens in parse_outfiles(files, format_func=lambda x: x.surface):
                print(tokens)
                ids2.append(int(i))
                s2.append("".join(tokens))
        self.assertEqual(len(s), len(s2))
        for a, b in zip(s, s2):
            self.assertEqual(a, b)

        self.assertEqual(len(ids), len(ids2))
        for a, b in zip(ids, ids2):
            self.assertEqual(a, b)

    def test_poc_filter(self):
        s = [u"すもももももももものうち",
             u"隣の客はよく柿食う客だ",
             u"犬も歩けば棒に当たる"]
        nouns = [[u"すもも", u"もも", u"もも", u"うち"],
                 [u"隣", u"客", u"柿", u"客"],
                 [u"犬", u"棒"]]
        with TemporaryDirectory() as d:
            files = jumanpp_batch(s, outfile_base=os.path.join(d, "{}.txt"),
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
            files = jumanpp_batch(s, outfile_base=os.path.join(d, "{}.txt"),
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

