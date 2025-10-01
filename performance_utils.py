"""
Streamlit性能优化配置模块
包含各种性能优化的辅助函数和配置
"""

import time
from typing import List, Tuple

import pandas as pd
import psutil
import streamlit as st


class PerformanceMonitor:
    """性能监控类"""

    def __init__(self):
        self.start_time = time.time()
        self.memory_start = psutil.Process().memory_info().rss / 1024 / 1024  # MB

    def log_performance(self, operation_name: str):
        """记录操作性能"""
        current_time = time.time()
        current_memory = psutil.Process().memory_info().rss / 1024 / 1024

        elapsed_time = current_time - self.start_time
        memory_used = current_memory - self.memory_start

        if st.sidebar.checkbox("Show Performance Metrics", value=False):
            st.sidebar.metric(f"{operation_name} - Time", f"{elapsed_time:.2f}s")
            st.sidebar.metric(f"{operation_name} - Memory", f"{memory_used:.1f}MB")


def setup_streamlit_config():
    """优化Streamlit配置"""
    # 设置页面配置（必须在第一个streamlit命令之前）
    if "page_config_set" not in st.session_state:
        st.set_page_config(
            page_title="Euraxess Jobs",
            page_icon="🎓",
            layout="wide",
            initial_sidebar_state="expanded",
            menu_items={"Get Help": None, "Report a bug": None, "About": "Euraxess Job Listings Dashboard - Optimized Version"},
        )
        st.session_state.page_config_set = True


@st.cache_resource
def get_memory_usage():
    """获取内存使用情况"""
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024  # MB


def optimize_dataframe_display(df: pd.DataFrame, max_rows: int = 1000) -> pd.DataFrame:
    """优化DataFrame显示性能"""
    if len(df) > max_rows:
        st.warning(f"⚠️ Large dataset detected ({len(df)} rows). Showing first {max_rows} rows for better performance.")
        return df.head(max_rows)
    return df


def create_pagination(df: pd.DataFrame, page_size: int = 50) -> Tuple[pd.DataFrame, int, int]:
    """创建分页功能"""
    total_rows = len(df)
    total_pages = (total_rows + page_size - 1) // page_size

    if total_pages > 1:
        page = st.selectbox("Page", options=range(1, total_pages + 1), format_func=lambda x: f"Page {x} of {total_pages}")
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        return df.iloc[start_idx:end_idx], page, total_pages
    else:
        return df, 1, 1


@st.cache_data(ttl=1800)  # 30分钟缓存
def load_csv_optimized(file_path: str) -> pd.DataFrame:
    """优化的CSV加载函数"""
    try:
        # 使用更高效的读取参数
        df = pd.read_csv(
            file_path,
            encoding="utf-8",
            low_memory=False,
            parse_dates=["posted_on"],  # 直接解析日期
            date_parser=pd.to_datetime,
            engine="c",  # 使用C引擎提升性能
        )
        return df
    except Exception as e:
        st.error(f"Error loading CSV: {str(e)}")
        return pd.DataFrame()


def setup_css_optimizations():
    """设置CSS优化"""
    st.markdown(
        """
    <style>
    /* 优化加载样式 */
    .stApp > div:first-child > div:first-child > div:first-child {
        padding-top: 1rem;
    }
    
    /* 优化侧边栏 */
    .css-1d391kg {
        padding-top: 1rem;
    }
    
    /* 优化数据表格显示 */
    .stDataFrame {
        font-size: 12px;
    }
    
    /* 减少不必要的动画 */
    .css-1offfwp {
        transition: none !important;
    }
    
    /* 优化加载指示器 */
    .stSpinner > div {
        border-top-color: #FF6B6B;
    }
    
    /* 隐藏Streamlit标识以提升加载速度 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """,
        unsafe_allow_html=True,
    )


class DataCache:
    """数据缓存管理器"""

    @staticmethod
    @st.cache_data
    def get_unique_values(series: pd.Series, sort: bool = True) -> List[str]:
        """获取唯一值并缓存"""
        unique_vals = series.dropna().unique().tolist()
        if sort:
            return sorted(unique_vals, key=lambda x: x.lower() if isinstance(x, str) else str(x).lower())
        return unique_vals

    @staticmethod
    @st.cache_data
    def filter_options_by_search(options: List[str], search_term: str) -> List[str]:
        """根据搜索词过滤选项"""
        if not search_term:
            return options
        search_lower = search_term.lower()
        return [opt for opt in options if search_lower in opt.lower()]


def show_data_statistics(df: pd.DataFrame):
    """显示数据统计信息"""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Jobs", f"{len(df):,}", delta=None)

    with col2:
        countries = df["country"].nunique()
        st.metric("Countries", countries, delta=None)

    with col3:
        universities = df["university"].nunique()
        st.metric("Universities", universities, delta=None)

    with col4:
        if "posted_on" in df.columns:
            recent_jobs = len(df[df["posted_on"] >= (pd.Timestamp.now() - pd.Timedelta(days=7))])
            st.metric("New This Week", recent_jobs, delta=None)
        else:
            st.metric("Data Status", "✅ Loaded", delta=None)


def create_advanced_filters(df: pd.DataFrame) -> dict:
    """创建高级过滤器"""
    filters = {}

    with st.expander("🔧 Advanced Filters", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            # 日期范围过滤
            if "posted_on" in df.columns:
                date_range = st.date_input("Posted Date Range", value=(), key="date_range")
                if len(date_range) == 2:
                    filters["date_range"] = date_range

            # 申请截止日期过滤
            if "application_deadline" in df.columns:
                deadline_filter = st.selectbox(
                    "Application Deadline", ["All", "Within 1 month", "Within 3 months", "No deadline"], key="deadline_filter"
                )
                filters["deadline_filter"] = deadline_filter

        with col2:
            # 文字搜索
            search_term = st.text_input("Search in titles and descriptions", placeholder="Enter keywords...", key="search_term")
            if search_term:
                filters["search_term"] = search_term

            # 资金计划过滤
            if "funding_program" in df.columns:
                funding_options = DataCache.get_unique_values(df["funding_program"])
                selected_funding = st.multiselect("Funding Program", options=funding_options, key="funding_filter")
                if selected_funding:
                    filters["funding_programs"] = selected_funding

    return filters
