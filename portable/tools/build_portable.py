"""Prepare a portable folder from the unmodified official Windows release.

Python 3.11+ standard library only. Run from any working directory.
Downloads the pinned official ZIP when absent. After preparation, use --zip
to create the deliverable archive and its SHA-256 checksum.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath


WORKSPACE = Path(__file__).resolve().parent.parent
PACKAGE_NAME = "Snapmaker-Orca-2.4.1-Portable"
PACKAGE = WORKSPACE / PACKAGE_NAME
OFFICIAL_NAME = "Snapmaker_Orca_Windows_V2.4.1_portable.zip"
OFFICIAL_SHA256 = "1f002e2168c576f800bcfd0509b5e164b5ad65a0963abc2bef8317d929d48c9d"
OFFICIAL_URL = (
    "https://github.com/Snapmaker/OrcaSlicer/releases/download/v2.4.1/" + OFFICIAL_NAME
)

LAUNCHER = r'''@echo off
setlocal DisableDelayedExpansion
rem Only child processes inherit these paths; no system settings are changed.
set "PORTABLE_APP=%~dp0App"
set "PORTABLE_DATA=%~dp0App\data_dir"
if not exist "%PORTABLE_APP%\snapmaker-orca.exe" goto missing_app
if not exist "%PORTABLE_DATA%" mkdir "%PORTABLE_DATA%"
if not exist "%PORTABLE_DATA%\temp" mkdir "%PORTABLE_DATA%\temp"
if not exist "%PORTABLE_DATA%\webview2" mkdir "%PORTABLE_DATA%\webview2"
if not exist "%PORTABLE_DATA%\temp" goto unwritable
if not exist "%PORTABLE_DATA%\webview2" goto unwritable
set "TEMP=%PORTABLE_DATA%\temp"
set "TMP=%PORTABLE_DATA%\temp"
set "WEBVIEW2_USER_DATA_FOLDER=%PORTABLE_DATA%\webview2"
start "" /D "%PORTABLE_APP%" "%PORTABLE_APP%\snapmaker-orca.exe" --datadir "%PORTABLE_DATA%" %*
exit /b %errorlevel%

:missing_app
echo App\snapmaker-orca.exe was not found.
echo Extract the entire ZIP before starting the application.
pause
exit /b 1

:unwritable
echo The portable data folder is not writable.
echo Move the entire folder to a writable local folder or USB drive.
pause
exit /b 1
'''

README = """Snapmaker Orca 2.4.1 ポータブル版（Windows x64）

■ 使い方
1. ZIPを右クリックして「すべて展開」します。ZIP内から直接実行しないでください。
2. 展開先の「Start-Snapmaker-Orca.cmd」をダブルクリックします。
3. 初回ウィザードで言語、プリンター、フィラメントなどを選択します。
   管理者として実行する必要はありません。PythonやPowerShellも起動には不要です。

USBメモリーや書き込み可能なローカルフォルダーで利用できます。
USBが遅い場合は、フォルダー全体をPCにコピーしてから使うと快適です。
モデルファイルを起動用cmdにドラッグ＆ドロップして開くこともできます。

■ 設定の持ち運び
設定、プリンタープロファイル、アプリのログなどは「App\\data_dir」に保存します。
起動用cmdは一時ファイルとWebView2のデータ保存先もその配下に指定します。
持ち運びやバックアップは、アプリ終了後にこのフォルダー全体をコピーしてください。
別のドライブ文字や場所に移動しても、起動用cmdは移動先を自動的に使います。
最近使ったモデルなどの絶対パスは、移動後に選び直す必要があります。

App内のexeを直接起動しても、標準のdata_dir機能で設定は持ち運べます。
一時ファイルとWebView2の保存先も揃えるには、起動用cmdを使ってください。
既存のインストール版の設定やログイン情報は取り込んでいません。
使用後のdata_dirにはログイン情報等が含まれることがあるため、他人に渡す前に確認してください。

■ 利用できる環境と制限
・Windows 10 / 11の64bit（Intel / AMD）を想定しています。
・Microsoft WebView2 Runtimeが必要です。本パッケージには同梱していません。
  通常は既に導入されていますが、未導入の会社PCではIT担当者に確認してください。
  アプリ内からのランタイム追加は管理者権限を要求する場合があります。
・会社のアプリ実行制限、USB実行制限、通信制限はそのまま適用されます。
・初回起動時に「Snapmaker Control」のWindows通信許可画面が出る場合があります。
  会社PCでの通信許可は社内ルールに従って判断してください。
・通常のスライスとG-codeのファイル出力から使えます。プリンターへの直接送信や
  クラウド機能には、通信、ログイン、追加プラグイン等が必要な場合があります。
・初回の拡張子関連付けは、必要がなければ選択しないでください。
・完全にPCへの痕跡を残さない方式ではありません。本体は起動時にURLプロトコル
  （Snapmaker_Orca / snapmaker-orca）をユーザーのレジストリへ登録する仕様です。
  Windows側にも実行履歴等が残ることがあります。
・更新時は新しい版を別フォルダーに展開し、終了した状態でdata_dirをバックアップしてから
  移行してください。通常のインストーラーで上書きする必要はありません。

■ 内容
Start-Snapmaker-Orca.cmd : インストール不要の起動用ファイル
App                     : 公式ポータブル版の本体、DLL、resources、ライセンス
App\\data_dir            : 持ち運ぶ設定とデータ（初回起動時に作成）
PROVENANCE.json         : 公式配布元と取得元ZIPのSHA-256
検証結果.txt             : 作成時に確認できた範囲と未検証の項目
SHA256SUMS.txt           : 配布時の各ファイルのSHA-256（設定保存後は変化します）

本体のexe、DLL、resources、ライセンスは公式配布物のままです。
追加したものは起動用cmd、data_dirフォルダー、この案内、検証・出典情報です。
Snapmakerが別途公開した製品ではなく、公式ポータブル版を使いやすく配置したものです。

■ 公式配布元・ソース・ライセンス
リリース: https://github.com/Snapmaker/OrcaSlicer/releases/tag/v2.4.1
ソース: https://github.com/Snapmaker/OrcaSlicer/tree/v2.4.1
公式サイト: https://www.snapmaker.com/snapmaker-orca
本体のライセンス: App\\LICENSE.txt（AGPL v3。付属ライブラリは各ライセンスに従います）
標準のポータブル設定:
https://github.com/Snapmaker/OrcaSlicer/blob/v2.4.1/src/slic3r/GUI/GUI_App.cpp#L2178
"""


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_windows_text(path: Path, text: str, *, bom: bool = False) -> None:
    path.write_text(text, encoding="utf-8-sig" if bom else "ascii", newline="\r\n")


def prepare() -> None:
    archive = WORKSPACE / "downloads" / OFFICIAL_NAME
    if PACKAGE.exists():
        raise FileExistsError(f"Refusing to overwrite an existing portable folder: {PACKAGE}")
    report = WORKSPACE / "検証結果.txt"
    if not report.is_file():
        raise FileNotFoundError(f"The published validation report is missing: {report}")
    if not archive.exists():
        archive.parent.mkdir(parents=True, exist_ok=True)
        partial = archive.with_suffix(".zip.part")
        request = urllib.request.Request(
            OFFICIAL_URL, headers={"User-Agent": "Snapmaker-Orca-Portable-Builder"}
        )
        print(f"Downloading {OFFICIAL_NAME}", flush=True)
        with urllib.request.urlopen(request, timeout=120) as response, partial.open("wb") as target:
            shutil.copyfileobj(response, target, length=1024 * 1024)
        if sha256(partial) != OFFICIAL_SHA256:
            raise ValueError("The downloaded ZIP does not match the official SHA-256.")
        partial.replace(archive)
    if sha256(archive) != OFFICIAL_SHA256:
        raise ValueError("The downloaded ZIP does not match the official SHA-256.")
    with zipfile.ZipFile(archive) as source:
        if bad := source.testzip():
            raise ValueError(f"ZIP CRC check failed: {bad}")
        executables = [
            entry for entry in source.infolist()
            if PurePosixPath(entry.filename).name.lower() == "snapmaker-orca.exe"
        ]
        if len(executables) != 1:
            raise ValueError(f"Expected one main executable; found {len(executables)}")
        prefix = PurePosixPath(executables[0].filename).parent
        PACKAGE.mkdir()
        app = PACKAGE / "App"
        app.mkdir()
        count = 0
        for entry in source.infolist():
            source_path = PurePosixPath(entry.filename)
            if source_path.is_absolute() or ".." in source_path.parts or "\\" in entry.filename:
                raise ValueError(f"Unsafe archive path: {entry.filename}")
            relative = source_path.relative_to(prefix)
            destination = app.joinpath(*relative.parts)
            if entry.is_dir():
                destination.mkdir(parents=True, exist_ok=True)
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                with source.open(entry) as src, destination.open("wb") as dst:
                    while block := src.read(1024 * 1024):
                        dst.write(block)
                count += 1
    data_dir = app / "data_dir"
    data_dir.mkdir(exist_ok=True)
    write_windows_text(
        data_dir / "_README.txt",
        "このフォルダーはポータブル設定の保存先です。削除せず、アプリ本体と一緒に持ち運んでください。\n",
        bom=True,
    )
    write_windows_text(PACKAGE / "Start-Snapmaker-Orca.cmd", LAUNCHER)
    write_windows_text(PACKAGE / "使い方.txt", README, bom=True)
    shutil.copyfile(report, PACKAGE / "検証結果.txt")
    provenance = {
        "application": "Snapmaker Orca",
        "version": "2.4.1",
        "platform": "Windows x64",
        "publisher": "Snapmaker",
        "official_release": "https://github.com/Snapmaker/OrcaSlicer/releases/tag/v2.4.1",
        "source_code": "https://github.com/Snapmaker/OrcaSlicer/tree/v2.4.1",
        "official_asset": OFFICIAL_NAME,
        "official_asset_url": OFFICIAL_URL,
        "official_asset_sha256": OFFICIAL_SHA256,
        "upstream_files_modified": False,
        "upstream_file_count": count,
        "additions": ["Start-Snapmaker-Orca.cmd", "App/data_dir/_README.txt", "使い方.txt", "PROVENANCE.json", "検証結果.txt", "SHA256SUMS.txt"],
        "webview2_runtime_bundled": False,
    }
    (PACKAGE / "PROVENANCE.json").write_text(
        json.dumps(provenance, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({"package": str(PACKAGE), "upstream_files": count}, ensure_ascii=False))


def archive_package() -> None:
    if not PACKAGE.is_dir():
        raise FileNotFoundError(PACKAGE)
    runtime_files = [path.relative_to(PACKAGE).as_posix()
                     for path in (PACKAGE / "App" / "data_dir").rglob("*")
                     if path.is_file() and path.name != "_README.txt"]
    if runtime_files:
        raise ValueError(f"Refusing to distribute a used data folder: {runtime_files[:10]}")
    original = WORKSPACE / "downloads" / OFFICIAL_NAME
    if sha256(original) != OFFICIAL_SHA256:
        raise ValueError("The official source ZIP failed its SHA-256 check.")
    with zipfile.ZipFile(original) as upstream:
        executable = next(entry for entry in upstream.infolist()
                          if PurePosixPath(entry.filename).name.lower() == "snapmaker-orca.exe")
        prefix = PurePosixPath(executable.filename).parent
        verified_files = 0
        for entry in upstream.infolist():
            if entry.is_dir():
                continue
            relative = PurePosixPath(entry.filename).relative_to(prefix)
            local = PACKAGE / "App" / Path(*relative.parts)
            with upstream.open(entry) as stream:
                upstream_hash = hashlib.file_digest(stream, "sha256").hexdigest()
            if sha256(local) != upstream_hash:
                raise ValueError(f"A vendor file has changed: {relative}")
            verified_files += 1
    print(f"Verified {verified_files} vendor files byte-for-byte by SHA-256.", flush=True)
    destination = WORKSPACE / (PACKAGE_NAME + ".zip")
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite {destination}")
    files = sorted(path for path in PACKAGE.rglob("*") if path.is_file() and path.name != "SHA256SUMS.txt")
    checksums = "".join(f"{sha256(path)}  {path.relative_to(PACKAGE).as_posix()}\n" for path in files)
    (PACKAGE / "SHA256SUMS.txt").write_text(checksums, encoding="utf-8", newline="\n")
    with zipfile.ZipFile(destination, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as target:
        for path in sorted(PACKAGE.rglob("*")):
            target.write(path, path.relative_to(WORKSPACE).as_posix())
    with zipfile.ZipFile(destination) as target:
        if bad := target.testzip():
            raise ValueError(f"Output ZIP CRC check failed: {bad}")
    digest = sha256(destination)
    destination.with_suffix(".zip.sha256").write_text(f"{digest}  {destination.name}\n", encoding="ascii")
    print(json.dumps({"archive": str(destination), "bytes": destination.stat().st_size, "sha256": digest}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", action="store_true", help="Archive the prepared, verified folder.")
    arguments = parser.parse_args()
    if arguments.zip:
        archive_package()
    else:
        prepare()
