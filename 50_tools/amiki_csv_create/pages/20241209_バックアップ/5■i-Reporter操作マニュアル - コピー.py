import streamlit as st
import os
import streamlit.components.v1 as components


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
        st.markdown(HIDE_ST_STYLE, unsafe_allow_html=True)

        with open(os.getcwd()+r'/static/i-Reporter/i-Reporterマニュアル.html', "r", encoding="utf-8") as f:
            html_content = f.read()

        # 画像パス置き換え
        html_content = html_content.replace(r'background-image:url(&quot;%E6%9D%90%E6%96%99/common.png&quot;)',
                                            r'background-image:url(&quot;app/static/i-Reporter/%E6%9D%90%E6%96%99/common.png&quot;)')
        html_content = html_content.replace(
            r'<img src="', r'<img src="app/static/i-Reporter/')

        # HTML表示
        components.html(html_content, height=400, scrolling=True)

    except Exception as e:
        # 簡単なエラー処理を追加
        st.subheader(e)


if __name__ == "__main__":
    main()
