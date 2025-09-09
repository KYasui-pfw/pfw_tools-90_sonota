import streamlit as st
import sqlite3
import pandas as pd
import os
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine, text
import io
import numpy as np
from decimal import Decimal
import plotly.graph_objects as go  # ヒートマップ用にインポート
import time  # 自動更新用にインポート


def main():
    st.set_page_config(layout="wide", page_title="進捗確認設定更新")

    HIDE_ST_STYLE = """
            <style>
            div[data-testid="stToolbar"],
            div[data-testid="stDecoration"],
            #MainMenu,
            header,
            footer {
                display: none !important; /* 強制的に非表示にし、スペースも占有しない */
                height: 0px !important; /* 念のため高さも0に */
            }
            .appview-container .main .block-container{
                        padding-top: 1rem;
                        padding-right: 3rem;
                        padding-left: 3rem;
                        padding-bottom: 1rem;
                    }
                    .reportview-container {
                        padding-top: 0rem;
                        padding-right: 3rem;
                        padding-left: 3rem;
                        padding-bottom: 0rem;
                    }
                    header[data-testid="stHeader"] {
                        z-index: -1;
                    }
                    div[data-testid="stToolbar"] {
                    z-index: 100;
                    }
                    div[data-testid="stDecoration"] {
                    z-index: 100;
                    }
            .block-container {
                        padding-top: 0rem !important;
                        padding-bottom: 0rem !important;
                    }
            </style>
            </style>
            """
    st.markdown(HIDE_ST_STYLE, unsafe_allow_html=True)
    # 1. CSVデータ定義
    # (CSVデータ定義は長いため、ここでは省略します。実際のスクリプトには含まれています)
    # -----------------------------------------------------------------------------
    # view_report_636 用のCSVデータ
    # -----------------------------------------------------------------------------
    csv_data_string_636 = """項目名,作業者名,作業チェック
    cluster_1_22_t,cluster_1_28_t,cluster_1_34_t
    cluster_1_35_t,cluster_1_41_t,cluster_1_47_n
    cluster_1_48_t,cluster_1_54_t,cluster_1_60_n
    cluster_1_61_t,cluster_1_67_t,cluster_1_73_n
    cluster_1_74_t,cluster_1_80_t,cluster_1_86_n
    cluster_1_87_t,cluster_1_93_t,cluster_1_99_n
    cluster_1_100_t,cluster_1_106_t,cluster_1_112_n
    cluster_1_113_t,cluster_1_119_t,cluster_1_125_n
    cluster_1_126_t,cluster_1_132_t,cluster_1_138_n
    cluster_1_139_t,cluster_1_145_t,cluster_1_151_n
    cluster_1_152_t,cluster_1_158_t,cluster_1_164_n
    cluster_1_165_t,cluster_1_171_t,cluster_1_177_n
    cluster_1_178_t,cluster_1_184_t,cluster_1_190_n
    cluster_1_191_t,cluster_1_197_t,cluster_1_203_n
    cluster_1_204_t,cluster_1_210_t,cluster_1_216_n
    cluster_1_217_t,cluster_1_223_t,cluster_1_229_n
    cluster_1_230_t,cluster_1_236_t,cluster_1_242_n
    cluster_1_243_t,cluster_1_249_t,cluster_1_255_n
    cluster_1_256_t,cluster_1_262_t,cluster_1_268_n
    cluster_1_269_t,cluster_1_275_t,cluster_1_281_n
    cluster_1_282_t,cluster_1_288_t,cluster_1_294_n
    cluster_1_295_t,cluster_1_301_t,cluster_1_307_n
    cluster_1_308_t,cluster_1_314_t,cluster_1_320_n
    cluster_1_321_t,cluster_1_327_t,cluster_1_333_n
    cluster_1_334_t,cluster_1_340_t,cluster_1_346_n
    cluster_1_347_t,cluster_1_353_t,cluster_1_359_n
    cluster_1_360_t,cluster_1_366_t,cluster_1_372_n
    cluster_1_373_t,cluster_1_379_t,cluster_1_385_n
    cluster_1_386_t,cluster_1_392_t,cluster_1_398_n
    cluster_1_399_t,cluster_1_405_t,cluster_1_411_n
    cluster_1_412_t,cluster_1_418_t,cluster_1_424_n
    cluster_1_425_t,cluster_1_431_t,cluster_1_437_n
    cluster_1_438_t,cluster_1_444_t,cluster_1_450_n
    cluster_1_451_t,cluster_1_457_t,cluster_1_463_n
    cluster_2_12_t,cluster_2_18_t,cluster_2_24_t
    cluster_2_25_t,cluster_2_31_t,cluster_2_37_t
    cluster_2_38_t,cluster_2_44_t,cluster_2_50_t
    cluster_2_51_t,cluster_2_57_t,cluster_2_63_t
    cluster_2_64_t,cluster_2_70_t,cluster_2_76_t
    cluster_2_77_t,cluster_2_83_t,cluster_2_89_t
    cluster_2_90_t,cluster_2_96_t,cluster_2_102_t
    cluster_2_103_t,cluster_2_109_t,cluster_2_115_t
    cluster_2_116_t,cluster_2_122_t,cluster_2_128_t
    cluster_2_129_t,cluster_2_135_t,cluster_2_141_t
    cluster_2_142_t,cluster_2_148_t,cluster_2_154_t
    cluster_2_155_t,cluster_2_161_t,cluster_2_167_t
    cluster_2_168_t,cluster_2_174_t,cluster_2_180_t
    cluster_2_181_t,cluster_2_187_t,cluster_2_193_t
    cluster_2_194_t,cluster_2_200_t,cluster_2_206_t
    cluster_2_207_t,cluster_2_213_t,cluster_2_219_t
    cluster_2_220_t,cluster_2_226_t,cluster_2_232_t
    cluster_2_233_t,cluster_2_239_t,cluster_2_245_t
    cluster_2_246_t,cluster_2_252_t,cluster_2_258_t
    cluster_2_259_t,cluster_2_265_t,cluster_2_271_t
    cluster_2_272_t,cluster_2_278_t,cluster_2_284_t
    cluster_2_285_t,cluster_2_291_t,cluster_2_297_t
    cluster_2_298_t,cluster_2_304_t,cluster_2_310_t
    cluster_2_311_t,cluster_2_317_t,cluster_2_323_t
    cluster_2_324_t,cluster_2_330_t,cluster_2_336_t
    cluster_2_337_t,cluster_2_343_t,cluster_2_349_t
    cluster_2_350_t,cluster_2_356_t,cluster_2_362_t
    cluster_2_363_t,cluster_2_369_t,cluster_2_375_t
    cluster_2_376_t,cluster_2_382_t,cluster_2_388_t
    """

    # -----------------------------------------------------------------------------
    # view_report_637 用のCSVデータ
    # -----------------------------------------------------------------------------
    csv_data_string_637 = """項目名,作業者名,作業チェック
    cluster_1_22_t,cluster_1_28_t,cluster_1_34_t
    cluster_1_35_t,cluster_1_41_t,cluster_1_47_n
    cluster_1_48_t,cluster_1_54_t,cluster_1_60_n
    cluster_1_61_t,cluster_1_67_t,cluster_1_73_n
    cluster_1_74_t,cluster_1_80_t,cluster_1_86_n
    cluster_1_87_t,cluster_1_93_t,cluster_1_99_n
    cluster_1_100_t,cluster_1_106_t,cluster_1_112_n
    cluster_1_113_t,cluster_1_119_t,cluster_1_125_n
    cluster_1_126_t,cluster_1_132_t,cluster_1_138_n
    cluster_1_139_t,cluster_1_145_t,cluster_1_151_n
    cluster_1_152_t,cluster_1_158_t,cluster_1_164_n
    cluster_1_165_t,cluster_1_171_t,cluster_1_177_n
    cluster_1_178_t,cluster_1_184_t,cluster_1_190_n
    cluster_1_191_t,cluster_1_197_t,cluster_1_203_n
    cluster_1_204_t,cluster_1_210_t,cluster_1_216_n
    cluster_1_217_t,cluster_1_223_t,cluster_1_229_n
    cluster_1_230_t,cluster_1_236_t,cluster_1_242_n
    cluster_1_243_t,cluster_1_249_t,cluster_1_255_n
    cluster_1_256_t,cluster_1_262_t,cluster_1_268_n
    cluster_1_269_t,cluster_1_275_t,cluster_1_281_n
    cluster_1_282_t,cluster_1_288_t,cluster_1_294_n
    cluster_1_295_t,cluster_1_301_t,cluster_1_307_n
    cluster_1_308_t,cluster_1_314_t,cluster_1_320_n
    cluster_1_321_t,cluster_1_327_t,cluster_1_333_n
    cluster_1_334_t,cluster_1_340_t,cluster_1_346_n
    cluster_1_347_t,cluster_1_353_t,cluster_1_359_n
    cluster_1_360_t,cluster_1_366_t,cluster_1_372_n
    cluster_1_373_t,cluster_1_379_t,cluster_1_385_n
    cluster_1_386_t,cluster_1_392_t,cluster_1_398_n
    cluster_1_399_t,cluster_1_405_t,cluster_1_411_n
    cluster_1_412_t,cluster_1_418_t,cluster_1_424_n
    cluster_1_425_t,cluster_1_431_t,cluster_1_437_n
    cluster_1_438_t,cluster_1_444_t,cluster_1_450_n
    cluster_1_451_t,cluster_1_457_t,cluster_1_463_n
    cluster_2_12_t,cluster_2_18_t,cluster_2_24_t
    cluster_2_25_t,cluster_2_31_t,cluster_2_37_t
    cluster_2_38_t,cluster_2_44_t,cluster_2_50_t
    cluster_2_51_t,cluster_2_57_t,cluster_2_63_t
    cluster_2_64_t,cluster_2_70_t,cluster_2_76_t
    cluster_2_77_t,cluster_2_83_t,cluster_2_89_t
    cluster_2_90_t,cluster_2_96_t,cluster_2_102_t
    cluster_2_103_t,cluster_2_109_t,cluster_2_115_t
    cluster_2_116_t,cluster_2_122_t,cluster_2_128_t
    cluster_2_129_t,cluster_2_135_t,cluster_2_141_t
    cluster_2_142_t,cluster_2_148_t,cluster_2_154_t
    cluster_2_155_t,cluster_2_161_t,cluster_2_167_t
    cluster_2_168_t,cluster_2_174_t,cluster_2_180_t
    cluster_2_181_t,cluster_2_187_t,cluster_2_193_t
    cluster_2_194_t,cluster_2_200_t,cluster_2_206_t
    cluster_2_207_t,cluster_2_213_t,cluster_2_219_t
    cluster_2_220_t,cluster_2_226_t,cluster_2_232_t
    cluster_2_233_t,cluster_2_239_t,cluster_2_245_t
    cluster_2_246_t,cluster_2_252_t,cluster_2_258_t
    cluster_2_259_t,cluster_2_265_t,cluster_2_271_t
    cluster_2_272_t,cluster_2_278_t,cluster_2_284_t
    cluster_2_285_t,cluster_2_291_t,cluster_2_297_t
    cluster_2_298_t,cluster_2_304_t,cluster_2_310_t
    cluster_2_311_t,cluster_2_317_t,cluster_2_323_t
    cluster_2_324_t,cluster_2_330_t,cluster_2_336_t
    cluster_2_337_t,cluster_2_343_t,cluster_2_349_t
    cluster_2_350_t,cluster_2_356_t,cluster_2_362_t
    cluster_2_363_t,cluster_2_369_t,cluster_2_375_t
    cluster_2_376_t,cluster_2_382_t,cluster_2_388_t
    cluster_2_389_t,cluster_2_395_t,cluster_2_401_t
    cluster_2_402_t,cluster_2_408_t,cluster_2_414_t
    cluster_2_415_t,cluster_2_421_t,cluster_2_427_t
    cluster_2_428_t,cluster_2_434_t,cluster_2_440_t
    cluster_2_441_t,cluster_2_447_t,cluster_2_453_t
    cluster_3_12_t,cluster_3_18_t,cluster_3_24_t
    cluster_3_25_t,cluster_3_31_t,cluster_3_37_t
    cluster_3_38_t,cluster_3_44_t,cluster_3_50_t
    cluster_3_51_t,cluster_3_57_t,cluster_3_63_t
    cluster_3_64_t,cluster_3_70_t,cluster_3_76_t
    cluster_3_77_t,cluster_3_83_t,cluster_3_89_t
    cluster_3_90_t,cluster_3_96_t,cluster_3_102_t
    cluster_3_103_t,cluster_3_109_t,cluster_3_115_t
    cluster_3_116_t,cluster_3_122_t,cluster_3_128_t
    cluster_3_129_t,cluster_3_135_t,cluster_3_141_t
    cluster_3_142_t,cluster_3_148_t,cluster_3_154_t
    cluster_3_155_t,cluster_3_161_t,cluster_3_167_t
    cluster_3_168_t,cluster_3_174_t,cluster_3_180_t
    cluster_3_181_t,cluster_3_187_t,cluster_3_193_t
    cluster_3_194_t,cluster_3_200_t,cluster_3_206_t
    cluster_3_207_t,cluster_3_213_t,cluster_3_219_t
    cluster_3_220_t,cluster_3_226_t,cluster_3_232_t
    cluster_3_233_t,cluster_3_239_t,cluster_3_245_t
    cluster_3_246_t,cluster_3_252_t,cluster_3_258_t
    cluster_3_259_t,cluster_3_265_t,cluster_3_271_t
    cluster_3_272_t,cluster_3_278_t,cluster_3_284_t
    cluster_3_285_t,cluster_3_291_t,cluster_3_297_t
    cluster_3_298_t,cluster_3_304_t,cluster_3_310_t
    cluster_3_311_t,cluster_3_317_t,cluster_3_323_t
    cluster_3_324_t,cluster_3_330_t,cluster_3_336_t
    cluster_3_337_t,cluster_3_343_t,cluster_3_349_t
    cluster_3_350_t,cluster_3_356_t,cluster_3_362_t
    cluster_3_363_t,cluster_3_369_t,cluster_3_375_t
    cluster_3_376_t,cluster_3_382_t,cluster_3_388_t
    """

    # -----------------------------------------------------------------------------
    # view_report_638 用のCSVデータ
    # -----------------------------------------------------------------------------
    csv_data_string_638 = """項目名,作業者名,作業チェック
    cluster_1_22_t,cluster_1_28_t,cluster_1_34_t
    cluster_1_35_t,cluster_1_41_t,cluster_1_47_n
    cluster_1_48_t,cluster_1_54_t,cluster_1_60_n
    cluster_1_61_t,cluster_1_67_t,cluster_1_73_n
    cluster_1_74_t,cluster_1_80_t,cluster_1_86_n
    cluster_1_87_t,cluster_1_93_t,cluster_1_99_n
    cluster_1_100_t,cluster_1_106_t,cluster_1_112_n
    cluster_1_113_t,cluster_1_119_t,cluster_1_125_n
    cluster_1_126_t,cluster_1_132_t,cluster_1_138_n
    cluster_1_139_t,cluster_1_145_t,cluster_1_151_n
    cluster_1_152_t,cluster_1_158_t,cluster_1_164_n
    cluster_1_165_t,cluster_1_171_t,cluster_1_177_n
    cluster_1_178_t,cluster_1_184_t,cluster_1_190_n
    cluster_1_191_t,cluster_1_197_t,cluster_1_203_n
    cluster_1_204_t,cluster_1_210_t,cluster_1_216_n
    cluster_1_217_t,cluster_1_223_t,cluster_1_229_n
    cluster_1_230_t,cluster_1_236_t,cluster_1_242_n
    cluster_1_243_t,cluster_1_249_t,cluster_1_255_n
    cluster_1_256_t,cluster_1_262_t,cluster_1_268_n
    cluster_1_269_t,cluster_1_275_t,cluster_1_281_n
    cluster_1_282_t,cluster_1_288_t,cluster_1_294_n
    cluster_1_295_t,cluster_1_301_t,cluster_1_307_n
    cluster_1_308_t,cluster_1_314_t,cluster_1_320_n
    cluster_1_321_t,cluster_1_327_t,cluster_1_333_n
    cluster_1_334_t,cluster_1_340_t,cluster_1_346_n
    cluster_1_347_t,cluster_1_353_t,cluster_1_359_n
    cluster_1_360_t,cluster_1_366_t,cluster_1_372_n
    cluster_1_373_t,cluster_1_379_t,cluster_1_385_n
    cluster_1_386_t,cluster_1_392_t,cluster_1_398_n
    cluster_1_399_t,cluster_1_405_t,cluster_1_411_n
    cluster_1_412_t,cluster_1_418_t,cluster_1_424_n
    cluster_1_425_t,cluster_1_431_t,cluster_1_437_n
    cluster_1_438_t,cluster_1_444_t,cluster_1_450_n
    cluster_1_451_t,cluster_1_457_t,cluster_1_463_n
    cluster_2_12_t,cluster_2_18_t,cluster_2_24_t
    cluster_2_25_t,cluster_2_31_t,cluster_2_37_t
    cluster_2_38_t,cluster_2_44_t,cluster_2_50_t
    cluster_2_51_t,cluster_2_57_t,cluster_2_63_t
    cluster_2_64_t,cluster_2_70_t,cluster_2_76_t
    cluster_2_77_t,cluster_2_83_t,cluster_2_89_t
    cluster_2_90_t,cluster_2_96_t,cluster_2_102_t
    cluster_2_103_t,cluster_2_109_t,cluster_2_115_t
    cluster_2_116_t,cluster_2_122_t,cluster_2_128_t
    cluster_2_129_t,cluster_2_135_t,cluster_2_141_t
    cluster_2_142_t,cluster_2_148_t,cluster_2_154_t
    cluster_2_155_t,cluster_2_161_t,cluster_2_167_t
    cluster_2_168_t,cluster_2_174_t,cluster_2_180_t
    cluster_2_181_t,cluster_2_187_t,cluster_2_193_t
    cluster_2_194_t,cluster_2_200_t,cluster_2_206_t
    cluster_2_207_t,cluster_2_213_t,cluster_2_219_t
    cluster_2_220_t,cluster_2_226_t,cluster_2_232_t
    cluster_2_233_t,cluster_2_239_t,cluster_2_245_t
    cluster_2_246_t,cluster_2_252_t,cluster_2_258_t
    cluster_2_259_t,cluster_2_265_t,cluster_2_271_t
    cluster_2_272_t,cluster_2_278_t,cluster_2_284_t
    cluster_2_285_t,cluster_2_291_t,cluster_2_297_t
    cluster_2_298_t,cluster_2_304_t,cluster_2_310_t
    cluster_2_311_t,cluster_2_317_t,cluster_2_323_t
    cluster_2_324_t,cluster_2_330_t,cluster_2_336_t
    cluster_2_337_t,cluster_2_343_t,cluster_2_349_t
    cluster_2_350_t,cluster_2_356_t,cluster_2_362_t
    cluster_2_363_t,cluster_2_369_t,cluster_2_375_t
    cluster_2_376_t,cluster_2_382_t,cluster_2_388_t
    cluster_2_389_t,cluster_2_395_t,cluster_2_401_t
    cluster_2_402_t,cluster_2_408_t,cluster_2_414_t
    cluster_2_415_t,cluster_2_421_t,cluster_2_427_t
    cluster_2_428_t,cluster_2_434_t,cluster_2_440_t
    cluster_2_441_t,cluster_2_447_t,cluster_2_453_t
    cluster_3_12_t,cluster_3_18_t,cluster_3_24_t
    cluster_3_25_t,cluster_3_31_t,cluster_3_37_t
    cluster_3_38_t,cluster_3_44_t,cluster_3_50_t
    cluster_3_51_t,cluster_3_57_t,cluster_3_63_t
    cluster_3_64_t,cluster_3_70_t,cluster_3_76_t
    cluster_3_77_t,cluster_3_83_t,cluster_3_89_t
    cluster_3_90_t,cluster_3_96_t,cluster_3_102_t
    cluster_3_103_t,cluster_3_109_t,cluster_3_115_t
    cluster_3_116_t,cluster_3_122_t,cluster_3_128_t
    cluster_3_129_t,cluster_3_135_t,cluster_3_141_t
    cluster_3_142_t,cluster_3_148_t,cluster_3_154_t
    cluster_3_155_t,cluster_3_161_t,cluster_3_167_t
    cluster_3_168_t,cluster_3_174_t,cluster_3_180_t
    cluster_3_181_t,cluster_3_187_t,cluster_3_193_t
    cluster_3_194_t,cluster_3_200_t,cluster_3_206_t
    cluster_3_207_t,cluster_3_213_t,cluster_3_219_t
    cluster_3_220_t,cluster_3_226_t,cluster_3_232_t
    cluster_3_233_t,cluster_3_239_t,cluster_3_245_t
    cluster_3_246_t,cluster_3_252_t,cluster_3_258_t
    cluster_3_259_t,cluster_3_265_t,cluster_3_271_t
    cluster_3_272_t,cluster_3_278_t,cluster_3_284_t
    cluster_3_285_t,cluster_3_291_t,cluster_3_297_t
    cluster_3_298_t,cluster_3_304_t,cluster_3_310_t
    cluster_3_311_t,cluster_3_317_t,cluster_3_323_t
    cluster_3_324_t,cluster_3_330_t,cluster_3_336_t
    cluster_3_337_t,cluster_3_343_t,cluster_3_349_t
    cluster_3_350_t,cluster_3_356_t,cluster_3_362_t
    cluster_3_363_t,cluster_3_369_t,cluster_3_375_t
    cluster_3_376_t,cluster_3_382_t,cluster_3_388_t
    cluster_3_389_t,cluster_3_395_t,cluster_3_401_t
    cluster_3_402_t,cluster_3_408_t,cluster_3_414_t
    cluster_3_415_t,cluster_3_421_t,cluster_3_427_t
    cluster_3_428_t,cluster_3_434_t,cluster_3_440_t
    cluster_3_441_t,cluster_3_447_t,cluster_3_453_t
    cluster_4_12_t,cluster_4_18_t,cluster_4_24_t
    cluster_4_25_t,cluster_4_31_t,cluster_4_37_t
    cluster_4_38_t,cluster_4_44_t,cluster_4_50_t
    cluster_4_51_t,cluster_4_57_t,cluster_4_63_t
    cluster_4_64_t,cluster_4_70_t,cluster_4_76_t
    cluster_4_77_t,cluster_4_83_t,cluster_4_89_t
    cluster_4_90_t,cluster_4_96_t,cluster_4_102_t
    cluster_4_103_t,cluster_4_109_t,cluster_4_115_t
    cluster_4_116_t,cluster_4_122_t,cluster_4_128_t
    cluster_4_129_t,cluster_4_135_t,cluster_4_141_t
    cluster_4_142_t,cluster_4_148_t,cluster_4_154_t
    cluster_4_155_t,cluster_4_161_t,cluster_4_167_t
    cluster_4_168_t,cluster_4_174_t,cluster_4_180_t
    cluster_4_181_t,cluster_4_187_t,cluster_4_193_t
    cluster_4_194_t,cluster_4_200_t,cluster_4_206_t
    cluster_4_207_t,cluster_4_213_t,cluster_4_219_t
    cluster_4_220_t,cluster_4_226_t,cluster_4_232_t
    cluster_4_233_t,cluster_4_239_t,cluster_4_245_t
    cluster_4_246_t,cluster_4_252_t,cluster_4_258_t
    cluster_4_259_t,cluster_4_265_t,cluster_4_271_t
    cluster_4_272_t,cluster_4_278_t,cluster_4_284_t
    cluster_4_285_t,cluster_4_291_t,cluster_4_297_t
    cluster_4_298_t,cluster_4_304_t,cluster_4_310_t
    cluster_4_311_t,cluster_4_317_t,cluster_4_323_t
    cluster_4_324_t,cluster_4_330_t,cluster_4_336_t
    cluster_4_337_t,cluster_4_343_t,cluster_4_349_t
    cluster_4_350_t,cluster_4_356_t,cluster_4_362_t
    cluster_4_363_t,cluster_4_369_t,cluster_4_375_t
    cluster_4_376_t,cluster_4_382_t,cluster_4_388_t
    """

    DB_URL_POSTGRES = 'postgresql://postgres:cimtops@ESRV10/irepodb'
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_folder = os.path.join(script_dir, '..', 'Database')
    sqlite_db_path = os.path.join(db_folder, 'hontai_seizo.db')
    DB_URL_SQLITE = f'sqlite:///{sqlite_db_path}'

    PROGRESS_CHECK_TABLE_NAME = 'progress_check_targets'
    MODEL_TYPE_TABLE_NAME = 'model_type_table'
    PRODUCTION_MACHINE_INFO_TABLE_NAME = 'production_machine_info'
    REPORT_TYPE_TABLE_NAME = 'report_type_table'

    model_type_df = pd.DataFrame()

    # --- データ処理関数 ---

    def load_base_csv_df(csv_string):
        try:
            base_df = pd.read_csv(io.StringIO(csv_string))
            return base_df
        except Exception as e:
            st.error(f"CSVデータの読み込みに失敗しました: {e}")
            return pd.DataFrame()

    def fetch_report_data(engine, table_name, year_str, month_str, order_num_str=None,
                          additional_filter_type=None,
                          prev_next_details=None,
                          final_check_db_col=None,
                          final_approval_db_col=None):

        # 月と次数のフォーマット (0埋めや空文字の扱い)
        formatted_month_str = month_str
        if month_str and month_str.startswith('0') and len(month_str) == 2:
            try:
                month_int = int(month_str)
                formatted_month_str = str(month_int)  # "01" -> "1"
            except ValueError:
                pass

        formatted_order_num_str = None
        if order_num_str and str(order_num_str).strip() != "":
            current_order_num_str = str(order_num_str).strip()
            if current_order_num_str.startswith('0') and len(current_order_num_str) == 2:
                try:
                    order_int = int(current_order_num_str)
                    formatted_order_num_str = str(order_int)  # "01" -> "1"
                except ValueError:
                    formatted_order_num_str = current_order_num_str  # 変換できない場合はそのまま
            else:
                formatted_order_num_str = current_order_num_str

        params = {}

        # 主条件 (選択された年月次)
        main_conditions_parts = []
        main_conditions_parts.append("top_remarks1 = :main_year")
        params['main_year'] = str(year_str)
        main_conditions_parts.append("top_remarks2 = :main_month")
        params['main_month'] = formatted_month_str

        if formatted_order_num_str:
            main_conditions_parts.append("top_remarks3 = :main_order_num")
            params['main_order_num'] = formatted_order_num_str

        main_condition_sql = f"({' AND '.join(main_conditions_parts)})"

        # 全体のWHERE句のリスト
        # 「前後1次」と「未完了フィルター」は同時には選択されない前提
        if additional_filter_type == 'previous_next_order' and prev_next_details:
            where_clauses_list = [main_condition_sql]  # 主条件を最初に含める
            plus_y, plus_m, plus_o = prev_next_details[0]
            minus_y, minus_m, minus_o = prev_next_details[1]

            # Plus condition
            plus_conditions_parts = []
            plus_conditions_parts.append("top_remarks1 = :plus_year")
            params['plus_year'] = str(plus_y)
            plus_conditions_parts.append("top_remarks2 = :plus_month")
            params['plus_month'] = str(int(plus_m))
            if plus_o is not None and str(plus_o).strip() != "":
                plus_conditions_parts.append("top_remarks3 = :plus_order")
                params['plus_order'] = str(int(plus_o))
            where_clauses_list.append(
                f"({' AND '.join(plus_conditions_parts)})")

            # Minus condition
            minus_conditions_parts = []
            minus_conditions_parts.append("top_remarks1 = :minus_year")
            params['minus_year'] = str(minus_y)
            minus_conditions_parts.append("top_remarks2 = :minus_month")
            params['minus_month'] = str(int(minus_m))
            if minus_o is not None and str(minus_o).strip() != "":
                minus_conditions_parts.append("top_remarks3 = :minus_order")
                params['minus_order'] = str(int(minus_o))
            where_clauses_list.append(
                f"({' AND '.join(minus_conditions_parts)})")

            sql_query_full = f"SELECT * FROM {table_name} WHERE {' OR '.join(where_clauses_list)}"

        else:  # 「未完了フィルター」またはフィルターなしの場合
            additional_or_conditions = []  # ORで結合する追加条件
            if additional_filter_type == 'final_check_incomplete' and final_check_db_col:
                additional_or_conditions.append(
                    f"({final_check_db_col} <> '4' OR {final_check_db_col} IS NULL)")
            elif additional_filter_type == 'final_approval_incomplete' and final_approval_db_col:
                additional_or_conditions.append(
                    f"({final_approval_db_col} <> '4' OR {final_approval_db_col} IS NULL)")

            if additional_or_conditions:
                # 主条件 OR (追加の未完了条件)
                sql_query_full = f"SELECT * FROM {table_name} WHERE {main_condition_sql} OR ({' AND '.join(additional_or_conditions)})"
            else:
                # フィルターなしの場合
                sql_query_full = f"SELECT * FROM {table_name} WHERE {main_condition_sql}"

        try:
            with engine.connect() as connection:
                result = connection.execute(text(sql_query_full), params)
                db_data_rows = result.fetchall()
            return db_data_rows
        except Exception as e:
            st.error(f"テーブル {table_name} からのデータ取得中にエラーが発生しました: {e}")
            st.error(f"実行しようとしたSQL: {sql_query_full}")
            st.error(f"使用したパラメータ: {params}")
            return []

    def create_final_dataframe(db_records, column_map_df, final_check_db_col_name=None, final_approval_db_col_name=None):
        # db_records: SQLAlchemyからのRowProxyオブジェクトのリスト
        # column_map_df: CSVカラム名（'項目名', '作業者名', '作業チェック'）をDBカラム名にマッピングするDataFrame
        # final_check_db_col_name: "最終ﾁｪｯｸ_検印" のDBカラム名
        # final_approval_db_col_name: "最終承認" のDBカラム名

        if not db_records:
            # st.warning("データベースレコードが空のため、DataFrameを作成できません。") # 必要に応じてコメント解除
            return pd.DataFrame()
        if column_map_df.empty:
            st.warning("カラム名マッピング用のCSVデータが空のため、DataFrameを作成できません。")
            return pd.DataFrame()

        processed_rows = []
        # 組立番号ごとに処理するため、まずグループ化
        from itertools import groupby

        # db_recordsがソートされていない可能性があるため、事前にソートする
        # top_remarks4 は '組立番号'
        db_records_sorted = sorted(
            db_records, key=lambda r: getattr(r, 'top_remarks4', ''))

        for assembly_number, group in groupby(db_records_sorted, key=lambda r: str(getattr(r, 'top_remarks4', ''))):
            group_list = list(group)  # イテレータを複数回使用するためにリスト化
            # 通常の項目処理
            for record in group_list:  # この組立番号の各レコードを反復処理
                for _, csv_row_def in column_map_df.iterrows():  # CSVで定義された項目を反復処理
                    item_col_name, worker_col_name, check_col_name = csv_row_def[
                        '項目名'], csv_row_def['作業者名'], csv_row_def['作業チェック']
                    item_value, worker_value, check_value = None, None, None
                    try:  # RowProxy（辞書のようなもの）としてアクセス試行
                        record_dict = record._mapping
                        item_value, worker_value, check_value = record_dict.get(
                            item_col_name.strip()), record_dict.get(worker_col_name.strip()), record_dict.get(check_col_name.strip())
                        # DBの値がカラム名自体の場合はNoneとして扱う（プレースホルダー）
                        if isinstance(worker_value, str) and worker_value == worker_col_name:
                            worker_value = None
                        if isinstance(item_value, str) and item_value == item_col_name:
                            item_value = None
                        if isinstance(check_value, str) and check_value == check_col_name:
                            check_value = None
                    except AttributeError:  # 他のレコードタイプ（RowProxyが期待されるが）のためのフォールバック
                        item_value = getattr(record, item_col_name, None)
                        if isinstance(item_value, str) and item_value == item_col_name:
                            item_value = None
                        worker_value = getattr(
                            record, worker_col_name, None)
                        if isinstance(worker_value, str) and worker_value == worker_col_name:
                            worker_value = None
                        check_value = getattr(record, check_col_name, None)
                        if isinstance(check_value, str) and check_value == check_col_name:
                            check_value = None

                    processed_rows.append(
                        {'組立番号': assembly_number, '項目名': item_value, '作業者名': worker_value, '作業チェック': check_value})

            # 「最終ﾁｪｯｸ_検印」項目の処理 (組立番号ごとに1レコード)
            if final_check_db_col_name:
                record_for_check = group_list[0]  # この組立番号グループの最初のレコードを使用
                final_check_raw_val = getattr(
                    record_for_check, final_check_db_col_name, None)

                completion_status_check = 0  # デフォルトは0（未着手）
                if pd.notna(final_check_raw_val) and str(final_check_raw_val).strip():
                    completion_status_check = 1  # 1としてマーク（作業中/完了）
                    if str(final_check_raw_val) == '2':  # 特定の値 '2'
                        completion_status_check = 2
                    elif str(final_check_raw_val) == '4':  # '4' は完了を示す特別な値として扱う
                        completion_status_check = 1  # 通常の完了として扱う（ヒートマップの色分けで考慮）

                processed_rows.append({
                    '組立番号': assembly_number,
                    '項目名': '最終ﾁｪｯｸ_検印',
                    '作業者名': None,  # 通常、このタイプのチェックには特定の作業者はいない
                    '作業チェック': final_check_raw_val,  # DBからの生の値を保存
                    '完了区分': completion_status_check
                })
            else:  # final_check_db_col_name が未定義の場合でも、構造のためにプレースホルダー行を追加
                processed_rows.append({
                    '組立番号': assembly_number,
                    '項目名': '最終ﾁｪｯｸ_検印',
                    '作業者名': None,
                    '作業チェック': None,
                    '完了区分': 0
                })

            # 「最終承認」項目の処理 (組立番号ごとに1レコード)
            if final_approval_db_col_name:
                # この組立番号グループの最初のレコードから承認ステータスを取得
                record_for_approval = group_list[0]
                final_approval_raw_val = getattr(
                    record_for_approval, final_approval_db_col_name, None)

                completion_status_approval = 0  # デフォルトは0（未着手）
                if pd.notna(final_approval_raw_val) and str(final_approval_raw_val).strip():
                    completion_status_approval = 1  # 1としてマーク（作業中/完了）
                    if str(final_approval_raw_val) == '2':  # 特定の値 '2' は異なる完了状態を意味する
                        completion_status_approval = 2
                    elif str(final_approval_raw_val) == '4':  # '4' は完了を示す特別な値として扱う
                        completion_status_approval = 1  # 通常の完了として扱う

                processed_rows.append({
                    '組立番号': assembly_number,
                    '項目名': '最終承認',
                    '作業者名': None,  # 通常、承認ステータスには特定の作業者はいない
                    '作業チェック': final_approval_raw_val,  # DBからの生の値を保存
                    '完了区分': completion_status_approval
                })
            else:  # 最終承認のデータがない場合も項目として追加し、完了区分を0とする
                processed_rows.append({
                    '組立番号': assembly_number,
                    '項目名': '最終承認',
                    '作業者名': None,
                    '作業チェック': None,
                    '完了区分': 0  # データがない場合は未着手扱い
                })
        return pd.DataFrame(processed_rows) if processed_rows else pd.DataFrame()

    def fetch_and_merge_progress_data(engine, target_year_str, target_month_str):
        year_col_sqlite, month_col_sqlite, kishu_col_sqlite = "年", "月", "機種区分"
        # SKおよびDKタイプ用のDataFrameをカテゴリ番号のインデックスで初期化
        df_sk = pd.DataFrame(index=pd.RangeIndex(
            start=1, stop=31, name="カテゴリ番号インデックス"), columns=['カテゴリNo_', 'カテゴリ名'])
        df_dk = pd.DataFrame(index=pd.RangeIndex(
            start=1, stop=31, name="カテゴリ番号インデックス"), columns=['カテゴリNo_', 'カテゴリ名'])

        for kishu_val, target_df in [('SK', df_sk), ('DK', df_dk)]:  # 各機種タイプについて処理
            # progress_check_targets および model_type_table からのデータを保持
            prog_data, model_data = None, None
            # 指定された機種タイプ、年、月の最新の進捗確認レコードを取得するSQL
            sql_prog = text(
                f'SELECT * FROM "{PROGRESS_CHECK_TABLE_NAME}" WHERE "{kishu_col_sqlite}" = :k AND ("{year_col_sqlite}" < :y OR ("{year_col_sqlite}" = :y AND "{month_col_sqlite}" <= :m)) ORDER BY "{year_col_sqlite}" DESC, "{month_col_sqlite}" DESC LIMIT 1')
            try:
                with engine.connect() as conn:
                    res = conn.execute(sql_prog, {
                                       'k': kishu_val, 'y': target_year_str, 'm': target_month_str}).fetchone()
                    if res:
                        prog_data = res._asdict()  # RowProxyをdictに変換
            except Exception as e:
                st.warning(
                    f"{PROGRESS_CHECK_TABLE_NAME} ({kishu_val}) 取得エラー: {e}")

            # 機種タイプデータが利用可能な場合は取得
            if not model_type_df.empty and kishu_col_sqlite in model_type_df.columns:
                model_series = model_type_df[model_type_df[kishu_col_sqlite] == kishu_val]
                if not model_series.empty:
                    model_data = model_series.iloc[0].to_dict()

            nos, names = [None]*30, [None]*30  # カテゴリ番号と名前のリストを初期化
            if prog_data:  # 進捗データからカテゴリ番号を移入
                for i in range(1, 31):
                    if f"カテゴリNo_{i}" in prog_data:
                        nos[i-1] = prog_data[f"カテゴリNo_{i}"]
            if model_data:  # 機種データからカテゴリ名を移入
                for i in range(1, 31):
                    if f"カテゴリ名{i}" in model_data:
                        val = model_data[f"カテゴリ名{i}"]
                        if pd.notna(val) and str(val).strip():  # 値がNaNでなく、空文字列でないことを確認
                            names[i-1] = f"【{str(val).strip()}】"  # 名前をフォーマット

            target_df['カテゴリNo_'], target_df['カテゴリ名'] = nos, names
            # カテゴリ番号が欠損している行を削除
            target_df.dropna(subset=['カテゴリNo_'], inplace=True)
            target_df.reset_index(drop=True, inplace=True)
        return df_sk, df_dk

    def process_final_combined_dataframe(df_orig):
        df = df_orig.copy()

        def robust_convert_and_clean(value):
            """
            値の型を安全に判別し、変換・整形を行うための頑健な関数
            """
            # 最初にNoneやNaN(欠損値)を処理し、エラーを防ぐ
            if pd.isna(value):
                return None

            # 型が Decimal の場合、数値(float)に変換する
            if isinstance(value, Decimal):
                return float(value)

            # 型が文字列 (str) の場合、空白を削除し、空文字なら None にする
            if isinstance(value, str):
                stripped_value = value.strip()
                return None if stripped_value == "" else stripped_value

            # すでに数値 (int or float) の場合は、そのまま返す
            if isinstance(value, (int, float)):
                return value

            # 上記のいずれにも当てはまらない予期せぬデータは、とりあえず文字列に変換する
            return str(value)

        if df.empty:
            return df
        # 特定の列をクリーニング
        for col in ['項目名', '作業者名', '作業チェック']:
            if col in df.columns and df[col].dtype == 'object':
                # df[col] = df[col].str.strip().replace('', None) # 元のアプローチ
                df[col] = df[col].apply(
                    robust_convert_and_clean)  # 堅牢なクリーニングを適用

        # 「最終承認」と「最終ﾁｪｯｸ_検印」以外の項目の「作業チェック」を0に変換
        special_items = ['最終承認', '最終ﾁｪｯｸ_検印']
        if '作業チェック' in df.columns and '項目名' in df.columns:
            df.loc[~df['項目名'].isin(special_items), '作業チェック'] = df.loc[~df['項目名'].isin(special_items), '作業チェック'].apply(
                lambda x: 0 if pd.notna(x) and str(x).strip() else None)

        # '項目名' をフォーマットし、括弧付きの項目または特別項目のみを保持
        if '項目名' in df.columns:
            df['項目名'] = df['項目名'].apply(lambda x: x if (pd.notna(x) and isinstance(
                x, str) and x.startswith('【') and x.endswith('】')) or x in special_items else None)

        req_cols = ['組立番号', '項目名', '作業チェック']  # 「未展開」ロジックに必要な列

        if not all(col in df.columns for col in req_cols):
            st.warning(f"「未展開」処理に必要な列不足。ステップ3をスキップ。")
        else:
            def apply_logic(group):  # 各組立グループ内の「未展開」項目を処理するロジック
                # 条件1: 全ての '項目名' と '作業チェック' がnull
                cond1 = (group['項目名'].isnull() &
                         group['作業チェック'].isnull()).all()

                # cond2ロジックから特別項目を除外
                non_special_group = group[~group['項目名'].isin(special_items)]
                # 条件2: 全ての非特別 '項目名' がnullで、'作業チェック' が0
                cond2 = (non_special_group['項目名'].isnull() & (
                    non_special_group['作業チェック'] == 0)).all() if not non_special_group.empty else False

                # ドロップする行をマークするSeries
                drop = pd.Series(False, index=group.index)
                if cond1 and not group.empty:  # 全ての項目がnullの場合、最初の項目を「【未展開】」とし、他をドロップ
                    group.loc[group.index[0], '項目名'] = "【未展開】"
                    drop.iloc[1:] = True
                elif cond2 and not group.empty:  # 全ての非特別項目がnullでチェック0の場合、最初の項目を「【未展開】」とする
                    group.loc[group.index[0], '項目名'] = "【未展開】"
                    drop.iloc[1:] = True
                else:
                    # '項目名' がnullで '作業チェック' が0の非特別項目をドロップ
                    drop = (group['項目名'].isnull()) & (
                        group['作業チェック'] == 0) & (~group['項目名'].isin(special_items))
                return group[~drop]  # マークされた行を除いたグループを返す

            df = df.groupby('組立番号', group_keys=False, sort=False).apply(
                apply_logic).reset_index(drop=True)

        # '完了区分' が存在しない場合は初期化
        if '項目名' in df.columns and '完了区分' not in df.columns:
            df['完了区分'] = 0  # デフォルトは0

        # '項目名' に基づいて '完了区分' を設定
        if '項目名' in df.columns:
            is_not_special_item = ~df['項目名'].isin(special_items)
            bracketed = df['項目名'].str.startswith(
                '【', na=False) & df['項目名'].str.endswith('】', na=False)
            not_undeployed = df['項目名'] != "【未展開】"

            # 括弧付き、未展開でない、非特別項目の場合、完了区分 = 1
            df.loc[is_not_special_item & bracketed &
                   not_undeployed, '完了区分'] = 1
            # 「【未展開】」の非特別項目の場合、完了区分 = 0
            df.loc[is_not_special_item & (
                df['項目名'] == "【未展開】"), '完了区分'] = 0

            # '作業者名' に基づくさらなる完了区分ロジック
            if '作業者名' in df.columns and '組立番号' in df.columns:
                for _, group in df.groupby('組立番号', sort=False):  # 組立番号でグループ化して反復処理
                    # 完了区分 = 1 の非特別項目を考慮
                    non_special_group_completed = group[(
                        ~group['項目名'].isin(special_items)) & (group['完了区分'] == 1)]
                    for idx in non_special_group_completed.index:  # これらの項目を反復処理
                        if idx not in df.index or df.loc[idx, '項目名'] == "【未展開】":
                            continue  # インデックスが無効か、項目が「【未展開】」の場合はスキップ

                        pos, found_blank = group.index.get_loc(idx), False
                        # 次の括弧付き/特別項目または空白の '作業者名' まで後続の行をチェック
                        for i in range(pos + 1, len(group)):
                            next_idx = group.index[i]
                            if next_idx not in df.index:
                                continue
                            # 次の項目が新しいカテゴリか特別項目の場合は停止
                            if (pd.notna(df.loc[next_idx, '項目名']) and df.loc[next_idx, '項目名'].startswith('【')) or \
                                    df.loc[next_idx, '項目名'] in special_items:
                                break
                            # 空白の '作業者名' が見つかった場合は空白としてマーク
                            if pd.isna(df.loc[next_idx, '作業者名']) or \
                                    (isinstance(df.loc[next_idx, '作業者名'], str) and not df.loc[next_idx, '作業者名'].strip()):
                                found_blank = True
                                break
                        if found_blank:  # 空白が見つかった場合、現在の項目の完了区分を0に設定
                            df.loc[idx, '完了区分'] = 0
        return df

    def fetch_production_data_and_merge(engine, assembly_numbers_list):
        """
        指定された組立番号のリストに基づいて、production_machine_info テーブルからデータを取得し、
        report_type_table とマージして機種区分を付与する。
        """
        if not assembly_numbers_list:
            return pd.DataFrame()

        # SQLインジェクションを避けるため、プレースホルダーの数を動的に生成
        # SQLiteでは `?` をプレースホルダーとして使用
        placeholders = ', '.join(['?'] * len(assembly_numbers_list))

        sql_query_str = f"""
            SELECT "組立番号", "年", "月", "次", "帳票No" 
            FROM "{PRODUCTION_MACHINE_INFO_TABLE_NAME}" 
            WHERE "組立番号" IN ({placeholders})
        """
        # SQLAlchemyのtext()を使用する場合、パラメータはリスト/タプルとして渡す
        # text()オブジェクト自体はパラメータ展開を直接サポートしないため、
        # pd.read_sql_query に直接SQL文字列とパラメータタプルを渡す

        prod_df = pd.DataFrame()
        try:
            with engine.connect() as conn:
                # pd.read_sql_query はSQL文字列とパラメータのタプルを受け付ける
                prod_df = pd.read_sql_query(
                    sql_query_str, conn, params=tuple(assembly_numbers_list))
        except Exception as e:
            st.error(f"{PRODUCTION_MACHINE_INFO_TABLE_NAME}取得エラー:{e}")
            st.error(f"実行しようとしたSQL (production_machine_info): {sql_query_str}")
            st.error(
                f"使用したパラメータ (production_machine_info): {tuple(assembly_numbers_list)}")
            return pd.DataFrame()

        if prod_df.empty:
            return pd.DataFrame()

        report_df = pd.DataFrame()
        try:
            with engine.connect() as conn:
                report_df = pd.read_sql_query(
                    f'SELECT "帳票No", "機種区分" FROM "{REPORT_TYPE_TABLE_NAME}"', conn)
        except Exception as e:
            st.error(f"{REPORT_TYPE_TABLE_NAME}取得エラー:{e}")
            prod_df['機種区分'] = pd.NA
            return prod_df

        if report_df.empty:
            st.warning(f"{REPORT_TYPE_TABLE_NAME}データなし。機種区分が結合できません。")
            prod_df['機種区分'] = pd.NA
            return prod_df

        try:
            prod_df["帳票No"] = prod_df["帳票No"].astype(str)
            report_df["帳票No"] = report_df["帳票No"].astype(str)

            merged_df = pd.merge(prod_df, report_df, on="帳票No", how='left')

            if "組立番号" in merged_df.columns:
                merged_df["組立番号"] = merged_df["組立番号"].astype(str)
            return merged_df
        except Exception as e:
            st.error(f"製造・帳票マージエラー:{e}")
            prod_df['機種区分'] = pd.NA
            return prod_df

    # --- DBエンジン初期化 ---
    db_engine_postgres, db_engine_sqlite = None, None
    try:
        db_engine_postgres = create_engine(DB_URL_POSTGRES)
    except Exception as e:
        st.error(f"PostgreSQL接続エラー: {e}")
    try:
        db_engine_sqlite = create_engine(DB_URL_SQLITE)
        # SQLiteからmodel_type_dfをロード
        with db_engine_sqlite.connect() as conn_sqlite:
            try:
                model_type_df = pd.read_sql_query(
                    f'SELECT * FROM "{MODEL_TYPE_TABLE_NAME}"', conn_sqlite)
            except Exception as e_model:
                st.error(f"{MODEL_TYPE_TABLE_NAME}読込エラー:{e_model}")
                model_type_df = pd.DataFrame()  # エラー時は空のDataFrameを確実にする
    except Exception as e:
        st.error(f"SQLite接続エラー: {e}")
        model_type_df = pd.DataFrame()  # エラー時は空のDataFrameを確実にする

    # --- 入力 ---
    today = datetime.today().date()
    years = [str(y) for y in range(today.year - 1, today.year + 2)]  # 年選択範囲
    months = [f"{m:02d}" for m in range(1, 13)]  # 月選択
    orders = [" "] + [f"{o:02d}" for o in range(1, 9)]  # 次数選択（''は全次数）

    # 入力セレクタのレイアウト変更
    col_year, col_month, col_order, col_, col_add_filter, col_orientation = st.columns([
        1, 1, 1, 0.3, 1.3, 1])
    with col_year:
        sel_y = st.selectbox(
            "生産計画年", years, index=years.index(str(today.year)))  # デフォルトは当年
    with col_month:
        sel_m = st.selectbox("生産計画月", months, index=today.month-1)  # デフォルトは当月
    with col_order:
        sel_o = st.selectbox("生産計画次", orders, index=0)  # デフォルトは「全次数」

    additional_filter_type_selected = None  # SQLクエリ用
    prev_next_details_for_fetch = None  # SQLクエリ用
    with col_:
        st.write(" ")

    with col_add_filter:
        disop_options = ['', '前後１次を表示', '最終ﾁｪｯｸ未完了の全表示', '最終承認未完了の全表示']
        disop = st.selectbox('＋追加表示条件', disop_options, index=0)

        s_nenplus, s_nenminus = 0, 0
        s_getsuplus, s_getsuminus = "01", "12"  # 文字列で初期化
        s_jiplus, s_jiminus = "01", "08"  # 文字列で初期化

        if disop == "前後１次を表示":
            additional_filter_type_selected = 'previous_next_order'
            current_nen = int(sel_y)
            current_getsu = sel_m  # 文字列 "01" など
            current_ji = sel_o  # 文字列 " " または "01" など

            # --- 「前後1次を表示」のロジック (1進捗状況確認.py より移植・調整) ---
            if current_getsu == '':  # 月が空欄の場合 (通常は発生しないが念のため)
                s_nenplus = current_nen + 1
                s_nenminus = current_nen - 1
                s_getsuplus = '01'
                s_getsuminus = '12'
                s_jiplus = '01'
                s_jiminus = '08'
            elif current_getsu == '01':
                if current_ji == ' ' or current_ji == '':  # 次が空欄
                    s_nenplus = current_nen
                    s_nenminus = current_nen - 1
                    s_getsuplus = '02'
                    s_getsuminus = '12'
                    s_jiplus = '01'
                    s_jiminus = '08'
                elif current_ji == '01':
                    s_nenplus = current_nen
                    s_nenminus = current_nen - 1
                    s_getsuplus = '01'
                    s_getsuminus = '12'
                    s_jiplus = '02'
                    s_jiminus = '08'
                elif current_ji == '08':
                    s_nenplus = current_nen
                    s_nenminus = current_nen
                    s_getsuplus = '02'
                    s_getsuminus = '01'
                    s_jiplus = '01'
                    s_jiminus = '07'
                else:  # 次が01と08以外
                    s_nenplus = current_nen
                    s_nenminus = current_nen
                    s_getsuplus = '01'
                    s_getsuminus = '01'
                    s_jiplus = f"{int(current_ji)+1:02d}"
                    s_jiminus = f"{int(current_ji)-1:02d}"
            elif current_getsu == '12':
                if current_ji == ' ' or current_ji == '':
                    s_nenplus = current_nen + 1
                    s_nenminus = current_nen
                    s_getsuplus = '01'
                    s_getsuminus = '11'
                    s_jiplus = '01'
                    s_jiminus = '08'
                elif current_ji == '01':
                    s_nenplus = current_nen
                    s_nenminus = current_nen
                    s_getsuplus = '12'
                    s_getsuminus = '11'
                    s_jiplus = '02'
                    s_jiminus = '08'
                elif current_ji == '08':
                    s_nenplus = current_nen + 1
                    s_nenminus = current_nen
                    s_getsuplus = '01'
                    s_getsuminus = '12'
                    s_jiplus = '01'
                    s_jiminus = '07'
                else:  # 次が01と08以外
                    s_nenplus = current_nen
                    s_nenminus = current_nen
                    s_getsuplus = '12'
                    s_getsuminus = '12'
                    s_jiplus = f"{int(current_ji)+1:02d}"
                    s_jiminus = f"{int(current_ji)-1:02d}"
            else:  # 月が01と12以外
                if current_ji == ' ' or current_ji == '':
                    s_nenplus = current_nen
                    s_nenminus = current_nen
                    s_getsuplus = f"{int(current_getsu)+1:02d}"
                    s_getsuminus = f"{int(current_getsu)-1:02d}"
                    s_jiplus = '01'
                    s_jiminus = '08'
                elif current_ji == '01':
                    s_nenplus = current_nen
                    s_nenminus = current_nen
                    s_getsuplus = current_getsu
                    s_getsuminus = f"{int(current_getsu)-1:02d}"
                    s_jiplus = '02'
                    s_jiminus = '08'
                elif current_ji == '08':
                    s_nenplus = current_nen
                    s_nenminus = current_nen
                    s_getsuplus = f"{int(current_getsu)+1:02d}"
                    s_getsuminus = current_getsu
                    s_jiplus = '01'
                    s_jiminus = '07'
                else:  # 次が01と08以外
                    s_nenplus = current_nen
                    s_nenminus = current_nen
                    s_getsuplus = current_getsu
                    s_getsuminus = current_getsu
                    s_jiplus = f"{int(current_ji)+1:02d}"
                    s_jiminus = f"{int(current_ji)-1:02d}"

            prev_next_details_for_fetch = (
                (s_nenplus, s_getsuplus, s_jiplus),
                (s_nenminus, s_getsuminus, s_jiminus)
            )

        elif disop == "最終ﾁｪｯｸ未完了の全表示":
            additional_filter_type_selected = 'final_check_incomplete'
        elif disop == "最終承認未完了の全表示":
            additional_filter_type_selected = 'final_approval_incomplete'

    with col_orientation:
        muki = st.selectbox('進捗向き', ['横', '縦'], index=0)

    order_ui = None if sel_o == " " else sel_o

    placeholder = st.empty()

    while True:
        with placeholder.container():
            if db_engine_postgres and db_engine_sqlite:
                configs = [
                    {'n': 'view_report_636', 'c': csv_data_string_636,
                     'final_check_db_col': 'cluster_2_398_t',
                     'final_approval_db_col': 'cluster_2_397_t'},
                    {'n': 'view_report_637', 'c': csv_data_string_637,
                     'final_check_db_col': 'cluster_3_398_t',
                     'final_approval_db_col': 'cluster_3_397_t'},
                    {'n': 'view_report_638', 'c': csv_data_string_638,
                     'final_check_db_col': 'cluster_4_398_t',
                     'final_approval_db_col': 'cluster_4_397_t'},
                    {'n': 'view_report_747', 'c': csv_data_string_636,
                     'final_check_db_col': 'cluster_2_398_t',
                     'final_approval_db_col': 'cluster_2_397_t'},
                    {'n': 'view_report_751', 'c': csv_data_string_637,
                     'final_check_db_col': 'cluster_3_398_t',
                     'final_approval_db_col': 'cluster_3_397_t'},
                    {'n': 'view_report_752', 'c': csv_data_string_638,
                     'final_check_db_col': 'cluster_4_398_t',
                     'final_approval_db_col': 'cluster_4_397_t'}
                ]
                dfs = []
                for cfg in configs:
                    map_df = load_base_csv_df(cfg['c'])
                    data_rows = fetch_report_data(
                        db_engine_postgres, cfg['n'], sel_y, sel_m, order_ui,
                        additional_filter_type=additional_filter_type_selected,
                        prev_next_details=prev_next_details_for_fetch,
                        final_check_db_col=cfg.get('final_check_db_col'),
                        final_approval_db_col=cfg.get('final_approval_db_col')
                    )
                    if data_rows:
                        single_df = create_final_dataframe(
                            data_rows, map_df,
                            cfg.get('final_check_db_col'),
                            cfg.get('final_approval_db_col'))
                        if not single_df.empty:
                            dfs.append(single_df)

                if dfs:
                    fcr_df = pd.concat(dfs, ignore_index=True)
                    fcr_df = process_final_combined_dataframe(fcr_df)

                    # --- fetch_production_data_and_merge の呼び出し変更 ---
                    prod_rel_data = pd.DataFrame()  # 初期化
                    if not fcr_df.empty and '組立番号' in fcr_df.columns:
                        unique_assembly_numbers = fcr_df['組立番号'].unique(
                        ).tolist()
                        if unique_assembly_numbers:
                            prod_rel_data = fetch_production_data_and_merge(
                                db_engine_sqlite,
                                assembly_numbers_list=unique_assembly_numbers  # 組立番号リストを渡す
                            )
                    # --- 呼び出し変更ここまで ---

                    if not prod_rel_data.empty and '組立番号' in fcr_df.columns and '組立番号' in prod_rel_data.columns:
                        fcr_df['組立番号'] = fcr_df['組立番号'].astype(str)
                        prod_rel_data['組立番号'] = prod_rel_data['組立番号'].astype(
                            str)
                        cols_merge = ['組立番号', '機種区分']
                        prod_sel = prod_rel_data[[
                            c for c in cols_merge if c in prod_rel_data.columns]]
                        if '組立番号' in prod_sel.columns:
                            fcr_df = pd.merge(
                                fcr_df, prod_sel, on="組立番号", how="left")

                    df_sk_prog, df_dk_prog = fetch_and_merge_progress_data(
                        db_engine_sqlite, sel_y, sel_m)

                    if not fcr_df.empty:
                        if 'カテゴリNo_結合結果' not in fcr_df.columns:
                            fcr_df['カテゴリNo_結合結果'] = pd.NA
                        output_rows_collector = []
                        newly_added_skdk_items_list = []

                        for asm_no, group_df in fcr_df.groupby('組立番号', sort=False):
                            current_kishu = group_df['機種区分'].iloc[0] if not group_df.empty and '機種区分' in group_df.columns and pd.notna(
                                group_df['機種区分'].iloc[0]) else None
                            group_processed_item_names = set()

                            for idx, original_row in group_df.iterrows():
                                row_dict = original_row.to_dict()
                                if row_dict.get('項目名') == "【未展開】":
                                    base_data_undeployed = {k: v for k, v in row_dict.items() if k not in [
                                        '項目名', 'カテゴリNo_結合結果']}
                                    target_progress_df = df_sk_prog if current_kishu == 'SK' and not df_sk_prog.empty else (
                                        df_dk_prog if current_kishu == 'DK' and not df_dk_prog.empty else None)

                                    if target_progress_df is not None:
                                        for _, prog_row in target_progress_df.iterrows():
                                            new_expanded_row = {
                                                **base_data_undeployed,
                                                '項目名': prog_row['カテゴリ名'],
                                                'カテゴリNo_結合結果': prog_row['カテゴリNo_'],
                                                '作業者名': None,
                                                '作業チェック': None,
                                                '完了区分': 3
                                            }
                                            output_rows_collector.append(
                                                new_expanded_row)
                                            if pd.notna(new_expanded_row['項目名']):
                                                group_processed_item_names.add(
                                                    new_expanded_row['項目名'])
                                    else:
                                        output_rows_collector.append(row_dict)
                                        if pd.notna(row_dict.get('項目名')):
                                            group_processed_item_names.add(
                                                row_dict.get('項目名'))
                                else:
                                    item_name = row_dict.get('項目名')
                                    mapped_value = pd.NA
                                    if item_name == '最終ﾁｪｯｸ_検印':
                                        mapped_value = 98
                                    elif item_name == '最終承認':
                                        mapped_value = 99
                                    elif current_kishu == 'SK' and not df_sk_prog.empty and pd.notna(item_name) and 'カテゴリ名' in df_sk_prog.columns:
                                        sk_map = df_sk_prog.set_index('カテゴリ名')[
                                            'カテゴリNo_']
                                        mapped_value = sk_map.get(
                                            item_name, pd.NA)
                                    elif current_kishu == 'DK' and not df_dk_prog.empty and pd.notna(item_name) and 'カテゴリ名' in df_dk_prog.columns:
                                        dk_map = df_dk_prog.set_index('カテゴリ名')[
                                            'カテゴリNo_']
                                        mapped_value = dk_map.get(
                                            item_name, pd.NA)
                                    row_dict['カテゴリNo_結合結果'] = mapped_value
                                    output_rows_collector.append(row_dict)
                                    if pd.notna(item_name):
                                        group_processed_item_names.add(
                                            item_name)

                            target_progress_df_add = df_sk_prog if current_kishu == 'SK' and not df_sk_prog.empty else (
                                df_dk_prog if current_kishu == 'DK' and not df_dk_prog.empty else None)
                            if target_progress_df_add is not None and 'カテゴリ名' in target_progress_df_add.columns:
                                base_info_add = {}
                                if not group_df.empty:
                                    first_row = group_df.iloc[0]
                                    for col in ['組立番号', '機種区分']:
                                        if col in first_row.index:
                                            base_info_add[col] = first_row[col]

                                if '組立番号' in base_info_add:
                                    for _, prog_add_row in target_progress_df_add.iterrows():
                                        if prog_add_row['カテゴリ名'] not in group_processed_item_names and prog_add_row['カテゴリ名'] not in ['最終承認', '最終ﾁｪｯｸ_検印']:
                                            new_added_row = {
                                                **base_info_add,
                                                '項目名': prog_add_row['カテゴリ名'],
                                                '作業者名': None,
                                                '作業チェック': None,
                                                'カテゴリNo_結合結果': prog_add_row['カテゴリNo_'],
                                                '完了区分': 3 if len(group_processed_item_names) > 2 else 0
                                            }
                                            newly_added_skdk_items_list.append(
                                                new_added_row)

                        if output_rows_collector or newly_added_skdk_items_list:
                            df_main = pd.DataFrame(
                                output_rows_collector) if output_rows_collector else pd.DataFrame()
                            df_appended = pd.DataFrame(
                                newly_added_skdk_items_list) if newly_added_skdk_items_list else pd.DataFrame()
                            fcr_df = pd.concat(
                                [df_main, df_appended], ignore_index=True)

                            column_order = ['組立番号', '項目名', '作業者名',
                                            '作業チェック', '完了区分', '機種区分', 'カテゴリNo_結合結果']
                            fcr_df = fcr_df.reindex(columns=column_order)
                            if 'カテゴリNo_結合結果' in fcr_df.columns:
                                fcr_df.dropna(
                                    subset=['カテゴリNo_結合結果'], inplace=True)

                            if not fcr_df.empty:
                                if 'カテゴリNo_結合結果' in fcr_df.columns:
                                    fcr_df['カテゴリNo_結合結果_num'] = pd.to_numeric(
                                        fcr_df['カテゴリNo_結合結果'], errors='coerce')

                                def aggregate_items(x):
                                    if '最終ﾁｪｯｸ_検印' in x['項目名'].values:
                                        final_check_row = x[x['項目名']
                                                            == '最終ﾁｪｯｸ_検印'].iloc[0]
                                        d = {'項目名_集約': '最終ﾁｪｯｸ_検印',
                                             '完了区分': final_check_row['完了区分'],
                                             'カテゴリNo_結合結果_num_for_sort': final_check_row['カテゴリNo_結合結果_num']}
                                    elif '最終承認' in x['項目名'].values:
                                        final_approval_row = x[x['項目名']
                                                               == '最終承認'].iloc[0]
                                        d = {'項目名_集約': '最終承認',
                                             '完了区分': final_approval_row['完了区分'],
                                             'カテゴリNo_結合結果_num_for_sort': final_approval_row['カテゴリNo_結合結果_num']}
                                    else:
                                        names = sorted(list(x['項目名'].dropna().astype(str).str.replace(
                                            '【', '', regex=False).str.replace('】', '', regex=False).unique()))
                                        d = {}
                                        d['項目名_集約'] = "/".join(
                                            names) if names else None
                                        valid_completions = x['完了区分'].dropna()
                                        d['完了区分'] = valid_completions.iloc[0] if not valid_completions.empty else 0
                                        d['カテゴリNo_結合結果_num_for_sort'] = x['カテゴリNo_結合結果_num'].iloc[
                                            0] if not x['カテゴリNo_結合結果_num'].empty else np.nan
                                    return pd.Series(d)

                                if '項目名' in fcr_df.columns and '完了区分' in fcr_df.columns:
                                    fcr_df_for_pivot = fcr_df.dropna(
                                        subset=['カテゴリNo_結合結果_num'])
                                    pivot_prep_df = pd.DataFrame()
                                    if not fcr_df_for_pivot.empty:
                                        pivot_prep_df = fcr_df_for_pivot.groupby(
                                            ['組立番号', 'カテゴリNo_結合結果_num'], as_index=False, sort=False).apply(aggregate_items).reset_index(drop=True)

                                    final_ordered_columns = []
                                    if not pivot_prep_df.empty and '項目名_集約' in pivot_prep_df.columns:
                                        if 'カテゴリNo_結合結果_num_for_sort' in pivot_prep_df.columns:
                                            sorted_items_from_data = pivot_prep_df.dropna(
                                                subset=[
                                                    'カテゴリNo_結合結果_num_for_sort']
                                            ).sort_values(
                                                by='カテゴリNo_結合結果_num_for_sort'
                                            )['項目名_集約'].dropna().unique().tolist()
                                            final_ordered_columns = [
                                                item for item in sorted_items_from_data if item not in ['最終承認', '最終ﾁｪｯｸ_検印']]
                                            if '最終ﾁｪｯｸ_検印' in sorted_items_from_data:
                                                final_ordered_columns.append(
                                                    '最終ﾁｪｯｸ_検印')
                                            if '最終承認' in sorted_items_from_data:
                                                final_ordered_columns.append(
                                                    '最終承認')
                                        else:
                                            unique_items_in_data = pivot_prep_df['項目名_集約'].dropna(
                                            ).unique().tolist()
                                            final_ordered_columns = [
                                                item for item in unique_items_in_data if item not in ['最終承認', '最終ﾁｪｯｸ_検印']]
                                            if '最終ﾁｪｯｸ_検印' in unique_items_in_data:
                                                final_ordered_columns.append(
                                                    '最終ﾁｪｯｸ_検印')
                                            if '最終承認' in unique_items_in_data:
                                                final_ordered_columns.append(
                                                    '最終承認')
                                    else:
                                        if '最終ﾁｪｯｸ_検印' in pivot_prep_df.columns:
                                            final_ordered_columns.append(
                                                '最終ﾁｪｯｸ_検印')
                                        if '最終承認' in pivot_prep_df.columns:
                                            final_ordered_columns.append(
                                                '最終承認')

                                    if '組立番号' in pivot_prep_df.columns and '項目名_集約' in pivot_prep_df.columns and '完了区分' in pivot_prep_df.columns:
                                        try:
                                            display_df = pivot_prep_df.pivot_table(
                                                index='組立番号', columns='項目名_集約', values='完了区分')
                                            if not display_df.empty:
                                                display_df = display_df.reindex(
                                                    columns=final_ordered_columns)
                                            else:
                                                unique_assy_numbers = pivot_prep_df['組立番号'].unique(
                                                ) if '組立番号' in pivot_prep_df else []
                                                if len(unique_assy_numbers) > 0:
                                                    display_df = pd.DataFrame(
                                                        index=unique_assy_numbers, columns=final_ordered_columns)
                                                else:
                                                    display_df = pd.DataFrame(
                                                        columns=final_ordered_columns)
                                            for col_name_fill in display_df.columns:
                                                if col_name_fill in ['最終承認', '最終ﾁｪｯｸ_検印']:
                                                    display_df[col_name_fill] = display_df[col_name_fill].fillna(
                                                        0)
                                                else:
                                                    display_df[col_name_fill] = display_df[col_name_fill].fillna(
                                                        3)
                                        except Exception as e_pivot:
                                            st.error(
                                                f"ピボットテーブル作成中にエラー: {e_pivot}")
                                            display_df = pd.DataFrame()
                                    else:
                                        display_df = pd.DataFrame()
                                else:
                                    display_df = pd.DataFrame()
                            else:
                                if not fcr_df.empty:
                                    fcr_df.sort_values(
                                        by=['組立番号'], inplace=True, na_position='last')
                                display_df = pd.DataFrame()
                        else:
                            display_df = pd.DataFrame()

                        if not fcr_df.empty:
                            fcr_df.reset_index(drop=True, inplace=True)
                            fcr_df.drop_duplicates(
                                subset=['組立番号', '機種区分', '項目名'], keep='first', inplace=True)
                            fcr_df.reset_index(drop=True, inplace=True)
                    else:
                        fcr_df = pd.DataFrame(columns=fcr_df.columns if not fcr_df.empty else [
                            '組立番号', '項目名', '作業者名', '作業チェック', '完了区分', '機種区分', 'カテゴリNo_結合結果'])
                        display_df = pd.DataFrame()

                    # ここからヒートマップ
                    if not display_df.empty:
                        dt_now_heatmap = datetime.now(
                            timezone(timedelta(hours=9)))
                        current_ji_display = '全次'
                        if order_ui and order_ui.strip():
                            try:
                                current_ji_display = f"{int(order_ui)}次"
                            except ValueError:
                                current_ji_display = f"{order_ui}次"

                        additional_filter_text = ""
                        if additional_filter_type_selected == 'previous_next_order':
                            additional_filter_text = " (前後1次)"
                        elif additional_filter_type_selected == 'final_check_incomplete':
                            additional_filter_text = " (最終ﾁｪｯｸ未完了)"
                        elif additional_filter_type_selected == 'final_approval_incomplete':
                            additional_filter_text = " (最終承認未完了)"

                        heatmap_title = f'{sel_y}年{sel_m}月{current_ji_display}{additional_filter_text}　最終更新時：{dt_now_heatmap.strftime("%Y年%m月%d日 %H時%M分")}'
                        df_heatmap_colored = display_df.copy()
                        z_values_processed = []
                        y_labels_heatmap = df_heatmap_colored.index.tolist()

                        for i, kumitate_no in enumerate(y_labels_heatmap):
                            row_values = df_heatmap_colored.loc[kumitate_no].values
                            is_odd_row = (i % 2 == 0)
                            processed_row = []
                            for idx_col, val in enumerate(row_values):
                                if pd.isna(val):
                                    processed_val = 3.0
                                else:
                                    processed_val = float(val)
                                if processed_val == 2.0:
                                    processed_val = 4.0

                                if not is_odd_row:
                                    if processed_val == 1.0:
                                        processed_val = 1.8
                                    elif processed_val == 3.0:
                                        processed_val = 3.8
                                    elif processed_val == 0.0:
                                        processed_val = 0.8
                                    elif processed_val == 4.0:
                                        processed_val = 4.8
                                processed_row.append(processed_val)
                            z_values_processed.append(processed_row)

                        z_data_for_heatmap = np.array(z_values_processed)
                        x_labels_heatmap = df_heatmap_colored.columns.tolist()
                        z_max_val = 4.8
                        color_map_strict = {
                            0.0: '#F7FbFF', 0.8: '#EBF5FF', 1.0: '#09306B', 1.8: '#072A5F',
                            3.0: '#898989', 3.8: '#7e837f', 4.0: '#F4D800', 4.8: '#EEDD00',
                        }
                        colorscale_heatmap_discrete = []
                        sorted_keys = sorted(color_map_strict.keys())
                        for idx, key_val in enumerate(sorted_keys):
                            colorscale_heatmap_discrete.append(
                                [key_val / z_max_val, color_map_strict[key_val]])
                            if idx + 1 < len(sorted_keys):
                                next_key_val = sorted_keys[idx+1]
                                colorscale_heatmap_discrete.append(
                                    [(next_key_val - 0.01) / z_max_val, color_map_strict[key_val]])
                            elif key_val < z_max_val:
                                colorscale_heatmap_discrete.append(
                                    [1.0, color_map_strict[key_val]])

                        num_A_labels = len(y_labels_heatmap)
                        num_B_labels = len(x_labels_heatmap)

                        def insert_linebreak(text, max_chars_per_line=9):
                            if not isinstance(text, str):
                                return text
                            parts = []
                            current_pos = 0
                            while current_pos < len(text):
                                parts.append(
                                    text[current_pos: current_pos + max_chars_per_line])
                                current_pos += max_chars_per_line
                            return "<br>".join(parts)

                        y_labels_for_display_y_axis_when_vertical = [insert_linebreak(
                            label, 9) for label in df_heatmap_colored.columns.tolist()]

                        if muki == '横':
                            y_labels_display = y_labels_heatmap[::-1]
                            z_values_display = z_data_for_heatmap[::-1, :]
                            x_labels_display = x_labels_heatmap
                            current_xgap, current_ygap = 4, 0
                            hover_template = '組立番号: %{y}<br>項目: %{x}<br>状態値: %{z:.1f}<extra></extra>'
                            heatmap_height = num_A_labels * 28 + 200
                            heatmap_width = num_B_labels * 1000
                        else:
                            y_labels_display = y_labels_for_display_y_axis_when_vertical
                            x_labels_display = y_labels_heatmap
                            z_values_display = z_data_for_heatmap.T
                            current_xgap, current_ygap = 0, 4
                            hover_template = '組立番号: %{x}<br>項目: %{y}<br>状態値: %{z:.1f}<extra></extra>'
                            heatmap_height = num_B_labels * 26 + 200
                            heatmap_width = num_A_labels * 1000

                        fig_heatmap = go.Figure(data=go.Heatmap(
                            z=z_values_display, x=x_labels_display, y=y_labels_display,
                            colorscale=colorscale_heatmap_discrete, showscale=False,
                            zmin=0, zmax=z_max_val, xgap=current_xgap, ygap=current_ygap,
                            hovertemplate=hover_template
                        ))
                        if muki == '横':
                            fig_heatmap.update_layout(
                                title=heatmap_title,
                                autosize=False,
                                height=heatmap_height,
                                width=heatmap_width,
                                xaxis_tickfont_size=10,
                                xaxis_showgrid=False,
                                yaxis_showgrid=False#, margin=dict(l=0, r=0, t=30, b=0)
                            )
                        else:
                            #レイアウト調整
                            if num_A_labels > 85:
                                fig_heatmap.update_layout(
                                    title=heatmap_title,
                                    autosize=False,
                                    height=heatmap_height,
                                    width=heatmap_width,
                                    xaxis_tickfont_size=10,
                                    xaxis_showgrid=False,
                                    yaxis_showgrid=False#, margin=dict(l=0, r=0, t=30, b=0)
                                )
                                fig_heatmap.update_xaxes(tickangle=90)
                            else:
                                fig_heatmap.update_layout(
                                    title=heatmap_title,
                                    autosize=False,
                                    height=heatmap_height,
                                    width=heatmap_width,
                                    xaxis_showgrid=False,
                                    yaxis_showgrid=False#, margin=dict(l=0, r=0, t=30, b=0)
                                )

                        
                        st.plotly_chart(fig_heatmap, use_container_width=True)
                        st.write('※５分に１度自動更新')
                    elif not fcr_df.empty:
                        st.warning(
                            "表示に必要なデータが作成できませんでした。加工後データを表示します。")
                        st.dataframe(fcr_df)
                    else:
                        st.info("指定された条件に一致する表示可能なデータがありません。")
                else:
                    st.info("データがありません")
            else:
                st.error("DB接続エラー。処理を実行できません。")
        time.sleep(300)


if __name__ == "__main__":
    main()
