# MST 機構の解説（Maximum Spanning Tree）

[手法選定ガイド](method-selection.html) ｜ [AIM の解説](method-aim.html) ｜ [INDEPENDENT の解説](method-independent.html) ｜ [メインレポート](index.html)

> 📘 本ページのアルゴリズム・実装の記述は、原論文 [arXiv:2108.04978](https://arxiv.org/abs/2108.04978) と
> [google/dpsynth](https://github.com/google/dpsynth) のソースコード（`dpsynth/discrete_mechanisms/mst.py`、2026-06 時点の main ブランチ）に基づく。
> 実験数値の節（🔎）のみ本デモの実測である。

---

## 1. 位置づけ

**MST（Maximum Spanning Tree）機構**は、NIST の合成データコンテスト優勝手法として知られる
DP 合成データ生成アルゴリズムである [arXiv:2108.04978](https://arxiv.org/abs/2108.04978)。
属性間の**ペア相関（2-way マージナル）のうち「最も相関の強い組み合わせで作る 1 本の木（最大全域木）」**だけを
差分プライバシーを満たしつつ選んで測定し、Private-PGM で同時分布を推定する。

**DPSynth の In-Memory API `dpsynth.generate()` のデフォルト機構は MST である**
（`discrete_config` 引数のデフォルト値が `MSTConfig()`）。
ただしこれは引数の既定値にすぎず、データに応じた自動選定ではない点に注意
（→ [手法選定ガイド](method-selection.html)）。

## 2. アルゴリズムの仕組み

```mermaid
flowchart LR
    A["① 1-way マージナル測定<br/>ガウス機構（予算 1/3）"] --> B["② ペア相関の重み計算<br/>独立モデルからの L1 乖離"]
    B --> C["③ DP 版クラスカル法<br/>指数機構（予算 1/3）で<br/>最大全域木を構築"]
    C --> D["④ 木の辺の 2-way マージナル測定<br/>ガウス機構（予算 1/3）"]
    D --> E["⑤ Private-PGM で<br/>同時分布を推定"]
    E --> F([合成データを<br/>サンプリング])
```

1. **1-way 測定**: 全列の周辺分布をガウス機構（集計値に正規ノイズを加える DP の基本機構）で測定する。
2. **ペア相関のスコアリング**: ノイズ付き 1-way から独立モデルを作り、各属性ペア `(a, b)` について
   「真の 2-way マージナル」と「1-way 同士の外積（独立を仮定した場合の予測）」の L1 距離を重みとする。
   独立仮定から乖離しているペアほど「相関が強い」とみなす（感度 1 の統計量になるよう設計されている）。
3. **DP 版クラスカル法**: 重み最大の辺を貪欲に選ぶ代わりに、各ラウンドで**指数機構**
   （スコアに応じた確率で候補を選ぶ DP 機構）により 1 辺ずつ選び、列数 −1 本の辺からなる全域木を作る。
4. **2-way 測定**: 木に選ばれた辺（属性ペア）の 2-way マージナルをガウス機構で測定する。
5. **推定と生成**: すべてのノイズ付き測定値を Private-PGM（`mbi`）に渡し、
   測定値と整合する同時分布（マルコフ確率場）を mirror descent で推定し、そこからサンプリングする。

選定は**最初に 1 回だけ**行われ、AIM のような反復・適応はない。

## 3. プライバシー予算の使われ方

`MSTConfig` のデフォルトでは、zCDP 換算の総予算 ρ を **3 等分**して使う。

| ステップ | 予算配分（既定） | 機構 |
|---|---|---|
| 1-way マージナル測定 | ρ × 1/3（`one_way_budget_fraction`） | ガウス機構 |
| 全域木の辺の選定 | ρ × 1/3（`select_budget_fraction`） | 指数機構（辺ごとに ε = √(8ρ′/(d−1)) を機械的に分配） |
| 2-way マージナル測定 | ρ × 残り 1/3 | ガウス機構 |

## 4. 主なパラメータ（`MSTConfig`）

| パラメータ | 既定値 | 意味 |
|---|---|---|
| `pgm_iters` | 5000 | Private-PGM（mirror descent）の反復回数 |
| `seed` | 0 | 乱数シード |
| `maximum_marginal_size` | 10,000,000 | 候補に含める 2-way マージナルのセル数上限（高カーディナリティ対策） |
| `one_way_budget_fraction` / `select_budget_fraction` | 1/3, 1/3 | 上記の予算配分 |

## 5. 得意なケース・苦手なケース

**得意**:

- **速度と品質のバランス**: 1 回の選定 + (d−1) 個の 2-way 測定で済むため高速。最初に試すベースラインに向く。
- 相関構造が「木」に近いデータ（強い相関が連鎖的につながっているデータ）。
- 列数・予算が限られていて、AIM の反復に予算を割けない場合。

**苦手**:

- **全域木に載らないペアの相関は保持されない**。木は d−1 本の辺しか持てないため、
  関心のあるペアが選から漏れると、そのペアの同時分布は大きく崩れうる（下記の実験C）。
- ユーザが「このペア相関を重視したい」と意図を伝える口（ワークロード指定）が**ない**。
- 3 つ以上の属性が絡む高次の相関（3-way 以上）はそもそもモデル化しない。

## 6. 本デモでの実験結果

> 🔎 以下は本デモ（UCI Adult、20,000 行、9 列、δ=1e-5）の実測。詳細は各リンク先を参照。

- **機構比較（ε=1.0、[メインレポート §5.1](index.html)）**: 平均 1-way TVD 0.098、相関誤差 0.064、
  TSTR AUC 0.687、生成時間**約 10 秒**。
- **複数シード（[追加実験B](experiments.html)）**: TSTR AUC 0.670 ± 0.087（10 シード）。
  AIM（0.666 ± 0.153）と**ほぼ同等**で、優劣はシード次第で逆転しうる。
- **2-way 忠実度（[追加実験C](experiments.html)）**: ペアによって明暗が分かれる。
  `education×income` は 0.041 と良好だが、木から外れた `marital-status×income`（0.364）・
  `occupation×income`（0.285）は大きく崩れ、**INDEPENDENT より悪い**ケースもあった。
- **ε スイープ（[メインレポート §5.1](index.html)）**: ε を 0.5 → 10 に上げると平均 1-way TVD は
  0.120 → 0.059 へおおむね単調に改善する。

## 7. 参考リンク

- 原論文: McKenna et al., *Winning the NIST Contest: A scalable and general approach to differentially private synthetic data* — [arXiv:2108.04978](https://arxiv.org/abs/2108.04978)
- 実装: [`dpsynth/discrete_mechanisms/mst.py`](https://github.com/google/dpsynth/blob/main/dpsynth/discrete_mechanisms/mst.py)
- 公式ドキュメント: [google/dpsynth README「Supported Synthesis Algorithms」](https://github.com/google/dpsynth)
- 推定エンジン: [Private-PGM / `mbi`](https://github.com/ryan112358/mbi)

---

← [手法選定ガイドに戻る](method-selection.html)
