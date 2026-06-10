# INDEPENDENT 機構の解説

[手法選定ガイド](method-selection.html) ｜ [MST の解説](method-mst.html) ｜ [AIM の解説](method-aim.html) ｜ [メインレポート](index.html)

> 📘 本ページのアルゴリズム・実装の記述は
> [google/dpsynth](https://github.com/google/dpsynth) のソースコード（`dpsynth/discrete_mechanisms/independent.py`、2026-06 時点の main ブランチ）に基づく。
> 実験数値の節（🔎）のみ本デモの実測である。

---

## 1. 位置づけ

**INDEPENDENT 機構**は、公式ドキュメントが "**baseline mechanism**" と明記する最も単純な手法である。
各列の周辺分布（1-way マージナル）だけを測定し、**全属性を互いに独立**としてモデル化する。
列間の相関は一切保持されない。

外部論文に基づく手法ではなく、「相関を全部捨てるとどうなるか」の比較基準（ベースライン）として、
また相関が不要な用途での最速・最小予算の選択肢として位置づけられる。

## 2. アルゴリズムの仕組み

```mermaid
flowchart LR
    A["① 総予算を列数 d で均等分割"] --> B["② 各列の 1-way マージナルを<br/>ガウス機構で測定"]
    B --> C["③ Private-PGM で<br/>独立な同時分布を推定"]
    C --> D([列ごとに独立に<br/>サンプリング])
```

1. 総予算を列数 d で均等に分け、各列に割り当てる。
2. 各列の周辺分布（値ごとの度数）をガウス機構で測定する。SELECT ステップは存在しない
   （測るものが最初から決まっているため、指数機構は使われない）。
3. ノイズ付き 1-way 測定値を Private-PGM（mirror descent）に渡し、非負性・総数整合を満たす
   周辺分布を推定する。同時分布は各列の周辺分布の積（= 独立）になる。

## 3. プライバシー予算の使われ方

| ステップ | 予算配分 | 機構 |
|---|---|---|
| 全列の 1-way マージナル測定 | 総予算を d 列で均等割り | ガウス機構 |

選定（指数機構）に予算を割かないため、**同じ総予算なら 1-way の測定精度は 3 機構で最も高くなりやすい**。

## 4. 主なパラメータ（`IndependentConfig`）

| パラメータ | 既定値 | 意味 |
|---|---|---|
| `pgm_iters` | 5000 | mirror descent の反復回数 |
| `seed` | 0 | 乱数シード |

調整すべきパラメータがほぼ無いことも、ベースラインとしての使いやすさにつながっている。

## 5. 得意なケース・苦手なケース

**得意**:

- **各列の周辺分布（単純集計）だけ再現できればよい**用途。例: 列ごとの度数分布の共有、
  ダッシュボードの単変量サマリー、スキーマ・形式だけ本物に似たテストデータ。
- **最速・最小コスト**。本デモでは 3 機構中最速（約 6 秒）。
- 他機構を評価するときの**比較基準**。「相関保持の効果」は INDEPENDENT との差分で測れる。

**苦手**:

- **列間の相関を使う用途すべて**。クロス集計、相関分析、予測モデルの学習データには不適。
  本デモの下流タスク（収入予測）では TSTR F1 がほぼ 0（全件を多数派クラスと予測）になった。
- 「1-way の分布が合っているから良い合成データだ」という誤解を誘発しやすい点にも注意
  （1-way 指標では他機構とほぼ差が出ない。下記の実験B）。

## 6. 本デモでの実験結果

> 🔎 以下は本デモ（UCI Adult、20,000 行、9 列、δ=1e-5）の実測。詳細は各リンク先を参照。

- **機構比較（ε=1.0、[メインレポート §5.1](index.html)）**: 平均 1-way TVD 0.106 は他機構と同水準だが、
  TSTR AUC **0.433**・F1 **0.003** と下流タスクでは壊滅的。生成時間は最速の**約 6 秒**。
- **複数シード（[追加実験B](experiments.html)）**: 平均 1-way TVD 0.086 ± 0.020 は**むしろ 3 機構で最良**。
  しかし TSTR AUC 0.490 ± 0.090 で**一貫して最下位**。「1-way の一致は下流の有用性を意味しない」ことの実例。
- **2-way 忠実度（[追加実験C](experiments.html)）**: 全ペアで AIM に劣るが、
  `marital-status×income`・`occupation×income` では **MST より良かった**
  （MST の全域木から外れたペアでは、誤った相関を張るより独立仮定の方がマシになる場合がある）。
- **MIA 耐性（[追加実験D](experiments.html)）**: AUC 0.511 で他機構と同様に攻撃の手がかりはほぼ無い。

## 7. 参考リンク

- 実装: [`dpsynth/discrete_mechanisms/independent.py`](https://github.com/google/dpsynth/blob/main/dpsynth/discrete_mechanisms/independent.py)
- 公式ドキュメント: [google/dpsynth README「Supported Synthesis Algorithms」](https://github.com/google/dpsynth)（"A baseline mechanism" との記載）
- 推定エンジン: [Private-PGM / `mbi`](https://github.com/ryan112358/mbi)
- 補足: 本デモでは INDEPENDENT 機構の重複クリーク・バグに対し
  [1 行パッチ](https://github.com/gghatano/dpsynth-demo/blob/main/patches/independent_dedup_cliques.patch)
  を当てて実行している（[実装ノート](engineering-notes.html) 参照）。

---

← [手法選定ガイドに戻る](method-selection.html)
