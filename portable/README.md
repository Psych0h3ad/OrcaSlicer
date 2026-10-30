# Snapmaker Orca 2.4.1 Portable

公式Windows x64ポータブル版に、設定・一時ファイル・WebView2データを同じフォルダー内へ保存する起動用ファイルを追加したものです。本体のexe、DLL、resourcesは変更していません。

## 使い方

1. [リリース](https://github.com/Psych0h3ad/OrcaSlicer/releases/tag/portable-v2.4.1-1)から `Snapmaker-Orca-2.4.1-Portable.zip` をダウンロードして、すべて展開します。
2. `Start-Snapmaker-Orca.cmd` をダブルクリックします。
3. 終了後、フォルダー全体をコピーすれば `App/data_dir` の設定も持ち運べます。

起動にPythonやPowerShellは不要です。Microsoft WebView2 Runtimeは別途必要です。会社のアプリ・USB・通信の制限は適用されます。本体によるURL関連付けのレジストリ登録やWindowsの実行履歴が残る場合があります。

## パッケージの作成

Python 3.11以降を使い、リポジトリのルートから実行します。

```console
python portable/tools/build_portable.py
python portable/tools/build_portable.py --zip
```

公式ZIPがなければ自動取得し、固定したSHA-256で検証します。生成先は `portable/Snapmaker-Orca-2.4.1-Portable.zip` です。既存の生成物や使用済み設定フォルダーは上書きしません。

## 確認範囲

管理者昇格なしで初回GUIセットアップ画面まで起動し、設定とWebView2データの保存先を確認しました。CLIスライス試験はアクセス違反で失敗しており、GUIでのスライス・印刷は未確認です。[検証結果](検証結果.txt)を参照してください。

## 配布元・ライセンス

[Snapmaker公式リリース v2.4.1](https://github.com/Snapmaker/OrcaSlicer/releases/tag/v2.4.1) / [対応するソース](https://github.com/Snapmaker/OrcaSlicer/tree/v2.4.1)。本体はAGPL v3で、同梱ライブラリにはそれぞれのライセンスが適用されます。リポジトリの `LICENSE.txt` と配布ZIP内のライセンスを参照してください。
