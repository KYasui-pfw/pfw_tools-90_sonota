import streamlit as st
import os


def main():

    try:
        st.set_page_config(
            page_title='iReporterチェックシート_マニュアル',
            layout="wide"
        )

        HIDE_ST_STYLE = """
                    <style>
                    div[data-testid="stToolbar"] {
                    visibility: hidden;
                    height: 0%;
                    position: fixed;
                    }
                    div[data-testid="stDecoration"] {
                    visibility: hidden;
                    height: 0%;
                    position: fixed;
                    }
                    #MainMenu {
                    visibility: hidden;
                    height: 0%;
                    }
                    header {
                    visibility: hidden;
                    height: 0%;
                    }
                    footer {
                    visibility: hidden;
                    height: 0%;
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
    """
        st.markdown(
            # プリント機能を使用するため、適用しないようにする⇒しない（タブを使用するため上を狭くしたい）
            HIDE_ST_STYLE, unsafe_allow_html=True)
        # タブを作成
        tab_titles = ['i-Reporter操作マニュアル　', '測定者マニュアル　',
                      '管理者マニュアル　']
        tab1, tab2, tab3 = st.tabs(tab_titles)

        with tab1:
            st.markdown('''
                        # i-Reporter操作マニュアル  
                        当ページはi-Reporterの操作に関するマニュアルページです。  
                        
                        ---
                        ''')

            st.write('※旧マニュアルは以下に格納されています')
            st.write('ファイルリンクは出来ないので、アドレスバーにコピーしてご利用ください')
            st.write(
                'file://esrv10/PFW-iR/加工チェックシート/990_操作マニュアル/01_共通/00_マニュアル共通ページ/マニュアル共通ページ.html')
        with tab2:

            # マニュアルを開く（今後Streamlitでマニュアルを扱うときの共通処理になる）
            with open(os.getcwd()+r'/static/測定者マニュアル.md', 'r', encoding='utf-8') as f:
                # ファイルの内容を読み取る
                text = f.read()
            text = text.replace(r'](i', r'](app/static/i')
            # text = text.replace(r'](i', r'](static/i')
            st.markdown(text, unsafe_allow_html=True)

        with tab3:

            # マニュアルを開く（今後Streamlitでマニュアルを扱うときの共通処理になる）
            with open(os.getcwd()+r'/static/管理者マニュアル.md', 'r', encoding='utf-8') as f:
                # ファイルの内容を読み取る
                text = f.read()
            text = text.replace(r'](i', r'](app/static/i')
            st.markdown(text, unsafe_allow_html=True)

    except Exception as e:
        # 簡単なエラー処理
        st.subheader(e)


if __name__ == "__main__":
    main()
