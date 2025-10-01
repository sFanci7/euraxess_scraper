import json
import os
from typing import Set

import pandas as pd
import streamlit as st
from dateutil import parser

# Configure Streamlit page - must be first Streamlit command
st.set_page_config(
    page_title="Euraxess Data",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "Euraxess Job Listings Dashboard with Favorites"},
)

# 收藏功能相关的函数
FAVORITES_FILE = "favorites.json"


@st.cache_data
def load_favorites() -> Set[str]:
    """Load the list of favorite job IDs"""
    try:
        if os.path.exists(FAVORITES_FILE):
            with open(FAVORITES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return set(data.get("favorites", []))
    except Exception:
        pass
    return set()


def save_favorites(favorites: Set[str]) -> None:
    """Save the list of favorite job IDs"""
    try:
        data = {"favorites": list(favorites)}
        with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        # Clear cache to ensure data updates
        load_favorites.clear()
    except Exception as e:
        st.error(f"Failed to save favorites: {str(e)}")


def toggle_favorite(job_id: str) -> None:
    """Toggle favorite status"""
    favorites = load_favorites()
    if job_id in favorites:
        favorites.remove(job_id)
        st.success(f"Removed job {job_id} from favorites")
    else:
        favorites.add(job_id)
        st.success(f"Added job {job_id} to favorites")
    save_favorites(favorites)


@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_and_process_data():
    """Load and preprocess the CSV data with caching."""
    try:
        # Load the CSV file
        df = pd.read_csv("output/jobs.csv")

        # Clean the 'posted_on' column
        df["posted_on"] = df["posted_on"].str.replace("Posted on: ", "")
        df["posted_on"] = pd.to_datetime(df["posted_on"], errors="coerce")

        # Create boolean columns for each profile (optimized to avoid fragmentation)
        profile_patterns = ["R1", "R2", "R3", "R4"]
        profile_columns = {pattern: df["profile"].str.contains(pattern, case=False, na=False) for pattern in profile_patterns}
        profile_df = pd.DataFrame(profile_columns, index=df.index)
        df = pd.concat([df, profile_df], axis=1)

        # Apply the extraction function to the 'field' column
        field_results = df["field"].apply(extract_relevant_items)
        df["field_1"], df["field_2"] = zip(*field_results)

        # Convert 'application_deadline' to datetime (vectorized)
        df["application_deadline"] = df["application_deadline"].apply(lambda x: parser.parse(x.split("(")[0].strip()) if pd.notnull(x) else None)

        # Filter out rows where 'application_deadline' is in the past
        current_time = pd.Timestamp.now()
        df = df[df["application_deadline"].isna() | (df["application_deadline"] >= current_time)]

        return df
    except FileNotFoundError:
        st.error("❌ jobs.csv file not found in output directory. Please run the scraper first.")
        st.stop()
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        st.stop()


@st.cache_data
def extract_relevant_items(s):
    """Extract relevant items from the 'field' column with caching."""
    try:
        items = [item.strip() for item in s.split(";")]
    except Exception:
        return None, None

    class_1 = []
    class_2 = []
    for i in range(len(items)):
        curr = items[i]
        prev = items[i - 1] if i > 0 else ""
        next_item = items[i + 1] if i < len(items) - 1 else ""

        if next_item == "»":
            class_1.append(curr)
        elif prev == "»":
            class_2.append(curr)
        elif prev != "»" and next_item != "»" and curr != "»":
            class_1.append(curr)

    return ",".join(set(class_1)), ",".join(set(class_2))


@st.cache_data
def prepare_filter_options(df):
    """Prepare filter options with caching."""
    # Create lists of unique fields and countries (optimized)
    all_main_fields = []
    all_sub_fields = []

    # Use vectorized operations where possible
    field_1_values = df["field_1"].dropna()
    field_2_values = df["field_2"].dropna()

    for field_str in field_1_values:
        if field_str:
            all_main_fields.extend(field_str.split(","))

    for field_str in field_2_values:
        if field_str:
            all_sub_fields.extend(field_str.split(","))

    all_main_fields = sorted(set(all_main_fields), key=lambda x: x.lower())
    all_sub_fields = sorted(set(all_sub_fields), key=lambda x: x.lower())

    # Create boolean columns for each unique field (optimized to avoid fragmentation)
    # Create all main field columns at once
    main_field_columns = {}
    for field in all_main_fields:
        if field not in df.columns:
            main_field_columns[field] = df["field_1"].str.contains(field, case=False, na=False)

    # Create all sub field columns at once
    sub_field_columns = {}
    for field in all_sub_fields:
        if field not in df.columns:
            sub_field_columns[field] = df["field_2"].str.contains(field, case=False, na=False)

    # Concatenate all new columns at once to avoid fragmentation
    if main_field_columns or sub_field_columns:
        all_new_columns = {**main_field_columns, **sub_field_columns}
        new_df = pd.DataFrame(all_new_columns, index=df.index)
        df = pd.concat([df, new_df], axis=1)

    # Get unique countries
    all_countries = sorted(df["country"].dropna().unique().tolist(), key=lambda x: x.lower())
    all_profiles = ["R1", "R2", "R3", "R4"]

    return df, all_countries, all_profiles, all_main_fields, all_sub_fields


@st.cache_data
def filter_dataframe(df, selected_countries, selected_profiles, selected_fields, selected_sub_fields, show_favorites_only=False):
    """Filter dataframe with caching."""
    df_filtered = df.copy()

    # Favorites filtering
    if show_favorites_only:
        favorites = load_favorites()
        df_filtered = df_filtered[df_filtered["id"].astype(str).isin(favorites)]

    if selected_countries:
        df_filtered = df_filtered[df_filtered["country"].isin(selected_countries)]

    if selected_profiles:
        df_filtered = df_filtered[df_filtered[selected_profiles].any(axis=1)]

    if selected_fields:
        df_filtered = df_filtered[df_filtered[selected_fields].any(axis=1)]

    if selected_sub_fields:
        df_filtered = df_filtered[df_filtered[selected_sub_fields].any(axis=1)]

    return df_filtered


def create_favorite_button(job_id: str, favorites: Set[str]) -> None:
    """Create favorite button"""
    is_favorited = str(job_id) in favorites

    if is_favorited:
        button_text = "💖 Favorited"
        button_type = "secondary"
    else:
        button_text = "🤍 Favorite"
        button_type = "primary"

    if st.button(button_text, key=f"fav_{job_id}", type=button_type, use_container_width=True):
        toggle_favorite(str(job_id))
        st.rerun()


def display_job_table_with_favorites(df_filtered: pd.DataFrame) -> None:
    """Display job table with favorites functionality"""
    favorites = load_favorites()

    # Prepare display columns
    show_columns = [
        "country",
        "university",
        "title",
        "link",
        "application_deadline",
        "posted_on",
        "description",
        "department",
        "location",
        "funding_program",
        "type",
        "profile",
        "field_1",
    ]

    # Add favorite status column
    df_display = df_filtered[show_columns].copy()
    df_display["is_favorite"] = df_filtered["id"].astype(str).isin(favorites)

    # Reorder columns with favorite status first
    columns_reordered = ["is_favorite"] + show_columns

    # Column configuration
    column_config = {
        "is_favorite": st.column_config.CheckboxColumn("Favorite", help="Whether this job is favorited", default=False, width="small"),
        "country": st.column_config.TextColumn("Country", width="small"),
        "title": st.column_config.TextColumn("Title", width="medium"),
        "university": st.column_config.TextColumn("University", width="medium"),
        "link": st.column_config.LinkColumn("Link", display_text="View Details"),
        "application_deadline": st.column_config.DateColumn("Deadline"),
        "posted_on": st.column_config.DateColumn("Posted"),
        "description": st.column_config.TextColumn("Description", width="large"),
    }

    # Display data table
    edited_df = st.data_editor(
        df_display[columns_reordered],
        use_container_width=True,
        height=500,
        column_config=column_config,
        hide_index=True,
        disabled=show_columns,  # Only allow editing favorite status
        key="job_table",
    )

    # Check for favorite status changes
    if edited_df is not None:
        # Compare original and edited favorite status
        original_favorites = df_display["is_favorite"]
        new_favorites = edited_df["is_favorite"]

        changed_indices = original_favorites != new_favorites
        if changed_indices.any():
            # Update favorite status
            current_favorites = load_favorites()

            for idx in df_filtered.index[changed_indices]:
                job_id = str(df_filtered.loc[idx, "id"])
                new_status = new_favorites[changed_indices].iloc[0] if changed_indices.sum() == 1 else new_favorites.loc[idx]

                if new_status and job_id not in current_favorites:
                    current_favorites.add(job_id)
                elif not new_status and job_id in current_favorites:
                    current_favorites.remove(job_id)

            save_favorites(current_favorites)
            st.rerun()


# Main app logic
def main():
    # Add loading spinner for data loading
    with st.spinner("Loading data..."):
        df = load_and_process_data()
        df, all_countries, all_profiles, all_main_fields, all_sub_fields = prepare_filter_options(df)

    # Load favorites data
    favorites = load_favorites()

    # Sidebar for filters with improved UI
    with st.sidebar:
        st.header("🔍 Filters")

        # Favorites filter option
        show_favorites_only = st.checkbox("🌟 Show only favorite jobs", value=False)

        if show_favorites_only and len(favorites) == 0:
            st.warning("You haven't favorited any jobs yet")

        st.divider()

        # Add search functionality for countries
        country_search = st.text_input("Search Countries", placeholder="Type to filter countries...")
        filtered_countries = [c for c in all_countries if country_search.lower() in c.lower()] if country_search else all_countries
        selected_countries = st.multiselect("Country", options=filtered_countries, key="countries")

        selected_profiles = st.multiselect("Profile", options=all_profiles, key="profiles")

        # Add search for fields
        field_search = st.text_input("Search Fields", placeholder="Type to filter fields...")
        filtered_fields = [f for f in all_main_fields if field_search.lower() in f.lower()] if field_search else all_main_fields
        selected_fields = st.multiselect("Field", options=filtered_fields, key="fields")

        # Add search for sub-fields
        subfield_search = st.text_input("Search Sub-fields", placeholder="Type to filter sub-fields...")
        filtered_sub_fields = [f for f in all_sub_fields if subfield_search.lower() in f.lower()] if subfield_search else all_sub_fields
        selected_sub_fields = st.multiselect("Sub-field", options=filtered_sub_fields, key="sub_fields")

        # Add clear all button
        if st.button("Clear All Filters", type="secondary"):
            st.rerun()

        st.divider()

        # Favorites statistics
        st.subheader("📚 Favorites Stats")
        st.metric("Total Favorites", len(favorites))

        if len(favorites) > 0:
            # Clear all favorites button
            if st.button("🗑️ Clear All Favorites", type="secondary"):
                save_favorites(set())
                st.success("All favorites cleared")
                st.rerun()

    # Main content area
    st.title("🎓 Euraxess Job Listings")

    # Add statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Jobs", len(df))
    with col2:
        st.metric("Countries", df["country"].nunique())
    with col3:
        st.metric("Universities", df["university"].nunique())
    with col4:
        recent_jobs = len(df[df["posted_on"] >= (pd.Timestamp.now() - pd.Timedelta(days=7))])
        st.metric("New This Week", recent_jobs)

    # Filter data with caching
    df_filtered = filter_dataframe(df, selected_countries, selected_profiles, selected_fields, selected_sub_fields, show_favorites_only)

    # Display results
    result_title = "🌟 Favorite Jobs" if show_favorites_only else "📊 All Jobs"
    st.subheader(f"{result_title} ({len(df_filtered)} jobs)")

    if len(df_filtered) == 0:
        if show_favorites_only:
            st.info("No favorite jobs match the current filter criteria. Try adjusting your filters or favorite some jobs.")
        else:
            st.warning("No jobs match the current filter criteria. Please adjust your filters.")
        return

    # Display table with favorites functionality
    display_job_table_with_favorites(df_filtered)


if __name__ == "__main__":
    main()
