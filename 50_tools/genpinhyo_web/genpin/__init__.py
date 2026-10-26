"""現品票システムの共通部品。

    config      ファイルの場所・接続先
    db          genpinhyo.db の接続・テーブル定義・バックアップ・記録
    portal_api  業務ポータル（Django）の読み取りAPI   ※標準ライブラリだけ（check_input も使う）
    irepo       i-Reporter の PostgreSQL（読むだけ）
    rbom        rBOM の FastAPI（読むだけ。CHANGE GEAR BOX 用）
    update      データ更新（加工伝票 → genpinhyo）。画面と夜間処理で共通
    listing     画面の一覧を組み立てる
    tag_excel   現品票の Excel（QRコード付き）
    conmas      i-Reporter の帳票の自動作成（ConMas Manager を Chrome で操作）
    ui          Streamlit の画面の共通部品

⚠ ここ（__init__.py）では何も import しない。check_input は pandas の無い環境で
  portal_api だけを使うので、ここで pandas を読み込むと動かなくなる。
"""
