jumanpp-batch
=============

**Apply JUMAN++ to batch input in parallel**
[![Build Status](https://travis-ci.org/kota7/jumanpp-batch.svg?branch=master)](https://travis-ci.org/kota7/jumanpp-batch) [![PyPI Status](https://badge.fury.io/py/jumanpp-batch.svg)](https://badge.fury.io/py/jumanpp-batch)


This python package facilitates the usage of [juman++](http://nlp.ist.i.kyoto-u.ac.jp/index.php?JUMAN++) software by providing the functionalities to apply the command (1) to batch input (2) and in parallel.

### Requirement

- Python 2.7+, 3.4+
- [JUMAN++](http://nlp.ist.i.kyoto-u.ac.jp/index.php?JUMAN++) 1.0.2


## Installation



### JUMAN++

Refer to the official document for the details ([Manual](http://lotus.kuee.kyoto-u.ac.jp/nl-resource/jumanpp/jumanpp-manual-1.01.pdf)).

Requirements:

- GCC 4.9+
- Boost 1.57+
- (Optional) gperftool

On ubuntu, these can be installed by:

```bash
sudo apt-get install build-essential libboost-all-dev google-perftools
```

As of this writing, JUMAN++ v1.0.2 can be installed by the following command:

```bash
wget http://lotus.kuee.kyoto-u.ac.jp/nl-resource/jumanpp/jumanpp-1.02.tar.xz
tar xJvf jumanpp-1.02.tar.xz
cd jumanpp-1.02 && ./configure && make && sudo make install && ../
```

Check:
```bash
echo "すもももももももものうち" | jumanpp
#すもも すもも すもも 名詞 6 普通名詞 1 * 0 * 0 "代表表記:酸桃/すもも 自動獲得:EN_Wiktionary"
#@ すもも すもも すもも 名詞 6 普通名詞 1 * 0 * 0 "自動獲得:テキスト"
#も も も 助詞 9 副助詞 2 * 0 * 0 NIL
#もも もも もも 名詞 6 普通名詞 1 * 0 * 0 "代表表記:股/もも カテゴリ:動物-部位"
#@ もも もも もも 名詞 6 普通名詞 1 * 0 * 0 "代表表記:桃/もも 漢字読み:訓 カテゴリ:植物;人工物-食べ物 ドメイン:料理・食事"
#も も も 助詞 9 副助詞 2 * 0 * 0 NIL
#もも もも もも 名詞 6 普通名詞 1 * 0 * 0 "代表表記:股/もも カテゴリ:動物-部位"
#@ もも もも もも 名詞 6 普通名詞 1 * 0 * 0 "代表表記:桃/もも 漢字読み:訓 カテゴリ:植物;人工物-食べ物 ドメイン:料理・食事"
#の の の 助詞 9 接続助詞 3 * 0 * 0 NIL
#うち うち うち 名詞 6 副詞的名詞 9 * 0 * 0 "代表表記:うち/うち"
#EOS
```

### jumanpp-batch library

The library can be downloaded from the [PyPI](https://pypi.org/) repository.

```bash
pip install jumanpp-batch
```

Or install the development version from GitHub.
```bash
git clone https://github.com/kota7/jumanpp-batch.git
pip install -U ./jumanpp-batch
```


## Usage

Please also refer to [usage notebook](https://github.com/kota7/jumanpp-batch/blob/master/notebook/jumanpp-batch%20-%20Apply%20jumanpp%20to%20batch%20input%20in%20parallel.ipynb) for the detailed description of the library.

### Execute JUMAN++ jobs

```python
from jumanpp_batch import jumanpp_batch, parse_outfiles
texts = ["すもももももももものうち", "隣の客はよく柿食う客だ", "犬も歩けば棒に当たる",
         "伊香保温泉日本の名湯", "海賊王に俺はなる！"]
outfiles = jumanpp_batch(texts, num_procs=3) 
print(outfiles)
#['jumanpp-result_1.txt', 'jumanpp-result_2.txt', 'jumanpp-result_3.txt']
```

The results are saved in files.

```bash
!cat {outfiles[0]}
#すもも すもも すもも 名詞 6 普通名詞 1 * 0 * 0 "代表表記:酸桃/すもも 自動獲得:EN_Wiktionary"
#@ すもも すもも すもも 名詞 6 普通名詞 1 * 0 * 0 "自動獲得:テキスト"
#も も も 助詞 9 副助詞 2 * 0 * 0 NIL
#もも もも もも 名詞 6 普通名詞 1 * 0 * 0 "代表表記:股/もも カテゴリ:動物-部位"
#@ もも もも もも 名詞 6 普通名詞 1 * 0 * 0 "代表表記:桃/もも 漢字読み:訓 カテゴリ:植物;人工物-食べ物 ドメイン:料理・食事"
#も も も 助詞 9 副助詞 2 * 0 * 0 NIL
#もも もも もも 名詞 6 普通名詞 1 * 0 * 0 "代表表記:股/もも カテゴリ:動物-部位"
#@ もも もも もも 名詞 6 普通名詞 1 * 0 * 0 "代表表記:桃/もも 漢字読み:訓 カテゴリ:植物;人工物-食べ物 ドメイン:料理・食事"
#の の の 助詞 9 接続助詞 3 * 0 * 0 NIL
#うち うち うち 名詞 6 副詞的名詞 9 * 0 * 0 "代表表記:うち/うち"
#EOS
#隣 となり 隣 名詞 6 普通名詞 1 * 0 * 0 "代表表記:隣り/となり カテゴリ:場所-その他"
#の の の 助詞 9 接続助詞 3 * 0 * 0 NIL
#...
```

### Parse the output files into tokens

```python
for id_, tokens in parse_outfiles(outfiles):
    print(tokens)
    print("***")
#[JumanppToken(surface='すもも', reading='すもも', headword='すもも', pos='名詞', pos_id='6', pos2='普通名詞', pos2_id='1', infltype='*', infltype_id='0', inflform='*', inflform_id='0', info='代表表記:酸桃/すもも 自動獲得:EN_Wiktionary', is_alternative=False), JumanppToken(surface='も', reading='も', headword='も', pos='助詞', pos_id='9', pos2='副助詞', pos2_id='2', infltype='*', infltype_id='0', inflform='*', inflform_id='0', info='NIL', is_alternative=False), JumanppToken(surface='もも', reading='もも', headword='もも', pos='名詞', pos_id='6', pos2='普通名詞', pos2_id='1', infltype='*', infltype_id='0', inflform='*', inflform_id='0', info='代表表記:股/もも カテゴリ:動物-部位', is_alternative=False), JumanppToken(surface='も', reading='も', headword='も', pos='助詞', pos_id='9', pos2='副助詞', pos2_id='2', infltype='*', infltype_id='0', inflform='*', inflform_id='0', info='NIL', is_alternative=False), JumanppToken(surface='もも', reading='もも', headword='もも', pos='名詞', pos_id='6', pos2='普通名詞', pos2_id='1', infltype='*', infltype_id='0', inflform='*', inflform_id='0', info='代表表記:股/もも カテゴリ:動物-部位', is_alternative=False), JumanppToken(surface='の', reading='の', headword='の', pos='助詞', pos_id='9', pos2='接続助詞', pos2_id='3', infltype='*', infltype_id='0', inflform='*', inflform_id='0', info='NIL', is_alternative=False), JumanppToken(surface='うち', reading='うち', headword='うち', pos='名詞', pos_id='6', pos2='副詞的名詞', pos2_id='9', infltype='*', infltype_id='0', inflform='*', inflform_id='0', info='代表表記:うち/うち', is_alternative=False)]
#***
#[JumanppToken(surface='隣', reading='となり', headword='隣', pos='名詞', pos_id='6', pos2='普通名詞', pos2_id='1', infltype='*', infltype_id='0', inflform='*', inflform_id='0', info='代表表記:隣り/となり カテゴリ:場所-その他', is_alternative=False), JumanppToken(surface='の', reading='の', 
```

### Apply formatter and filter to the tokens

```python
for id_, tokens in parse_outfiles(outfiles,
                                  format_func=lambda x: "{} ({})".format(x.headword, x.reading),
                                  pos_filter=("名詞", "動詞")):
    print(tokens)
    print("***")
#['すもも (すもも)', 'もも (もも)', 'もも (もも)', 'うち (うち)']
#***
#['隣 (となり)', '客 (きゃく)', '柿 (かき)', '食う (くう)', '客 (きゃく)']
#***
#['犬 (いぬ)', '歩く (あるけば)', '棒 (ぼう)', '当たる (あたる)']
#***
#['伊香保 (伊香保)', '温泉 (おんせん)', '日本 (にっぽん)', '湯 (ゆ)']
#***
#['海賊 (かいぞく)', '王 (おう)', '俺 (おれ)', 'なる (なる)']
#***
```
