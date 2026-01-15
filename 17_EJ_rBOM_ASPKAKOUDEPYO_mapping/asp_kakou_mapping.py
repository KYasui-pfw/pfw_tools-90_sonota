# -*- coding: utf-8 -*-
"""
ASP加工伝票マッピングスクリプト

処理内容:
1. EJとrBOMからCSVファイルをコピー
2. 加工部番と製番をキーにしてマッピング
3. 結果を3つのファイルに振り分けて出力
"""

import shutil
import sys
import logging
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# パス設定
BASE_DIR = Path(__file__).parent
LOG_DIR = BASE_DIR / "log"

# ログ設定
def setup_logging():
    """ログ設定を行う"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # ログファイル名（日付付き）
    log_filename = LOG_DIR / f"log_{datetime.now().strftime('%Y%m%d')}.txt"

    # ロガー設定
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # 既存のハンドラをクリア
    logger.handlers.clear()

    # フォーマット
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    # ファイルハンドラ
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # コンソールハンドラ
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def cleanup_old_logs(days=7):
    """古いログファイルを削除する"""
    if not LOG_DIR.exists():
        return

    cutoff_date = datetime.now() - timedelta(days=days)

    for log_file in LOG_DIR.glob("log_*.txt"):
        try:
            # ファイル名から日付を取得
            date_str = log_file.stem.replace("log_", "")
            file_date = datetime.strptime(date_str, "%Y%m%d")

            if file_date < cutoff_date:
                log_file.unlink()
                logging.info(f"古いログファイルを削除: {log_file.name}")
        except (ValueError, OSError):
            pass


IN_EJ_DIR = BASE_DIR / "in_EJ"
IN_RBOM_DIR = BASE_DIR / "in_rBOM"
WORK_DIR = BASE_DIR / "work"


def connect_ej_server():
    """EJサーバーにネットワーク接続する"""
    logging.info("=" * 60)
    logging.info("EJサーバー接続")
    logging.info("=" * 60)
    logging.info(f"  サーバー: {EJ_SERVER}")
    logging.info(f"  ユーザー: {EJ_USER}")

    try:
        # net use コマンドを実行
        cmd = f'net use {EJ_SERVER} /user:{EJ_USER} {EJ_PASSWORD}'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        if result.returncode == 0:
            logging.info("  -> 接続成功")
            return True
        else:
            # エラーメッセージを確認
            error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
            # 既に接続されている場合もエラーにはしない
            if "既に" in error_msg or "already" in error_msg.lower():
                logging.info("  -> 既に接続されています")
                return True
            logging.error(f"  -> 接続失敗: {error_msg}")
            return False
    except Exception as e:
        logging.error(f"  -> 接続エラー: {e}")
        return False


def disconnect_ej_server():
    """EJサーバーからネットワーク切断する"""
    logging.info("=" * 60)
    logging.info("EJサーバー切断")
    logging.info("=" * 60)
    logging.info(f"  サーバー: {EJ_SERVER}")

    try:
        # net use /delete コマンドを実行
        cmd = f'net use {EJ_SERVER} /delete /y'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        if result.returncode == 0:
            logging.info("  -> 切断成功")
            return True
        else:
            error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
            # 接続が存在しない場合もエラーにはしない
            if "見つかりません" in error_msg or "not found" in error_msg.lower():
                logging.info("  -> 接続が存在しませんでした")
                return True
            logging.warning(f"  -> 切断時の警告: {error_msg}")
            return True  # 切断は失敗してもエラーにしない
    except Exception as e:
        logging.warning(f"  -> 切断時の警告: {e}")
        return True  # 切断は失敗してもエラーにしない


# コピー元ファイル（絶対パス）
EJ_SERVER = r"\\172.17.107.102"
EJ_USER = r"administrator@pfw_design.local"
EJ_PASSWORD = "1956fkthoy"
EJ_SOURCE = Path(r"\\172.17.107.102\PrintOutCsv\4.加工\4-03 ASPKakouDenpyo.csv")
RBOM_SOURCE = Path(r"\\esrv11\KakouDenpyo\4-03 ASPKakouDenpyo.csv")

# コピー先ファイル（相対パス）
EJ_DEST = IN_EJ_DIR / "ej_4-03 ASPKakouDenpyo.csv"
RBOM_DEST = IN_RBOM_DIR / "4-03 ASPKakouDenpyo.csv"

# 出力ファイル（1週目）
OUTPUT_BOTH_1 = WORK_DIR / "01_rBOM_EJ_both.csv"        # rBOMにありEJにもあったデータ
OUTPUT_RBOM_ONLY_1 = WORK_DIR / "01_rBOM_only.csv"      # rBOMにありEJになかったデータ
OUTPUT_EJ_ONLY_1 = WORK_DIR / "01_EJ_only.csv"          # rBOMになくEJにあったデータ

# 出力ファイル（2週目：rBOM加工部番の最後1文字を削除してマッピング）
OUTPUT_BOTH_2 = WORK_DIR / "02_rBOM_EJ_both.csv"        # rBOMにありEJにもあったデータ
OUTPUT_RBOM_ONLY_2 = WORK_DIR / "02_rBOM_only.csv"      # rBOMにありEJになかったデータ
OUTPUT_EJ_ONLY_2 = WORK_DIR / "02_EJ_only.csv"          # rBOMになくEJにあったデータ

# 最終出力フォルダ・ファイル
OUT_DIR = BASE_DIR / "perl_denpyo"
OUTPUT_MERGED = WORK_DIR / "03_最終結合ファイル.csv"  # 両方の伝票Noを含む
OUTPUT_FINAL = OUT_DIR / "4-03 ASPKakouDenpyo.csv"    # rBOM伝票No削除後


def copy_files():
    """ファイルをコピーする"""
    logging.info("=" * 60)
    logging.info("ファイルコピー開始")
    logging.info("=" * 60)

    # EJファイルのコピー
    logging.info(f"EJファイル:")
    logging.info(f"  コピー元: {EJ_SOURCE}")
    logging.info(f"  コピー先: {EJ_DEST}")
    if EJ_SOURCE.exists():
        shutil.copy2(EJ_SOURCE, EJ_DEST)
        logging.info("  -> コピー完了")
    else:
        logging.error("  -> エラー: コピー元ファイルが存在しません")
        return False

    # rBOMファイルのコピー
    logging.info(f"rBOMファイル:")
    logging.info(f"  コピー元: {RBOM_SOURCE}")
    logging.info(f"  コピー先: {RBOM_DEST}")
    if RBOM_SOURCE.exists():
        shutil.copy2(RBOM_SOURCE, RBOM_DEST)
        logging.info("  -> コピー完了")
    else:
        logging.error("  -> エラー: コピー元ファイルが存在しません")
        return False

    return True


def mapping_data():
    """データをマッピングして振り分ける（2週実行）"""
    logging.info("=" * 60)
    logging.info("マッピング処理開始")
    logging.info("=" * 60)

    # CSVファイル読み込み（Shift-JIS）
    logging.info("CSVファイル読み込み中...")
    df_ej = pd.read_csv(EJ_DEST, encoding="cp932")
    df_rbom = pd.read_csv(RBOM_DEST, encoding="cp932")

    logging.info(f"  EJデータ: {len(df_ej)}件")
    logging.info(f"  rBOMデータ: {len(df_rbom)}件")

    # 数値カラムを整数に変換（小数点削除）
    # インデックス7:必要数, 8:未引当在庫数, 9:手持ち在庫数, 11:出庫済数
    numeric_cols_idx = [7, 8, 9, 11]
    for idx in numeric_cols_idx:
        ej_col = df_ej.columns[idx]
        rbom_col = df_rbom.columns[idx]
        df_ej[ej_col] = pd.to_numeric(df_ej[ej_col], errors="coerce").fillna(0).astype(int)
        df_rbom[rbom_col] = pd.to_numeric(df_rbom[rbom_col], errors="coerce").fillna(0).astype(int)
    logging.info("  数値カラム（必要数,未引当在庫数,手持ち在庫数,出庫済数）を整数に変換")

    # カラム名をインデックスで取得（文字化け対策）
    # インデックス5: 加工部番
    # インデックス10: 製番
    ej_kakou_col = df_ej.columns[5]    # 加工部番
    ej_seiban_col = df_ej.columns[10]  # 製番
    rbom_kakou_col = df_rbom.columns[5]    # 加工部番
    rbom_seiban_col = df_rbom.columns[10]  # 製番

    logging.info(f"  キーカラム（EJ）: [{ej_kakou_col}], [{ej_seiban_col}]")
    logging.info(f"  キーカラム（rBOM）: [{rbom_kakou_col}], [{rbom_seiban_col}]")

    # ========================================
    # 1週目: EJ加工部番 と rBOM加工部番（そのまま）
    # ========================================
    logging.info("-" * 60)
    logging.info("【1週目】EJ加工部番 と rBOM加工部番（そのまま）")
    logging.info("-" * 60)

    # マッピング用のキー列を作成（加工部番＋製番をキーとする）
    df_ej["_key"] = df_ej[ej_kakou_col].astype(str) + "_" + df_ej[ej_seiban_col].astype(str)
    df_rbom["_key"] = df_rbom[rbom_kakou_col].astype(str) + "_" + df_rbom[rbom_seiban_col].astype(str)

    # キーのセットを作成
    ej_keys = set(df_ej["_key"])
    rbom_keys = set(df_rbom["_key"])

    # 振り分け
    both_keys = rbom_keys & ej_keys          # 両方にある
    rbom_only_keys = rbom_keys - ej_keys     # rBOMのみ
    ej_only_keys = ej_keys - rbom_keys       # EJのみ

    logging.info(f"振り分け結果:")
    logging.info(f"  両方にあるデータ: {len(both_keys)}件")
    logging.info(f"  rBOMのみのデータ: {len(rbom_only_keys)}件")
    logging.info(f"  EJのみのデータ: {len(ej_only_keys)}件")

    # 両方にあるデータ（横結合）
    df_both_rbom = df_rbom[df_rbom["_key"].isin(both_keys)].copy()
    df_both_ej = df_ej[df_ej["_key"].isin(both_keys)].copy()

    # カラム名にプレフィックスを付けて区別
    df_both_rbom_renamed = df_both_rbom.drop(columns=["_key"]).add_prefix("rBOM_")
    df_both_ej_renamed = df_both_ej.add_prefix("EJ_")

    # _keyで結合
    df_both_rbom_renamed["_key"] = df_both_rbom["_key"].values
    df_both = pd.merge(df_both_rbom_renamed, df_both_ej_renamed, left_on="_key", right_on="EJ__key", how="inner")
    df_both = df_both.drop(columns=["_key", "EJ__key"])

    # rBOMのみのデータ
    df_rbom_only = df_rbom[df_rbom["_key"].isin(rbom_only_keys)].drop(columns=["_key"])

    # EJのみのデータ
    df_ej_only = df_ej[df_ej["_key"].isin(ej_only_keys)].drop(columns=["_key"])

    # CSVファイル出力（1週目）
    logging.info("出力ファイル:")

    df_both.to_csv(OUTPUT_BOTH_1, index=False, encoding="cp932")
    logging.info(f"  {OUTPUT_BOTH_1.name}: {len(df_both)}件")

    df_rbom_only.to_csv(OUTPUT_RBOM_ONLY_1, index=False, encoding="cp932")
    logging.info(f"  {OUTPUT_RBOM_ONLY_1.name}: {len(df_rbom_only)}件")

    df_ej_only.to_csv(OUTPUT_EJ_ONLY_1, index=False, encoding="cp932")
    logging.info(f"  {OUTPUT_EJ_ONLY_1.name}: {len(df_ej_only)}件")

    # ========================================
    # 2週目: 1週目でマッチしなかったデータを対象に
    #        rBOM加工部番の最後1文字を削除してマッピング
    # ========================================
    logging.info("-" * 60)
    logging.info("【2週目】1週目の残り同士でマッピング（rBOM加工部番の最後1文字削除）")
    logging.info("-" * 60)

    logging.info(f"  対象データ:")
    logging.info(f"    1週目rBOMのみ: {len(df_rbom_only)}件")
    logging.info(f"    1週目EJのみ: {len(df_ej_only)}件")

    # 1週目でマッチしなかったデータを使用
    df_rbom_only_copy = df_rbom_only.copy()
    df_ej_only_copy = df_ej_only.copy()

    # rBOMの加工部番から最後の1文字を削除してキーを作成
    df_ej_only_copy["_key2"] = df_ej_only_copy[ej_kakou_col].astype(str) + "_" + df_ej_only_copy[ej_seiban_col].astype(str)
    df_rbom_only_copy["_key2"] = df_rbom_only_copy[rbom_kakou_col].astype(str).str[:-1] + "_" + df_rbom_only_copy[rbom_seiban_col].astype(str)

    # キーのセットを作成
    ej_keys2 = set(df_ej_only_copy["_key2"])
    rbom_keys2 = set(df_rbom_only_copy["_key2"])

    # 振り分け
    both_keys2 = rbom_keys2 & ej_keys2          # 両方にある
    rbom_only_keys2 = rbom_keys2 - ej_keys2     # rBOMのみ
    ej_only_keys2 = ej_keys2 - rbom_keys2       # EJのみ

    logging.info(f"振り分け結果:")
    logging.info(f"  両方にあるデータ: {len(both_keys2)}件")
    logging.info(f"  rBOMのみのデータ: {len(rbom_only_keys2)}件")
    logging.info(f"  EJのみのデータ: {len(ej_only_keys2)}件")

    # 両方にあるデータ（横結合）
    df_both_rbom2 = df_rbom_only_copy[df_rbom_only_copy["_key2"].isin(both_keys2)].copy()
    df_both_ej2 = df_ej_only_copy[df_ej_only_copy["_key2"].isin(both_keys2)].copy()

    # カラム名にプレフィックスを付けて区別
    df_both_rbom_renamed2 = df_both_rbom2.drop(columns=["_key2"]).add_prefix("rBOM_")
    df_both_ej_renamed2 = df_both_ej2.add_prefix("EJ_")

    # _key2で結合
    df_both_rbom_renamed2["_key2"] = df_both_rbom2["_key2"].values
    df_both2 = pd.merge(df_both_rbom_renamed2, df_both_ej_renamed2, left_on="_key2", right_on="EJ__key2", how="inner")
    df_both2 = df_both2.drop(columns=["_key2", "EJ__key2"])

    # rBOMのみのデータ
    df_rbom_only2 = df_rbom_only_copy[df_rbom_only_copy["_key2"].isin(rbom_only_keys2)].drop(columns=["_key2"])

    # EJのみのデータ
    df_ej_only2 = df_ej_only_copy[df_ej_only_copy["_key2"].isin(ej_only_keys2)].drop(columns=["_key2"])

    # CSVファイル出力（2週目）
    logging.info("出力ファイル:")

    df_both2.to_csv(OUTPUT_BOTH_2, index=False, encoding="cp932")
    logging.info(f"  {OUTPUT_BOTH_2.name}: {len(df_both2)}件")

    df_rbom_only2.to_csv(OUTPUT_RBOM_ONLY_2, index=False, encoding="cp932")
    logging.info(f"  {OUTPUT_RBOM_ONLY_2.name}: {len(df_rbom_only2)}件")

    df_ej_only2.to_csv(OUTPUT_EJ_ONLY_2, index=False, encoding="cp932")
    logging.info(f"  {OUTPUT_EJ_ONLY_2.name}: {len(df_ej_only2)}件")

    # ========================================
    # 最終CSV出力
    # ========================================
    logging.info("-" * 60)
    logging.info("【最終出力】")
    logging.info("-" * 60)

    # 伝票Noのカラム（インデックス4）
    ej_denpyo_col = df_ej.columns[4]      # EJの伝票No（チーム番）
    rbom_denpyo_col = df_rbom.columns[4]  # rBOMの伝票No（チーNo）

    # EJのカラム名を取得（元のカラム順序を維持）
    ej_columns = list(df_ej.columns)
    # _keyカラムを除外
    ej_columns = [c for c in ej_columns if not c.startswith("_key")]

    # rBOMのカラム名を取得（製番区分とrBOM伝票Noを除外）
    rbom_columns = list(df_rbom.columns)
    # _keyカラムと製番区分（最後のカラム）を除外
    rbom_columns = [c for c in rbom_columns if not c.startswith("_key")]
    rbom_columns = rbom_columns[:-1]  # 最後の製番区分を削除
    # rBOMの伝票No（インデックス4）も除外
    rbom_columns = [c for c in rbom_columns if c != rbom_denpyo_col]

    # rBOM伝票Noの列名（結合ファイル用）
    RBOM_DENPYO_COL_NAME = "伝票No"

    # 生産月次カラム（インデックス3）
    seisan_getsuji_col = df_ej.columns[3]

    # ========================================
    # 1. マッピングできたデータ（EJ + rBOM伝票Noを最後に追加）
    #    生産月次が202602以降の場合はrBOMの伝票Noを伝票Ｎｏ列に使用
    # ========================================

    # 1週目のマッチしたデータ
    df_matched_ej_1 = df_ej[df_ej["_key"].isin(both_keys)][ej_columns].copy()
    df_matched_rbom_1 = df_rbom[df_rbom["_key"].isin(both_keys)][["_key", rbom_denpyo_col]].copy()
    df_matched_rbom_1 = df_matched_rbom_1.rename(columns={rbom_denpyo_col: RBOM_DENPYO_COL_NAME})
    # EJにキーを追加してマージ
    df_matched_ej_1["_key"] = df_ej[df_ej["_key"].isin(both_keys)]["_key"].values
    df_matched_1 = pd.merge(df_matched_ej_1, df_matched_rbom_1, on="_key", how="left")
    df_matched_1 = df_matched_1.drop(columns=["_key"])
    # 生産月次が202602以降の場合、伝票ＮｏにrBOMの伝票Noを使用
    mask_1 = df_matched_1[seisan_getsuji_col].astype(str).str[:6] >= "202602"
    df_matched_1.loc[mask_1, ej_denpyo_col] = df_matched_1.loc[mask_1, RBOM_DENPYO_COL_NAME]

    # 2週目のマッチしたデータ
    df_matched_ej_2 = df_ej_only_copy[df_ej_only_copy["_key2"].isin(both_keys2)][ej_columns].copy()
    df_matched_rbom_2 = df_rbom_only_copy[df_rbom_only_copy["_key2"].isin(both_keys2)][["_key2", rbom_denpyo_col]].copy()
    df_matched_rbom_2 = df_matched_rbom_2.rename(columns={rbom_denpyo_col: RBOM_DENPYO_COL_NAME})
    # EJにキーを追加してマージ
    df_matched_ej_2["_key2"] = df_ej_only_copy[df_ej_only_copy["_key2"].isin(both_keys2)]["_key2"].values
    df_matched_2 = pd.merge(df_matched_ej_2, df_matched_rbom_2, on="_key2", how="left")
    df_matched_2 = df_matched_2.drop(columns=["_key2"])
    # 生産月次が202602以降の場合、伝票ＮｏにrBOMの伝票Noを使用
    mask_2 = df_matched_2[seisan_getsuji_col].astype(str).str[:6] >= "202602"
    df_matched_2.loc[mask_2, ej_denpyo_col] = df_matched_2.loc[mask_2, RBOM_DENPYO_COL_NAME]

    # ========================================
    # 2. マッピングできなかったデータ（伝票Noは空）
    # ========================================

    # マッピングできなかったEJ
    df_unmatched_ej = df_ej_only2[ej_columns].copy()
    df_unmatched_ej[RBOM_DENPYO_COL_NAME] = ""

    # マッピングできなかったrBOM（製番区分を除外、伝票NoはEJの伝票Ｎｏ列に入れる）
    df_unmatched_rbom = df_rbom_only2[rbom_columns].copy()
    # rBOMの伝票NoをEJの伝票Ｎｏ列に設定
    df_unmatched_rbom[ej_denpyo_col] = df_rbom_only2[rbom_denpyo_col].values
    df_unmatched_rbom[RBOM_DENPYO_COL_NAME] = ""

    # ========================================
    # 縦結合して結合ファイル出力
    # ========================================
    df_merged = pd.concat([df_matched_1, df_matched_2, df_unmatched_ej, df_unmatched_rbom], ignore_index=True)

    logging.info(f"  マッチしたデータ（1週目）: {len(df_matched_1)}件")
    logging.info(f"  マッチしたデータ（2週目）: {len(df_matched_2)}件")
    logging.info(f"  マッチしなかったEJ: {len(df_unmatched_ej)}件")
    logging.info(f"  マッチしなかったrBOM: {len(df_unmatched_rbom)}件")
    logging.info(f"  合計: {len(df_merged)}件")

    # 結合ファイル出力（両方の伝票Noを含む）
    df_merged.to_csv(OUTPUT_MERGED, index=False, encoding="cp932")
    logging.info(f"出力ファイル:")
    logging.info(f"  {OUTPUT_MERGED.name}: {len(df_merged)}件")

    # ========================================
    # out出力前の編集処理
    # ========================================
    # カラム名取得（インデックスで参照）
    inch_col = df_ej.columns[14]       # 吋
    kishumei_col = df_ej.columns[13]   # 機種名
    seiban_col = df_ej.columns[10]     # 製番

    # 1. 「吋」が空欄の場合は「機種名」も空欄にする
    mask_inch_empty = df_merged[inch_col].isna() | (df_merged[inch_col].astype(str).str.strip() == "")
    df_merged.loc[mask_inch_empty, kishumei_col] = ""

    # 2. 「製番」がAから始まる場合は「機種名」を「STOCK」にする
    mask_seiban_a = df_merged[seiban_col].astype(str).str.upper().str.startswith("A")
    df_merged.loc[mask_seiban_a, kishumei_col] = "STOCK"

    # ========================================
    # 伝票No列（rBOMの伝票No）を削除して最終出力
    # ========================================
    df_final = df_merged.drop(columns=[RBOM_DENPYO_COL_NAME])

    # 出力フォルダ作成
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 最終CSV出力
    df_final.to_csv(OUTPUT_FINAL, index=False, encoding="cp932")
    logging.info(f"  {OUTPUT_FINAL}: {len(df_final)}件")

    return True


def main():
    """メイン処理"""
    # ログ設定
    setup_logging()

    # 古いログファイルを削除（7日以上前）
    cleanup_old_logs(days=7)

    logging.info("=" * 60)
    logging.info("ASP加工伝票マッピング処理 開始")
    logging.info("=" * 60)

    try:
        # ディレクトリ確認
        for dir_path in [IN_EJ_DIR, IN_RBOM_DIR, WORK_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # EJサーバーに接続
        if not connect_ej_server():
            logging.error("エラー: EJサーバーへの接続に失敗しました")
            return

        try:
            # ファイルコピー
            if not copy_files():
                logging.error("エラー: ファイルコピーに失敗しました")
                return

            # マッピング処理
            if not mapping_data():
                logging.error("エラー: マッピング処理に失敗しました")
                return

            logging.info("=" * 60)
            logging.info("処理完了")
            logging.info("=" * 60)

        finally:
            # EJサーバーから切断（エラーが発生しても必ず切断）
            disconnect_ej_server()

    except Exception as e:
        logging.error(f"予期しないエラーが発生しました: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
