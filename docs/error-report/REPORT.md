# kamidana の親切なエラーメッセージは今でも有用か? — jinja2 標準スタックトレースとの比較

実験レポート。マージしないかもしれない調査用のファイル群。

- 動機: kamidana の「親切なエラーメッセージ」機能 (`kamidana/debug/`) は jinja2 の
  traceback が貧弱だった時代に作られた。その後 jinja2 (および Python 自体) の
  traceback 表示は強化されたので、今でもこの機能に意味があるのかを確認する。
- 環境: Python 3.12.13 / jinja2 3.1.6 / kamidana 0.10.0
- 参考: https://pod.hatenablog.com/entry/2019/02/25/224123 (当時のブログ記事)

## 実行方法

```console
$ ./run.sh   # outputs/<case>/{kamidana,kamidana-debug,jinja2}.txt を再生成する
```

各ケースで3つの出力を取っている:

| ファイル | 内容 |
|---|---|
| `kamidana.txt` | `kamidana` 実行時の親切エラー表示 (本機能) |
| `kamidana-debug.txt` | `kamidana --debug` — 同じ environment で生 traceback |
| `jinja2.txt` | `j2.py` — kamidana を介さない素の jinja2 + `traceback.print_exc()` |

`j2.py` は `FileSystemLoader` + `StrictUndefined` の environment で、その case ディレクトリに
`additionals.py` があれば `as_filter` 等でマークされた関数を登録して同じ条件でレンダリングする。

## 結論 (TL;DR)

jinja2 の生 traceback は 2019 年当時と比べて大幅に改善されており、**「どのテンプレートの
何行目・どの block で落ちたか」は素の jinja2 だけでも十分追える** ようになっている。

それでも kamidana の表示にはまだ意味がある:

1. **前後コンテキスト (±3行) が出る**。継承・include では「入口のタグ」(`{% extends %}` /
   `{% block %}` / `{% include %}`) が見えることが重要で、jinja2 は1行しか出さない。
2. **冒頭に exception/message/where のサマリがある**。長い traceback を読まなくても
   第一報が掴める。
3. **jinja2 内部フレームの混入がない**。生 traceback には `jinja2/utils.py`,
   `jinja2/runtime.py`, `jinja2/loaders.py` のフレームが混ざる (下記参照)。
4. `XTemplatePathNotFound` のヒントメッセージなど、kamidana 独自の情報が載る。

一方で今回見つかった kamidana 側の問題点もある (後述「見つかった問題」)。

## ケース別の観察

### 00extends-super — 継承 + super() 中の未定義変数 (ブログ記事の例)

`layout.html` の `head` block で未定義の `url_for` を呼ぶ。`child.html` が `head` を
override し `{{ super() }}` 経由で親の block に到達してエラー。

- kamidana: ブログ記事と同じ見た目の出力が今も出る。4フレーム × 前後3行。
- jinja2: `File "layout.html", line 5, in block 'head'` のように block 名つきで
  同じ4フレームが出る。2019年より格段に良い。ただし末尾に内部フレーム
  `jinja2/utils.py", line 92, in from_obj` が混入する。

### 01multi-inheritance — 3段継承 (base → mid → child)

`super()` チェーンの末端 `base.html` で `user_name` 未定義。

- 両者とも child → mid → base の top-level フレームと block 'greeting' フレームを
  正しく表示。情報量はほぼ同等。kamidana は各フレームに前後3行の窓が付く分だけ
  縦に長いが、タグ構造が読み取りやすい。

### 02python-filter — filter → 別モジュール → 別関数で raise (行ったり来たり)

`{{ 100|money }}` → `additionals.money` → `helpers.format_money` →
`helpers.lookup_rate` で `KeyError: 'JPY'`。

- 両者とも Python 側フレーム (additionals.py → helpers.py) を表示する。
  jinja2 はテンプレートフレームと Python フレームを1本に並べるだけ。
  kamidana はテンプレート部分をコンテキスト付きで出し、Python 部分を
  `Traceback:` セクションとして分離して出す — そして jinja2 内部フレーム
  (`utils.py from_obj`) を落とすので、素の出力より Python 側が1フレーム綺麗。
- **惜しい点**: ヘッダの `where: main.jinja2` は「テンプレートの最内側フレーム」を
  指すだけで、実際の raise 箇所 (`helpers.py:7`) ではない。Python 側エラーでは
  `where` が誤解を招く。

### 03include-missing — include 先ファイルが存在しない

- kamidana: `XTemplatePathNotFound` のガイダンスメッセージ + include した側
  (`main.html:3`) のコンテキスト + Python 側 traceback。情報量は十分。
- jinja2: `TemplateNotFound: './missing.html' not found in search path: '.'`
  + include 行1フレーム。これはこれで簡潔。

### 04/05syntax-error — 構文エラー (.jinja2 / .html)

`hello {{ name }` のような閉じ忘れ。

- kamidana: エラー行を中心に前後コンテキスト。拡張子に関係なく動いた
  (jinja2 が偽 traceback の co_name を "template" に書き換えるので
  `_is_jinja2_frame` にヒットする)。
- jinja2: 最終行には `File "main.html", line 3, in template` と出るが、
  `environment.py` / `loaders.py` のコンパイル経路の内部フレームが大量に混入し
  本質部分が埋もれる。このケースは kamidana の方が明確に見やすい。

### 06extends-syntax-error — 継承元テンプレートの構文エラー

`child.html` が `layout.html` を extends し、layout 側に `{% block footr %}` の閉じ忘れ。

- 両者とも「実行したのは child、壊れているのは layout.html:4」を正しく示す。
  jinja2 は `handle_exception` が2回現れるなど経路がやや複雑。

### 07macro-caller — macro + caller

`{% call layout.head() %}` の中で macro 本体が `url_for` 未定義で落ちる。

- kamidana: child2.html の call 行 → layout2.html の macro 内の行、2窓で簡潔。
- jinja2: 間に `jinja2/runtime.py", line 784, in _invoke` が挟まる。
  macro 内フレームは `in template` とだけ表示され block 名のような補助がない。

### 08include-chain — include 先テンプレート内の未定義変数

`main.html` → `part.html` で `user_name` 未定義。両者とも2フレームでほぼ同等。

### 09cli-errors — テンプレート外のエラー (kamidana 側のみ)

jinja2 に対応物がないので kamidana の出力だけを見た:

- `./no-such.html` → `XTemplatePathNotFound` のヒントは出るが `where: None` と表示
  される (`original_context.where` が None)。ちょっと不格好。
- `-d ./missing.json` → gentle 対象外なので素の traceback にフォールバック。
  余計なフレームは混入しない (re-raise で元 traceback を復元している) ので妥当。
- `-a missing.py` → **壊れている**。`missing.py` をファイルパスとして探して失敗
  → fallback で `kamidana.additionals.missing.py` を **これもファイルパスとして**
  探し、`module file is not found: kamidana.additionals.missing.py` という
  混乱したメッセージになる。dotted name (`-a missing`) なら
  `kamidana.additionals.missing` の import が正しく試行される。
  (`kamidana/_import.py` の拡張子 `.py` 判定によるもの)

## jinja2 生 traceback 側の観察メモ

- `^^^^` マーカー行が fake traceback ではズレる/独立行になるケースがある
  (`kamidana-debug.txt` 系で確認。例: `outputs/00extends-super/kamidana-debug.txt`
  の `File ".../layout.html", line 4` の次行に無インデントの `^^^^^` が出る)。
- エラーに到るまでの内部フレーム (`environment.handle_exception`,
  `utils.from_obj`, `runtime._invoke`, `loaders.get_source`) が混ざるのは
  相変わらず。
- block 名が `in block 'head'` と出るのは有用。macro は `in template` のみ。

## 見つかった問題まとめ (kamidana 側)

1. `where:` がテンプレートの最内側フレームを指すため、Python 側 (filter/関数内)
   で raise した場合に実際の発生箇所を示さない (case 02)。
2. `XTemplatePathNotFound` 直撃時に `where: None` と表示される (case 09)。
3. `-a <name>.py` で存在しないファイルを渡すと fallback 先をファイルパスとして
   解釈してしまい、メッセージが `kamidana.additionals.<name>.py` という存在しない
   ファイル名になる (case 09)。ユーザーの typo を誤導する。

## 総評

「親切なエラーメッセージ」機能の根幹 (テンプレートフレーム抽出 + コンテキスト表示)
は今も健在で、少なくとも syntax error 系・継承系では素の jinja2 出力より確実に
読みやすい。一方で jinja2 標準だけでも「場所の特定」自体は可能なので、この機能の
差分は「情報がある/ない」ではなく「読みやすさ+αのヒント」に移っている。
維持するなら上記の `where:` の精度や `-a` fallback のバグを直すと価値が上がる。
