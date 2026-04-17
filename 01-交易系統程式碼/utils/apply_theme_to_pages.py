"""
快速应用主题到所有页面的脚本
"""

THEME_IMPORT = """import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from utils.ui_theme import apply_theme

# 应用主题
apply_theme(st)
"""

THEME_HEADER = """st.markdown('''
<style>
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
        border-right: 1px solid #E5E7EB;
    }}
</style>
''', unsafe_allow_html=True)
"""

if __name__ == "__main__":
    print("🎨 Theme Application Helper")
    print("请手动在每个页面的导入部分添加上述代码")
