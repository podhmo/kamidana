# kamidana の親切なエラーメッセージは今でも有用か? — jinja2 標準スタックトレースとの比較 (再調査)

実験レポート。マージしないかもしれない調査用のファイル群。

- 動機: kamidana の「親切なエラーメッセージ」機能 (`kamidana/debug/`) は jinja2 の
  traceback が貧弱だった時代に作られた。その後 jinja2 (および Python 自体) の
  traceback 表示は強化されたので、今でもこの機能に意味があるのかを確認する。
- 環境: Python 3.12.13 / jinja2 3.1.6 / kamidana 0.10.0
- 参考: https://pod.hatenablog.com/entry/2019/02/25/224123 (当時のブログ記事)
- **これは再調査版**: 初回の調査で見つかった6件の問題がすべて修正された
  (issue #60–#65 → PR #66–#71) 後の master で `outputs/` を取り直した。
  修正後の状態で変わった点・残っている観察点を反映している。

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
`level.py` は `Renderer.on_error(level=N)` を直接叩いてフレーム上限を変えた表示を取る
(case 10/11 の `*-level5.txt` / `*-level50.txt`)。

## 結論 (TL;DR)

jinja2 の生 traceback は 2019 年当時と比べて大幅に改善されており、**「どのテンプレートの
何行目・どの block で落ちたか」は素の jinja2 だけでも十分追える** ようになっている。

それでも kamidana の表示にはまだ意味がある:

1. **前後コンテキスト (±3行) が出る**。継承・include では「入口のタグ」(`{% extends %}` /
   `{% block %}` / `{% include %}`) が見えることが重要で、jinja2 は1行しか出さない。
2. **冒頭に exception/message/where のサマリがある**。長い traceback を読まなくても
   第一報が掴める。`where:` は実際の raise 箇所 (`file.py:NN`) を指すようになった。
3. **jinja2 内部フレームの混入がない**。生 traceback には `jinja2/utils.py`,
   `jinja2/runtime.py`, `jinja2/loaders.py` のフレームが混ざる (下記参照)。
4. `XTemplatePathNotFound` のヒントメッセージなど、kamidana 独自の情報が載る。

初回調査時の最大の弱点だった「深いネストでフレームが5窓に切り捨てられる」問題は
修正されており、**現在は素の jinja2 と同じ全フレームがコンテキスト付きで出る**。
記録の完全性でも生 traceback を下回るケースはなくなった。

## ケース別の観察

### 00extends-super — 継承 + super() 中の未定義変数 (ブログ記事の例)

`layout.html` の `head` block で未定義の `url_for` を呼ぶ。`child.html` が `head` を
override し `{{ super() }}` 経由で親の block に到達してエラー。

- kamidana: ブログ記事と同じ見た目の出力が今も出る。4フレーム × 前後3行。
  `where: layout.html` はテンプレート側エラーなので従来通り最内側テンプレートを指す。
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
- **[修正済み]** `where:` は以前「テンプレートの最内側フレーム」(`main.jinja2`) を
  指していたが、現在は実際の raise 箇所 `helpers.py:7` を指す (issue #60 / PR #67)。
  テンプレート側の入口は窓表示で追えるので、サマリの精度が上がった。

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

- `./no-such.html` → `XTemplatePathNotFound` のヒントが出る。**[修正済み]**
  以前は `where: None` と不格好に表示されていたが、現在は `where:` 行自体を
  出さない (issue #61 / PR #66)。
- `-d ./missing.json` → gentle 対象外なので素の traceback にフォールバック。
  余計なフレームは混入しない (re-raise で元 traceback を復元している) ので妥当。
- `-a missing.py` → **[修正済み]** 以前は fallback が
  `kamidana.additionals.missing.py` を**ファイルパスとして**探し、
  `module file is not found: kamidana.additionals.missing.py` という誤導する
  メッセージになっていた。現在は `.py` 拡張子を剥がしてからフォールバックし、
  `ImportError: module not found: missing.py (also tried kamidana.additionals.missing)`
  と正しいモジュール名で報告される (issue #62 / PR #68)。

### 10deep-chain — 多段ネストの記録 (継承4段 → include連鎖 → macro → python filter)

「多段にネストした関係がうまく記録できているか」の検証用に、意図的に深い
チェーンを作った:

```
c0.html -(extends)-> c1.html -(extends)-> c2.html -(extends)-> base.html
  ※ 各々が {% block content %}[cN] {{ super() }}{% endblock %} で中継
base.html -(include)-> part1.html -(include)-> part2.html
part2.html -(import/call)-> macros.html {% macro price() %}{{ 100|money }}...
money (additionals.py) -> helpers.format_money -> helpers.lookup_rate -> KeyError
```

素の jinja2 traceback (`outputs/10deep-chain/jinja2.txt`) はテンプレートフレームを
**11個すべて** 記録する (c0/c1/c2/base の top-level 4つ + block 'content' 4つ +
part1 + part2 + macro の1つ)。

**[修正済み]** 以前の kamidana は `on_error` の `level=5` で末尾5窓しか出さず、
チェーン先頭 (エントリの `c0.html` を含む) が暗黙に捨てられていた。現在は
デフォルト `level=None` なので**全11フレームがコンテキスト付きで出る**
(`outputs/10deep-chain/kamidana.txt`)。素の jinja2 と記録の完全性が並び、
さらに各フレームに前後3行の窓が付く分だけ情報量は上。

上限を明示した場合 (例: `level=5`) は従来通り末尾が残るが、先頭に
`... (6 frames omitted)` の省略マーカーが出るので切り捨てに気付ける
(`outputs/10deep-chain/kamidana-level5.txt`、issue #63 / PR #69)。
ただし `level` は CLI からは変更できず、`translate_error`/`on_error` の
API 引数経由のみ。

### 11recursive — 再帰と dedup の振る舞い

初回調査では `level=5` の存在意義 (無限ループ時の出力爆発対策か?) を検証するため
再帰ケースを作った。`level=5` は撤廃済みだが、再帰時の出力を抑える役は dedup
(`_extract._deduplicate`) が担っているので、このケースは dedup の検証として残す。

- **素の jinja2 の爆発は実在する**: 相互 include (ping⇄pong) では生 traceback が
  **約3000行** になる (`mutual-include-jinja2.txt`)。2ファイル周期のため Python の
  "Previous line repeated N more times" 畳み込みが効かない。自己 include では
  同じフレームの繰り返しなので畳まれて29行 (`self-include-jinja2.txt`)。
  → 「繰り返しフレームで出力が爆発する」問題は本物で、間引き自体には意義がある。
- **kamidana は dedup で収束する**: 同一 `(realpath, lineno)` を潰すので、
  `level` 上限なしでも相互 include は ping/pong の2窓、自己 include は1窓に収まる
  (`mutual-include.txt`, `self-include.txt`)。爆発防止としては dedup で十分。

初回調査で見つかった dedup のバグ2件は両方とも修正済み:

- **[修正済み] 同一ファイル内の呼出元が消える**: 以前は連続する同一ファイルの
  フレームを落としていたため、同一テンプレート内の macro 呼出で caller 側
  (`samemacro.html:4` の `{{ price() }}`) が表示されなかった。現在は lineno が
  異なれば別 call site として保持されるので caller 行と macro 本体内の行の
  両方が出る (`same-file-macro.txt`、issue #64 / PR #70)。
- **[修正済み] `"./x.html"` と絶対パスが別キーになる**: エントリのテンプレートは
  `"./ping.html"`、include 解決後は絶対パスだったため dedup をすり抜けて
  `ping.html` が2窓に重複表示されていた。現在は物理パスを realpath に正規化
  してから dedup するので重複しない (`mutual-include.txt`、issue #65 / PR #71)。

## jinja2 生 traceback 側の観察メモ

- `^^^^` マーカー行が fake traceback ではズレる/独立行になるケースがある
  (`kamidana-debug.txt` 系で確認。例: `outputs/00extends-super/kamidana-debug.txt`
  の `File ".../layout.html", line 4` の次行に無インデントの `^^^^^` が出る)。
- エラーに到るまでの内部フレーム (`environment.handle_exception`,
  `utils.from_obj`, `runtime._invoke`, `loaders.get_source`) が混ざるのは
  相変わらず。
- block 名が `in block 'head'` と出るのは有用。macro は `in template` のみ。

## 前回見つかった問題と対応状況

初回調査で挙げた6件は、すべて issue 化 (#60–#65) され修正が master にマージ済み。
本レポートの `outputs/` は修正後に取り直したもので、挙動の変化を確認できる。

| # | 問題 | issue | 修正PR | 確認した出力 |
|---|------|-------|--------|--------------|
| 1 | `where:` が最内側テンプレートを指し、Python 側 raise 箇所を示さない | #60 | #67 | `02python-filter/kamidana.txt` → `where: helpers.py:7` |
| 2 | `XTemplatePathNotFound` 直撃時に `where: None` と表示 | #61 | #66 | `09cli-errors/missing-template.txt` → `where:` 行を省略 |
| 3 | `-a <name>.py` の fallback をファイルパスとして解釈し誤導メッセージ | #62 | #68 | `09cli-errors/missing-additionals.txt` → 正しいモジュール名 |
| 4 | `level=5` でフレームが暗黙に切り捨てられ、深いチェーンの先頭が失われる | #63 | #69 | `10deep-chain/kamidana.txt` → 全11フレーム / `kamidana-level5.txt` → 省略マーカー |
| 5 | dedup が同一ファイル連続フレームを落とし macro caller が消える | #64 | #70 | `11recursive/same-file-macro.txt` → caller 行も表示 |
| 6 | dedup キーが生パス文字列で `"./x.html"` と絶対パスが別扱い | #65 | #71 | `11recursive/mutual-include.txt` → 重複なし |

## 残る観察点 (今回新たに気付いた点・未修正)

- **`where:` が stdlib 内部を指すことがある** (issue #72): raise 箇所を正確に
  指すようになった副作用として、RecursionError が `os.path` 内部で起きる再帰
  include では `where: <frozen posixpath>:63` と表示される
  (`11recursive/self-include.txt`)。正確ではあるがユーザーが見るべき場所
  (再帰している `{% include %}` 行) ではない。直すなら「最内側のユーザー
  コード (非 stdlib・非 jinja2) フレーム」を優先するか、テンプレート位置を
  併記する形が考えられる。深刻度は低い。
- **`level` は CLI から変えられない** (issue #73): 省略マーカー付きの上限機能は
  `translate_error`/`on_error` の引数経由のみ。上限をユーザーが使いたい場面は
  dedup があるので実質ほぼないが、API だけの隠れ機能になっている。

## 総評

「親切なエラーメッセージ」機能の根幹 (テンプレートフレーム抽出 + コンテキスト表示)
は健在で、初回調査で見つかった弱点 (フレーム切り捨て・`where:` の精度・dedup の
バグ・`-a` fallback) はすべて解消された。現状では少なくとも syntax error 系・
継承・include・macro のどの系でも、素の jinja2 出力より確実に読みやすく、
記録の完全性でも遜色がない。

jinja2 標準だけでも「場所の特定」自体は可能なので、この機能の差分は
「情報がある/ない」ではなく「読みやすさ+αのヒント」に位置づけられるが、
前後コンテキストと冒頭サマリは今も実用上有効な差分と言える。
