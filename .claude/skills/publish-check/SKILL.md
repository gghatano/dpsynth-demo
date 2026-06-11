---
name: publish-check
description: 公開サイトの整合確認。content/ の Markdown と htmls/ のビルド成果物、ビルダー（scripts/03_build_html.py）の PAGES テーブル、ナビ、README のリンクの整合を点検し、ビルドを実行して検証する。ページの追加・改名・公開前の最終確認に使う。
---

# 公開（ビルド & Pages）の整合確認

`.claude/docs/documentation-conventions.md` の第 3 節を前提に、
「`content/*.md`（ソース）→ ビルダー → `htmls/*.html`（成果物）→ GitHub Pages」の経路全体を点検する。

## 手順

1. ビルダー（`scripts/03_build_html.py`）の PAGES テーブルを読み、
   `content/*.md` の実ファイル一覧と突き合わせる（ビルド対象漏れ・存在しない md の参照）。
2. 以下のチェックリストで静的に点検する。
3. ビルドを実行して検証する: `.venv/bin/python scripts/03_build_html.py`
   （venv が無ければ `markdown` パッケージのみ入れた環境でも動く。DP 生成は不要）。
4. `python -m http.server 8099 --directory htmls` でローカル閲覧し、
   ナビ・図・アンカーリンクを抜き取り確認する（可能な場合）。
5. `htmls/` の再生成差分が意図どおりかを `git diff --stat htmls/` で確認する。

## チェックリスト

### ソースと成果物の対応
- [ ] `content/` の全 md が PAGES テーブルに載っているか（意図的な除外はコメントで明示）
- [ ] PAGES の出力名・サブタイトル・ナビキーが最新の内容を反映しているか
- [ ] `htmls/` がソースより古くないか（content/ 変更後にビルドし忘れていないか）
- [ ] `htmls/` を直接編集した形跡がないか（あれば content/ 側へ移してビルドし直す）

### リンク・図
- [ ] Markdown 内の相互リンクが公開後の HTML 名（`setup.html` 等）で書かれているか
- [ ] アンカー参照（`index.html#ref14` 等）の参照先見出しが実在するか
- [ ] 本文から参照する `figures/*.png` が実在し、ビルドで埋め込まれているか
- [ ] README の公開 URL・各 content ファイルへのリンクが現状と一致しているか
- [ ] レポート本体（index）から各個別ページ（機構・共有コンポーネント等の解説）へ、概要＋リンクで到達できるか（本体に深掘りが残っていないか）

### 公開ワークフロー
- [ ] `.github/workflows/deploy-pages.yml` の公開元が `htmls/` を指しているか
- [ ] 公開ビルドに重い処理（データ生成・評価）が混入していないか（Markdown 変換のみか）
- [ ] `.nojekyll` が `htmls/` に存在するか

## ページを追加・改名するときの定型手順

1. `content/<new>.md` を作成（相互リンクは HTML 名で記述）
2. ビルダーの PAGES テーブルにエントリ追加（md / out / subtitle / key）
3. ナビ定義に項目を追加
4. README の構成図・リンク一覧を更新
5. ビルド実行 → `htmls/` の差分確認 → ローカル閲覧で確認

## 出力形式

```
## publish-check 結果
### ビルド検証
- 実行コマンドと結果（成功/失敗、再生成されたページ数）
### 修正済み
- <file>:<line> 内容
### 要判断
- [重要度] 指摘と提案
```
