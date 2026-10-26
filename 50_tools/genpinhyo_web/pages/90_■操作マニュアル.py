import streamlit as st
import os


def main():

    try:

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
        tab_titles = ['現品票発行　', '現品票手入力発行　',
                      'チェックシート再作成　', 'iReporterチェック項目入力　',
                      'iReporter進捗確認　']
        tab1, tab2, tab3, tab4, tab5 = st.tabs(tab_titles)

        with tab1:

            # マニュアルを開く（今後Streamlitでマニュアルを扱うときの共通処理になる）
            with open(os.getcwd()+r'/static/現品票発行マニュアル.md', 'r', encoding='utf-8') as f:
                # ファイルの内容を読み取る
                text = f.read()
            text = text.replace(r'](i', r'](app/static/i')
            st.markdown(text, unsafe_allow_html=True)

        with tab2:

            # マニュアルを開く（今後Streamlitでマニュアルを扱うときの共通処理になる）
            with open(os.getcwd()+r'/static/現品票手入力発行マニュアル.md', 'r', encoding='utf-8') as f:
                # ファイルの内容を読み取る
                text = f.read()
            text = text.replace(r'](i', r'](app/static/i')
            # text = text.replace(r'](i', r'](static/i')
            st.markdown(text, unsafe_allow_html=True)

        with tab3:

            # マニュアルを開く（今後Streamlitでマニュアルを扱うときの共通処理になる）
            with open(os.getcwd()+r'/static/チェックシート再作成マニュアル.md', 'r', encoding='utf-8') as f:
                # ファイルの内容を読み取る
                text = f.read()
            text = text.replace(r'](i', r'](app/static/i')
            st.markdown(text, unsafe_allow_html=True)

        with tab4:

            # マニュアルを開く（今後Streamlitでマニュアルを扱うときの共通処理になる）
            with open(os.getcwd()+r'/static/iReporterチェック項目入力マニュアル.md', 'r', encoding='utf-8') as f:
                # ファイルの内容を読み取る
                text = f.read()
            text = text.replace(r'](i', r'](app/static/i')
            st.markdown(text, unsafe_allow_html=True)

        with tab5:

            # マニュアルを開く（今後Streamlitでマニュアルを扱うときの共通処理になる）
            with open(os.getcwd()+r'/static/iReporter進捗確認マニュアル.md', 'r', encoding='utf-8') as f:
                # ファイルの内容を読み取る
                text = f.read()
            text = text.replace(r'](i', r'](app/static/i')
            st.markdown(text, unsafe_allow_html=True)

    except Exception as e:
        # 簡単なエラー処理
        st.subheader(e)


if __name__ == "__main__":
    main()
