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
        # st.markdown(HIDE_ST_STYLE, unsafe_allow_html=True) プリント機能を使用するため、適用しないようにする

    # マニュアルを開く（今後Streamlitでマニュアルを扱うときの共通処理になる）
        with open(os.getcwd()+r'/static/マニュアル.md', 'r', encoding='utf-8') as f:
            # ファイルの内容を読み取る
            text = f.read()
        text = text.replace(r'](i', r'](app/static/i')
        # text = text.replace(r'](i', r'](static/i')
        st.markdown(text, unsafe_allow_html=True)

    except Exception as e:
        # 簡単なエラー処理を追加
        st.subheader(e)


if __name__ == "__main__":
    main()
