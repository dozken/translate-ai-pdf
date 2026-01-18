"""
PDF Translation Cost Calculator App
Main Streamlit application for calculating translation costs.
"""

import streamlit as st
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime
import pdfplumber

from config import config
from constants import PAGE_LAYOUT
from translations import get_translation, LANGUAGES, DEFAULT_LANGUAGE
from utils.pdf_processor import extract_text_from_pdf
from utils.token_calculator import calculate_all_provider_tokens
from utils.cost_calculator import calculate_all_provider_costs
from utils.translator import (
    translate_text_gemini,
    split_into_paragraphs,
    TranslationStoppedException,
)
from utils.pdf_generator import create_pdf_from_text
from utils.logger_config import setup_logging, get_logger
from utils.progress_storage import (
    get_file_id,
    load_progress,
    delete_progress,
    get_translated_text_from_progress,
)

# Configure logging
setup_logging(log_level=config.LOG_LEVEL, log_file=config.LOG_FILE, console_output=True)
logger = get_logger(__name__)

# Initialize language in session state
if "language" not in st.session_state:
    st.session_state.language = DEFAULT_LANGUAGE


# Helper function to get translation
def t(key: str, **kwargs):
    """Shortcut for get_translation with current language"""
    return get_translation(key, st.session_state.language, **kwargs)


# Page configuration
page_title = t("page_title")
page_icon = t("page_icon")
st.set_page_config(
    page_title=page_title, page_icon=page_icon, layout=PAGE_LAYOUT, initial_sidebar_state="expanded"
)

# Custom CSS for modern, clean UI
st.markdown(
    """
<style>
    /* Main container spacing */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    /* Metric cards */
    [data-testid="stMetricValue"] {
        font-size: 1.5rem;
        font-weight: 600;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.9rem;
        opacity: 0.8;
    }
    
    /* Button styling */
    .stButton > button {
        width: 100%;
        border-radius: 0.5rem;
        transition: all 0.2s ease;
        font-weight: 500;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Dataframe styling */
    .dataframe {
        font-size: 0.9rem;
        border-radius: 0.5rem;
    }
    
    /* Streaming text container */
    .streaming-text-container {
        background-color: #0e1117;
        color: #fafafa;
        padding: 1.25rem;
        border-radius: 0.5rem;
        max-height: 300px;
        overflow-y: auto;
        font-family: 'Courier New', monospace;
        white-space: pre-wrap;
        border: 2px solid #4a5568;
        line-height: 1.6;
        font-size: 0.95rem;
    }
    
    /* Remove excessive spacing from dividers */
    hr {
        margin: 1.5rem 0;
    }
    
    /* Sidebar improvements */
    .css-1d391kg {
        padding-top: 2rem;
    }
    
    /* Section headers */
    h3 {
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    
    /* Info boxes */
    .stInfo {
        border-radius: 0.5rem;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Title
st.title(f"{page_icon} {page_title}")
st.markdown(t("upload_prompt"))

# Clean Sidebar
with st.sidebar:
    st.header(f"⚙️ {t('sidebar_settings')}")

    # Language selector
    selected_language = st.selectbox(
        t("select_language"),
        options=list(LANGUAGES.keys()),
        format_func=lambda x: LANGUAGES[x],
        index=list(LANGUAGES.keys()).index(st.session_state.language),
        key="language_selector",
    )
    if selected_language != st.session_state.language:
        st.session_state.language = selected_language
        st.rerun()

    st.divider()

    # Consolidated info section
    st.info(t("sidebar_info"))
    st.caption(t("token_counting_note"))

# Main content area
uploaded_file = st.file_uploader(t("choose_pdf_file"), type=["pdf"], help=t("upload_help"))

if uploaded_file is not None:
    # Get current file identifier using progress storage utility
    filename = uploaded_file.name if hasattr(uploaded_file, "name") else "unknown"
    file_size = uploaded_file.size if hasattr(uploaded_file, "size") else 0
    current_file_id = get_file_id(filename, file_size)

    logger.info(f"File uploaded: filename={filename}, file_id={current_file_id}, size={file_size}")

    # Check if file has changed - if so, reset translation state
    if "current_file_id" not in st.session_state:
        st.session_state.current_file_id = None

    if st.session_state.current_file_id != current_file_id:
        # File has changed - reset all translation-related state
        logger.info(
            f"File changed from {st.session_state.current_file_id} to {current_file_id}, resetting translation state"
        )
        st.session_state.current_file_id = current_file_id
        st.session_state.translation_in_progress = False
        st.session_state.translation_progress = (0, 0)
        st.session_state.translated_text = None
        st.session_state.translation_pdf_path = None
        st.session_state.translation_error = None
        st.session_state.translation_clicked = None
        st.session_state.streaming_text = ""
        st.session_state.streaming_start_time = None
        st.session_state.existing_progress = None
        st.session_state.resume_from_index = 0
        st.session_state.user_chose_resume = None
        st.session_state.translation_stopped = False

    # Check for existing progress
    logger.info(f"Checking for existing progress: file_id={current_file_id}")
    if "existing_progress" not in st.session_state or st.session_state.existing_progress is None:
        st.session_state.existing_progress = load_progress(current_file_id)

    existing_progress = st.session_state.existing_progress

    # Show progress banner if existing progress found
    if existing_progress and st.session_state.user_chose_resume is None:
        completed = existing_progress.get("completed_paragraphs", 0)
        total = existing_progress.get("total_paragraphs", 0)
        percent = (completed / total * 100) if total > 0 else 0
        last_updated = existing_progress.get("updated_at", "unknown")

        logger.info(
            f"Found existing progress: file_id={current_file_id}, "
            f"completed={completed}/{total} ({percent:.1f}%), "
            f"last_updated={last_updated}"
        )

        st.markdown("---")
        with st.container():
            st.markdown(f"### 📊 {t('progress_found')}")

            # Progress info
            progress_cols = st.columns([3, 1])
            with progress_cols[0]:
                st.info(
                    f"**{t('progress_status', completed=completed, total=total, percent=f'{percent:.1f}')}**\n\n"
                    f"*{t('last_updated', timestamp=last_updated)}*"
                )
                st.progress(percent / 100)

            with progress_cols[1]:
                # Action buttons
                if st.button(
                    t("resume_translation"),
                    type="primary",
                    use_container_width=True,
                    key="btn_resume",
                ):
                    st.session_state.user_chose_resume = True
                    st.session_state.resume_from_index = completed
                    logger.info(
                        f"User chose to resume for file_id: {current_file_id}, will continue from paragraph {completed + 1} of {total} (paragraphs 1-{completed} already translated)"
                    )
                    st.rerun()

                if st.button(t("start_fresh"), use_container_width=True, key="btn_start_fresh"):
                    st.session_state.user_chose_resume = False
                    st.session_state.resume_from_index = 0
                    delete_progress(current_file_id, reason="user chose to start fresh")
                    st.session_state.existing_progress = None
                    logger.info(
                        f"User chose to start fresh for file_id: {current_file_id}, deleting old progress and resetting resume index"
                    )
                    st.rerun()

                # Download partial PDF button
                if completed > 0:
                    if st.button(
                        t("download_partial_pdf", completed=completed, total=total),
                        use_container_width=True,
                        key="btn_download_partial",
                    ):
                        # Generate partial PDF
                        try:
                            translated_text = get_translated_text_from_progress(existing_progress)
                            output_dir = config.get_pdf_output_dir()
                            base_name = Path(filename).stem
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            pdf_filename = f"translated_{base_name}_partial_{timestamp}.pdf"
                            pdf_path = str(output_dir / pdf_filename)

                            source_lang = existing_progress.get(
                                "source_lang", config.SOURCE_LANGUAGE
                            )
                            target_lang = existing_progress.get(
                                "target_lang", config.TARGET_LANGUAGE
                            )

                            title = t("partial_pdf_title", completed=completed, total=total)

                            create_pdf_from_text(
                                translated_text,
                                pdf_path,
                                title=title,
                                source_lang=source_lang,
                                target_lang=target_lang,
                                metadata={
                                    "original_filename": filename,
                                    "partial_translation": True,
                                    "completed_paragraphs": completed,
                                    "total_paragraphs": total,
                                    "note": t("partial_pdf_note", completed=completed, total=total),
                                },
                                include_metadata=False,
                            )

                            logger.info(
                                f"Partial PDF generated: file_id={current_file_id}, {completed}/{total} paragraphs, path={pdf_path}"
                            )

                            # Download button
                            with open(pdf_path, "rb") as pdf_file:
                                st.download_button(
                                    label=f"📥 {t('download_pdf')}",
                                    data=pdf_file.read(),
                                    file_name=pdf_filename,
                                    mime="application/pdf",
                                    type="primary",
                                    use_container_width=True,
                                    key="download_partial_pdf_btn",
                                )
                        except Exception as e:
                            logger.error(f"Error generating partial PDF: {e}", exc_info=True)
                            st.error(f"Error generating partial PDF: {e}")

        st.markdown("---")

    # Process PDF
    logger.info(
        f"Processing uploaded PDF: {uploaded_file.name if hasattr(uploaded_file, 'name') else 'unknown'}"
    )
    with st.spinner(t("extracting_text")):
        try:
            extracted_text, metadata = extract_text_from_pdf(uploaded_file)
            logger.info(
                f"PDF extracted successfully: {metadata['page_count']} pages, {metadata['char_count']} chars, {metadata['word_count']} words"
            )

            if not extracted_text:
                logger.warning("No text extracted from PDF")
                st.error(t("no_text_extracted"))
                st.stop()

            # PDF statistics
            st.success(t("pdf_processed"))
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(label=t("pages"), value=metadata["page_count"])
            with col2:
                st.metric(label=t("characters"), value=f"{metadata['char_count']:,}")
            with col3:
                st.metric(label=t("words"), value=f"{metadata['word_count']:,}")

            # Calculate tokens
            logger.debug("Calculating token counts for all providers")
            with st.spinner(t("calculating_tokens")):
                token_counts = calculate_all_provider_tokens(extracted_text)
                logger.info(f"Token calculation completed for {len(token_counts)} providers")

            # Token counts (simplified)
            st.markdown(f"### {t('token_counts_title')}")

            # Group providers by token count (excluding DeepL)
            token_groups = {}
            for provider_key, token_data in token_counts.items():
                if provider_key == "deepl":
                    continue
                token_count = token_data.get("tokens", 0)
                if token_count not in token_groups:
                    token_groups[token_count] = []
                token_groups[token_count].append((provider_key, token_data))

            # Display grouped token counts
            token_data_list = []
            for token_count, providers in sorted(token_groups.items()):
                provider_names = [p[1]["model"] for p in providers]
                all_exact = all(p[1].get("exact", False) for p in providers)
                exact_badge = "✅" if all_exact else "⚠️"
                label = (
                    f"{exact_badge} {provider_names[0]}"
                    if len(providers) == 1
                    else f"{exact_badge} {len(providers)} providers"
                )

                token_data_list.append(
                    {"token_count": token_count, "label": label, "providers": providers}
                )

            # Display in columns
            num_rows = (len(token_data_list) + 2) // 3
            for row_idx in range(num_rows):
                token_cols = st.columns(3)
                start_idx = row_idx * 3
                end_idx = min(start_idx + 3, len(token_data_list))
                for col_idx, group_data in enumerate(token_data_list[start_idx:end_idx]):
                    with token_cols[col_idx]:
                        st.metric(label=group_data["label"], value=f"{group_data['token_count']:,}")

            # Calculate costs
            logger.debug("Calculating costs for all providers")
            with st.spinner(t("calculating_costs")):
                cost_data = calculate_all_provider_costs(token_counts)
                logger.info(
                    f"Cost calculation completed: {len(cost_data)} providers, cheapest: ${cost_data[0]['total_cost']:.4f}"
                    if cost_data
                    else "No cost data"
                )

            # Initialize session state for translation (if not already initialized)
            if "translation_in_progress" not in st.session_state:
                st.session_state.translation_in_progress = False
            if "translation_progress" not in st.session_state:
                st.session_state.translation_progress = (0, 0)
            if "translated_text" not in st.session_state:
                st.session_state.translated_text = None
            if "translation_pdf_path" not in st.session_state:
                st.session_state.translation_pdf_path = None
            if "translation_error" not in st.session_state:
                st.session_state.translation_error = None
            if "translation_clicked" not in st.session_state:
                st.session_state.translation_clicked = None
            if "translation_stopped" not in st.session_state:
                st.session_state.translation_stopped = False

            # List of implemented providers
            implemented_providers = ["google_gemini"]

            # Cost comparison
            if not st.session_state.translation_in_progress:
                st.markdown(f"### {t('cost_comparison_title')}")

                # Prepare dataframe
                cheapest_cost = (
                    min(cost_data, key=lambda x: x["total_cost"])["total_cost"] if cost_data else 0
                )
                df_data = []
                for cost in cost_data:
                    model_name = cost["model"]
                    if cost.get("exact", False):
                        model_name = f"✅ {model_name}"
                    elif "note" in cost:
                        model_name = f"⚠️ {model_name}"

                    df_data.append(
                        {
                            t("provider"): cost["provider"],
                            t("model"): model_name,
                            t("input_tokens"): f"{cost['input_tokens']:,}",
                            t("output_tokens_est"): f"{cost['output_tokens']:,}",
                            t("input_cost"): f"${cost['input_cost']:.4f}",
                            t("output_cost"): f"${cost['output_cost']:.4f}",
                            t("total_cost"): f"${cost['total_cost']:.4f}",
                            "provider_key": cost["provider_key"],
                            "is_implemented": cost["provider_key"] in implemented_providers,
                            "total_cost_value": cost["total_cost"],
                        }
                    )

                df = pd.DataFrame(df_data)
                st.dataframe(
                    df[
                        [
                            t("provider"),
                            t("model"),
                            t("input_tokens"),
                            t("output_tokens_est"),
                            t("input_cost"),
                            t("output_cost"),
                            t("total_cost"),
                        ]
                    ],
                    use_container_width=True,
                    hide_index=True,
                    height=min(400, len(df_data) * 50 + 50),
                )

                # Provider selection buttons
                st.markdown(f"#### {t('select_provider_title')}")
                num_cols = min(2, len(cost_data))
                button_cols = st.columns(num_cols)

                for idx, cost in enumerate(cost_data):
                    col = button_cols[idx % num_cols]
                    with col:
                        is_implemented = cost["provider_key"] in implemented_providers
                        provider_icon = {
                            "Google": "🔵",
                            "Anthropic": "🟣",
                            "OpenAI": "🟢",
                            "DeepL": "🔴",
                        }.get(cost["provider"], "⚪")

                        button_label = f"{provider_icon} **{cost['provider']} {cost['model']}**"
                        if is_implemented:
                            button_label += f"\n💰 ${cost['total_cost']:.4f}"
                            if cost["total_cost"] == cheapest_cost:
                                button_label = f"🏆 {t('best_value')}\n{button_label}"
                        else:
                            button_label += f"\n🚧 {t('coming_soon')}"

                        button_type = (
                            "primary"
                            if (cost["total_cost"] == cheapest_cost and is_implemented)
                            else "secondary"
                        )

                        if st.button(
                            button_label,
                            key=f"translate_btn_{cost['provider_key']}",
                            disabled=not is_implemented,
                            use_container_width=True,
                            type=button_type,
                        ):
                            st.session_state.translation_clicked = cost["provider_key"]
                            st.session_state.translation_error = None
                            st.rerun()

                # Cost summary
                if cost_data:
                    cheapest = min(cost_data, key=lambda x: x["total_cost"])
                    most_expensive = max(cost_data, key=lambda x: x["total_cost"])
                    cost_range = most_expensive["total_cost"] - cheapest["total_cost"]

                    info_cols = st.columns(3)
                    with info_cols[0]:
                        st.metric(t("metric_cheapest"), f"${cheapest['total_cost']:.4f}")
                    with info_cols[1]:
                        st.metric(
                            t("metric_most_expensive"),
                            f"${most_expensive['total_cost']:.4f}",
                            delta=f"+${cost_range:.4f}",
                            delta_color="inverse",
                        )
                    with info_cols[2]:
                        st.metric(t("metric_cost_range"), f"${cost_range:.4f}")

            # Handle translation for Gemini Pro
            if (
                st.session_state.translation_clicked == "google_gemini"
                and not st.session_state.translation_in_progress
            ):
                clicked_cost = next(c for c in cost_data if c["provider_key"] == "google_gemini")
                logger.info(
                    f"Translation requested for provider: {clicked_cost['provider']}, model: {clicked_cost['model']}, estimated cost: ${clicked_cost['total_cost']:.4f}"
                )

                # Get API key and strip whitespace
                google_api_key = config.GOOGLE_API_KEY
                if google_api_key:
                    google_api_key = google_api_key.strip()

                if not google_api_key:
                    logger.error("Google API key is missing")
                    st.error(f"❌ {t('api_key_missing')}")
                    st.info(t("api_key_info"))
                else:
                    # Show API key status (masked for security)
                    api_key_preview = "****...****" if google_api_key else "****"
                    st.caption(t("using_api_key", api_key=api_key_preview))

                    # Determine if resuming - use preserved resume_from_index if available, otherwise calculate from progress
                    resume_from = 0
                    if st.session_state.user_chose_resume:
                        # Use the resume_from_index that was set when user clicked "Resume" button
                        if (
                            "resume_from_index" in st.session_state
                            and st.session_state.resume_from_index > 0
                        ):
                            resume_from = st.session_state.resume_from_index
                            logger.info(
                                f"Using preserved resume index: {resume_from} (paragraph {resume_from + 1}) for file_id: {current_file_id}"
                            )
                        elif existing_progress:
                            # Fallback: calculate from existing progress
                            resume_from = existing_progress.get("completed_paragraphs", 0)
                            st.session_state.resume_from_index = resume_from
                            if resume_from > 0:
                                logger.info(
                                    f"Calculated resume from progress: {resume_from} (paragraph {resume_from + 1}) for file_id: {current_file_id}"
                                )
                    elif st.session_state.user_chose_resume is False:
                        logger.info(
                            f"Starting fresh translation for file_id: {current_file_id}, deleting old progress"
                        )
                        delete_progress(current_file_id, reason="user chose to start fresh")
                        st.session_state.existing_progress = None
                        st.session_state.resume_from_index = 0

                    # Start translation button
                    info_cols = st.columns([3, 1])
                    with info_cols[0]:
                        info_text = t(
                            "estimated_cost_info",
                            cost=f"{clicked_cost['total_cost']:.4f}",
                            provider=clicked_cost["provider"],
                            model=clicked_cost["model"],
                        )
                        if resume_from > 0:
                            total_paras = (
                                existing_progress.get("total_paragraphs", 0)
                                if existing_progress
                                else 0
                            )
                            info_text += f"\n\n🔄 **{t('resuming_from', index=resume_from + 1)}**"
                            if total_paras > 0:
                                info_text += f"\n\n✅ **Will CONTINUE from paragraph {resume_from + 1} of {total_paras}** (paragraphs 1-{resume_from} already translated)"
                        else:
                            info_text += f"\n\n🆕 **Will START from the beginning**"
                        st.info(info_text)
                    with info_cols[1]:
                        if st.button(
                            t("start_translation_button"), type="primary", use_container_width=True
                        ):
                            logger.info(
                                f"Starting translation process - resume_from_index: {resume_from}"
                            )
                            st.session_state.translation_in_progress = True
                            st.session_state.translated_text = None
                            st.session_state.translation_pdf_path = None
                            st.session_state.resume_from_index = resume_from
                            st.rerun()

            # Handle translation in progress
            if (
                st.session_state.translation_in_progress
                and st.session_state.translation_clicked == "google_gemini"
            ):
                # Get API key
                google_api_key = config.GOOGLE_API_KEY
                if google_api_key:
                    google_api_key = google_api_key.strip()

                if not google_api_key:
                    st.session_state.translation_in_progress = False
                    st.error(f"❌ {t('api_key_missing')}")
                else:
                    # Progress display
                    st.markdown(f"### {t('translation_progress')}")
                    metrics_cols = st.columns(5)
                    with metrics_cols[0]:
                        start_time_placeholder = st.empty()
                    with metrics_cols[1]:
                        end_time_placeholder = st.empty()
                    with metrics_cols[2]:
                        duration_placeholder = st.empty()
                    with metrics_cols[3]:
                        paragraphs_placeholder = st.empty()
                    with metrics_cols[4]:
                        eta_placeholder = st.empty()

                    # Progress bar and text in one row
                    progress_cols = st.columns([4, 1])
                    with progress_cols[0]:
                        progress_bar_placeholder = st.empty()
                        progress_text_placeholder = st.empty()
                    with progress_cols[1]:
                        if st.button(
                            t("stop_translation"),
                            type="secondary",
                            use_container_width=True,
                            key="stop_translation_btn",
                        ):
                            st.session_state.translation_stopped = True
                            logger.info("User clicked stop translation button")
                            st.rerun()

                    # Status placeholder (simplified, no duplicate info)
                    status_placeholder = st.empty()

                    # Streaming text display
                    st.markdown(f"#### {t('live_translation_title')}")
                    stats_cols = st.columns(4)
                    char_count_placeholder = stats_cols[0].empty()
                    word_count_placeholder = stats_cols[1].empty()
                    paragraph_count_placeholder = stats_cols[2].empty()
                    speed_placeholder = stats_cols[3].empty()

                    streaming_text_placeholder = st.empty()

                    # Partial PDF download section (will be updated during translation)
                    partial_pdf_container = st.container()

                    # Initialize streaming text accumulator
                    if "streaming_text" not in st.session_state:
                        st.session_state.streaming_text = ""
                    if "streaming_start_time" not in st.session_state:
                        st.session_state.streaming_start_time = None
                    if "current_paragraph_text" not in st.session_state:
                        st.session_state.current_paragraph_text = ""
                    if "current_paragraph_idx" not in st.session_state:
                        st.session_state.current_paragraph_idx = 0

                    # Count paragraphs early so it's available in callbacks
                    paragraphs_list = split_into_paragraphs(extracted_text)
                    paragraph_count = len(paragraphs_list)
                    if paragraph_count == 0:
                        paragraph_count = 1  # At least 1 paragraph
                    logger.info(f"Text split into {paragraph_count} paragraphs for translation")

                    def update_progress(completed, total):
                        """Update progress showing completed paragraphs with ETA."""
                        progress = completed / total if total > 0 else 0.0
                        percentage = progress * 100

                        # Update progress bar with percentage
                        progress_bar_placeholder.progress(progress)

                        # Calculate ETA if we have progress
                        eta_text = ""
                        eta_display = "-"
                        rate_text = ""
                        if completed > 0 and completed < total:
                            # Get elapsed time
                            if "translation_start_time" not in st.session_state:
                                st.session_state.translation_start_time = datetime.now()

                            elapsed = (
                                datetime.now() - st.session_state.translation_start_time
                            ).total_seconds()

                            # Calculate rate (paragraphs per second)
                            if elapsed > 0:
                                rate = completed / elapsed  # paragraphs per second
                                remaining_paragraphs = total - completed
                                eta_seconds = remaining_paragraphs / rate if rate > 0 else 0

                                # Format ETA for inline text
                                if eta_seconds < 60:
                                    eta_text = f" | ETA: {int(eta_seconds)}s"
                                    eta_display = f"{int(eta_seconds)}s"
                                elif eta_seconds < 3600:
                                    minutes = int(eta_seconds // 60)
                                    seconds = int(eta_seconds % 60)
                                    eta_text = f" | ETA: {minutes}m {seconds}s"
                                    eta_display = f"{minutes}m {seconds}s"
                                else:
                                    hours = int(eta_seconds // 3600)
                                    minutes = int((eta_seconds % 3600) // 60)
                                    eta_text = f" | ETA: {hours}h {minutes}m"
                                    eta_display = f"{hours}h {minutes}m"

                                # Also show rate
                                rate_text = f" ({rate:.2f} para/s)"

                                # Update ETA metric
                                eta_placeholder.metric(
                                    t("metric_eta"),
                                    eta_display,
                                    help=f"Estimated time remaining at {rate:.2f} paragraphs/second",
                                )
                            else:
                                eta_placeholder.metric(t("metric_eta"), "-")
                        else:
                            if completed >= total:
                                eta_placeholder.metric(t("metric_eta"), "Done")
                            else:
                                eta_placeholder.metric(t("metric_eta"), "-")

                        # Show consolidated progress text with ETA
                        if completed < total:
                            progress_text_placeholder.markdown(
                                f"**{completed}/{total} paragraphs ({percentage:.1f}%)**{eta_text}{rate_text}"
                            )
                            # Clear status placeholder to avoid duplicate info
                            status_placeholder.empty()
                        else:
                            progress_text_placeholder.markdown(
                                f"**✅ {completed}/{total} paragraphs translated (100%)**"
                            )
                            status_placeholder.success(f"✅ Translation completed!")

                        # Store completed count for partial PDF button
                        st.session_state.current_completed = completed
                        st.session_state.current_total = total

                    def update_streaming(paragraph_idx, chunk_text, accumulated_text):
                        """Update streaming text display with enhanced visuals - shows only current paragraph."""
                        st.session_state.streaming_text = accumulated_text

                        # Track current paragraph separately
                        # If paragraph index changed, reset current paragraph text and start building new one
                        if st.session_state.current_paragraph_idx != paragraph_idx:
                            st.session_state.current_paragraph_idx = paragraph_idx
                            st.session_state.current_paragraph_text = chunk_text
                        else:
                            # Same paragraph - append chunk to current paragraph text
                            # Extract just the current paragraph from accumulated text
                            # Split by double newlines (paragraph separator) and get the last one
                            paragraphs = accumulated_text.split("\n\n")
                            if paragraphs:
                                st.session_state.current_paragraph_text = paragraphs[-1]
                            else:
                                # Fallback: append chunk if split didn't work
                                st.session_state.current_paragraph_text += chunk_text

                        # Initialize start time on first chunk
                        if st.session_state.streaming_start_time is None:
                            st.session_state.streaming_start_time = datetime.now()

                        # Calculate stats based on total accumulated text
                        char_count = len(accumulated_text)
                        word_count = len(accumulated_text.split())
                        elapsed = (
                            datetime.now() - st.session_state.streaming_start_time
                        ).total_seconds()
                        speed = char_count / elapsed if elapsed > 0 else 0

                        # Update streaming text display
                        import html

                        escaped_current_paragraph = html.escape(
                            st.session_state.current_paragraph_text
                        )
                        streaming_text_placeholder.markdown(
                            f'<div class="streaming-text-container">{escaped_current_paragraph}</div>',
                            unsafe_allow_html=True,
                        )

                        # Update stats - show current paragraph out of total
                        char_count_placeholder.metric(t("metric_characters"), f"{char_count:,}")
                        word_count_placeholder.metric(t("metric_words"), f"{word_count:,}")
                        paragraph_count_placeholder.metric(
                            t("metric_paragraphs"), f"{paragraph_idx} / {paragraph_count}"
                        )
                        speed_placeholder.metric(
                            t("metric_speed"),
                            f"{speed:.0f} {t('chars_per_sec')}"
                            if speed > 0
                            else f"0 {t('chars_per_sec')}",
                        )

                    try:
                        # Get language settings from config
                        source_lang = config.SOURCE_LANGUAGE
                        target_lang = config.TARGET_LANGUAGE

                        # Record start time
                        start_time = datetime.now()
                        start_time_str = start_time.strftime("%H:%M:%S")
                        st.session_state.translation_start_time = (
                            start_time  # Store for ETA calculation
                        )
                        logger.info(
                            f"Translation started at {start_time_str}, source: {source_lang}, target: {target_lang}"
                        )

                        # Initialize progress display
                        progress_bar_placeholder.progress(0.0)
                        progress_text_placeholder.markdown(
                            f"**0/{paragraph_count} paragraphs (0.0%)**"
                        )

                        # Display initial metrics
                        start_time_placeholder.metric(t("metric_start_time"), start_time_str)
                        end_time_placeholder.metric(t("metric_end_time"), "-")
                        duration_placeholder.metric(t("metric_duration"), "-")
                        paragraphs_placeholder.metric(t("metric_total_paragraphs"), paragraph_count)
                        eta_placeholder.metric(t("metric_eta"), "-")

                        status_placeholder.info(t("starting_translation"))

                        # Reset streaming text and stats
                        st.session_state.streaming_text = ""
                        st.session_state.streaming_start_time = None
                        st.session_state.current_paragraph_text = ""
                        st.session_state.current_paragraph_idx = 0
                        # Waiting message
                        import html

                        waiting_msg = html.escape(t("waiting_for_translation"))
                        streaming_text_placeholder.markdown(
                            f'<div class="streaming-text-container" style="color: #888;">{waiting_msg}</div>',
                            unsafe_allow_html=True,
                        )
                        char_count_placeholder.metric(t("metric_characters"), "0")
                        word_count_placeholder.metric(t("metric_words"), "0")
                        paragraph_count_placeholder.metric(
                            t("metric_paragraphs"), f"0 / {paragraph_count}"
                        )
                        speed_placeholder.metric(t("metric_speed"), f"0 {t('chars_per_sec')}")

                        # Enable streaming based on config
                        enable_streaming = config.ENABLE_STREAMING

                        # Get resume index from session state
                        resume_from_index = st.session_state.get("resume_from_index", 0)
                        if resume_from_index > 0:
                            status_placeholder.info(
                                f"🔄 {t('resuming_from', index=resume_from_index + 1)}"
                            )

                        # Create stop check callback
                        def stop_check():
                            return st.session_state.get("translation_stopped", False)

                        # Reset stop flag at start
                        st.session_state.translation_stopped = False

                        # Partial PDF download button (check progress file periodically)
                        with partial_pdf_container:
                            current_progress = load_progress(current_file_id)
                            if current_progress:
                                completed_para = current_progress.get("completed_paragraphs", 0)
                                total_para = current_progress.get(
                                    "total_paragraphs", paragraph_count
                                )
                                if completed_para > 0:
                                    partial_cols = st.columns([3, 1])
                                    with partial_cols[0]:
                                        st.info(
                                            f"💾 {t('download_partial_pdf', completed=completed_para, total=total_para)}"
                                        )
                                    with partial_cols[1]:
                                        if st.button(
                                            t(
                                                "download_partial_pdf",
                                                completed=completed_para,
                                                total=total_para,
                                            ),
                                            key="partial_pdf_download_btn",
                                            use_container_width=True,
                                        ):
                                            # Generate partial PDF from current progress
                                            try:
                                                logger.info(
                                                    f"Generating partial PDF: file_id={current_file_id}, {completed_para}/{total_para} paragraphs"
                                                )
                                                translated_text_partial = (
                                                    get_translated_text_from_progress(
                                                        current_progress
                                                    )
                                                )
                                                output_dir = config.get_pdf_output_dir()
                                                base_name = Path(filename).stem
                                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                                pdf_filename = f"translated_{base_name}_partial_{timestamp}.pdf"
                                                pdf_path = str(output_dir / pdf_filename)

                                                source_lang_partial = current_progress.get(
                                                    "source_lang", config.SOURCE_LANGUAGE
                                                )
                                                target_lang_partial = current_progress.get(
                                                    "target_lang", config.TARGET_LANGUAGE
                                                )

                                                title = t(
                                                    "partial_pdf_title",
                                                    completed=completed_para,
                                                    total=total_para,
                                                )

                                                create_pdf_from_text(
                                                    translated_text_partial,
                                                    pdf_path,
                                                    title=title,
                                                    source_lang=source_lang_partial,
                                                    target_lang=target_lang_partial,
                                                    metadata={
                                                        "original_filename": filename,
                                                        "partial_translation": True,
                                                        "completed_paragraphs": completed_para,
                                                        "total_paragraphs": total_para,
                                                        "note": t(
                                                            "partial_pdf_note",
                                                            completed=completed_para,
                                                            total=total_para,
                                                        ),
                                                    },
                                                    include_metadata=False,
                                                )

                                                logger.info(
                                                    f"Partial PDF generated: file_id={current_file_id}, path={pdf_path}"
                                                )

                                                # Provide download
                                                with open(pdf_path, "rb") as pdf_file:
                                                    st.download_button(
                                                        label=f"📥 {t('download_pdf')}",
                                                        data=pdf_file.read(),
                                                        file_name=pdf_filename,
                                                        mime="application/pdf",
                                                        type="primary",
                                                        use_container_width=True,
                                                        key="download_generated_partial_pdf",
                                                    )
                                            except Exception as e:
                                                logger.error(
                                                    f"Error generating partial PDF: {e}",
                                                    exc_info=True,
                                                )
                                                st.error(f"Error generating partial PDF: {e}")

                        translated_text = translate_text_gemini(
                            extracted_text,
                            google_api_key,
                            source_lang=source_lang,
                            target_lang=target_lang,
                            progress_callback=update_progress,
                            stream=enable_streaming,
                            stream_callback=update_streaming if enable_streaming else None,
                            progress_file_id=current_file_id,
                            resume_from_index=resume_from_index,
                            stop_check=stop_check,
                        )

                        st.session_state.translated_text = translated_text
                        logger.info(
                            f"Translation completed: {len(translated_text)} characters translated"
                        )

                        # Record end time
                        end_time = datetime.now()
                        end_time_str = end_time.strftime("%H:%M:%S")
                        duration = end_time - start_time
                        duration_str = f"{duration.total_seconds():.1f}s"
                        logger.info(f"Translation duration: {duration_str}")

                        # Update metrics
                        end_time_placeholder.metric(t("metric_end_time"), end_time_str)
                        duration_placeholder.metric(t("metric_duration"), duration_str)

                        # Final streaming text update
                        if enable_streaming:
                            final_char_count = len(translated_text)
                            final_word_count = len(translated_text.split())
                            final_elapsed = (
                                (
                                    datetime.now() - st.session_state.streaming_start_time
                                ).total_seconds()
                                if st.session_state.streaming_start_time
                                else 0
                            )
                            final_speed = (
                                final_char_count / final_elapsed if final_elapsed > 0 else 0
                            )

                            # Final text display
                            import html

                            escaped_final_text = html.escape(translated_text)
                            streaming_text_placeholder.markdown(
                                f'<div class="streaming-text-container">{escaped_final_text}</div>',
                                unsafe_allow_html=True,
                            )
                            char_count_placeholder.metric(
                                t("metric_characters"), f"{final_char_count:,}"
                            )
                            word_count_placeholder.metric(
                                t("metric_words"), f"{final_word_count:,}"
                            )
                            paragraph_count_placeholder.metric(
                                t("metric_paragraphs"), f"{paragraph_count} / {paragraph_count}"
                            )
                            speed_placeholder.metric(
                                t("metric_avg_speed"),
                                f"{final_speed:.0f} {t('chars_per_sec')}"
                                if final_speed > 0
                                else f"0 {t('chars_per_sec')}",
                            )

                        # Generate PDF
                        status_placeholder.info(t("generating_pdf"))
                        logger.info("Generating PDF from translated text")

                        # Determine output directory
                        output_dir = config.get_pdf_output_dir()

                        # Get original filename if available
                        original_filename = (
                            uploaded_file.name if hasattr(uploaded_file, "name") else "document.pdf"
                        )
                        # Create output filename
                        base_name = Path(original_filename).stem
                        pdf_filename = f"translated_{base_name}.pdf"
                        pdf_path = str(output_dir / pdf_filename)

                        create_pdf_from_text(
                            translated_text,
                            pdf_path,
                            title="Translated Document",
                            source_lang=source_lang,
                            target_lang=target_lang,
                            metadata={"original_filename": original_filename},
                            include_metadata=False,  # Don't add metadata page
                        )

                        logger.info(f"PDF generated successfully: {pdf_path}")
                        st.session_state.translation_pdf_path = pdf_path
                        st.session_state.translation_in_progress = False

                        # Delete progress file after successful completion
                        delete_progress(current_file_id, reason="translation completed")
                        logger.info(f"Progress deleted after completion: file_id={current_file_id}")
                        st.session_state.existing_progress = None

                        # Show completion with full progress
                        progress_bar_placeholder.progress(1.0)
                        progress_text_placeholder.markdown("**Progress: Complete (100%)**")
                        status_placeholder.success(t("translation_completed"))

                    except TranslationStoppedException as e:
                        # Translation was stopped by user
                        logger.info(f"Translation stopped: {e}")
                        st.session_state.translation_in_progress = False
                        st.session_state.translation_stopped = True

                        # Load current progress to show what was completed
                        current_progress = load_progress(current_file_id)
                        if current_progress:
                            completed = current_progress.get("completed_paragraphs", 0)
                            total = current_progress.get("total_paragraphs", 0)
                            percent = (completed / total * 100) if total > 0 else 0

                            progress_bar_placeholder.progress(percent / 100)
                            progress_text_placeholder.markdown(
                                f"**⏸️ {t('translation_stopped')}: {completed}/{total} paragraphs translated ({percent:.1f}%)**"
                            )
                            status_placeholder.warning(t("translation_stopped_message"))

                            # Show resume button
                            resume_cols = st.columns([3, 1])
                            with resume_cols[1]:
                                if st.button(
                                    t("resume_translation_button"),
                                    type="primary",
                                    use_container_width=True,
                                    key="resume_after_stop",
                                ):
                                    st.session_state.translation_stopped = False
                                    st.session_state.translation_in_progress = True
                                    st.session_state.resume_from_index = completed
                                    st.session_state.user_chose_resume = True
                                    logger.info(
                                        f"Resuming translation from paragraph {completed + 1} after stop"
                                    )
                                    st.rerun()
                        else:
                            status_placeholder.warning(t("translation_stopped_message"))

                    except ValueError as e:
                        # Authentication/API key errors
                        logger.error(f"Authentication error during translation: {e}", exc_info=True)
                        st.session_state.translation_in_progress = False
                        st.session_state.translation_error = str(e)
                        progress_bar_placeholder.empty()
                        progress_text_placeholder.empty()
                        streaming_text_placeholder.empty()
                        char_count_placeholder.empty()
                        status_placeholder.error(t("authentication_error", error=str(e)))
                        st.warning(f"""
                        {t("troubleshooting_title")}
                        {t("troubleshooting_1")}
                        {t("troubleshooting_2")}
                        {t("troubleshooting_3")}
                        {t("troubleshooting_4")}
                        {t("troubleshooting_5")}
                        """)
                    except ImportError as e:
                        # Missing package errors
                        logger.error(f"Missing package error: {e}", exc_info=True)
                        st.session_state.translation_in_progress = False
                        st.session_state.translation_error = str(e)
                        progress_bar_placeholder.empty()
                        progress_text_placeholder.empty()
                        streaming_text_placeholder.empty()
                        char_count_placeholder.empty()
                        status_placeholder.error(t("missing_package", error=str(e)))
                        st.info(t("install_packages"))
                    except Exception as e:
                        # Other errors
                        logger.error(f"Translation error: {e}", exc_info=True)
                        st.session_state.translation_in_progress = False
                        st.session_state.translation_error = str(e)
                        progress_bar_placeholder.empty()
                        progress_text_placeholder.empty()
                        streaming_text_placeholder.empty()
                        char_count_placeholder.empty()
                        error_msg = str(e)

                        # Provide helpful error messages
                        if "rate limit" in error_msg.lower() or "429" in error_msg:
                            status_placeholder.error(t("rate_limit_exceeded"))
                            st.warning(t("rate_limit_warning"))
                        elif "network" in error_msg.lower() or "connection" in error_msg.lower():
                            status_placeholder.error(t("network_error"))
                            st.warning(t("network_warning"))
                        else:
                            status_placeholder.error(t("translation_failed", error=error_msg))

                        with st.expander(t("error_details")):
                            st.exception(e)

            # Translation results
            if st.session_state.translated_text and st.session_state.translation_pdf_path:
                st.markdown(f"### {t('translation_results_title')}")

                pdf_path = st.session_state.translation_pdf_path
                result_cols = st.columns([2, 1])

                with result_cols[0]:
                    if config.PDF_OUTPUT_DIR:
                        st.success(f"📁 {t('pdf_saved_to', path=pdf_path)}")
                    else:
                        st.info(f"📁 {t('pdf_saved_temp', path=pdf_path)}")

                with result_cols[1]:
                    with open(pdf_path, "rb") as pdf_file:
                        st.download_button(
                            label=t("download_pdf"),
                            data=pdf_file.read(),
                            file_name=Path(pdf_path).name,
                            mime="application/pdf",
                            type="primary",
                            use_container_width=True,
                        )

                # Preview
                st.markdown(f"#### {t('translation_preview_title')}")
                preview_cols = st.columns([3, 1])

                with preview_cols[0]:
                    preview_text = st.session_state.translated_text[:1000]
                    st.text_area(t("preview_label"), preview_text, height=200, disabled=True)

                with preview_cols[1]:
                    st.metric(t("characters"), f"{len(st.session_state.translated_text):,}")
                    st.metric(t("words"), f"{len(st.session_state.translated_text.split()):,}")
                    try:
                        with pdfplumber.open(pdf_path) as pdf:
                            st.metric(t("pages"), len(pdf.pages))
                    except Exception:
                        estimated_pages = max(1, len(st.session_state.translated_text) // 2000)
                        st.metric(t("pages"), f"~{estimated_pages}")

            # Show error if any
            if st.session_state.translation_error:
                st.error(t("translation_error", error=st.session_state.translation_error))

            # Show message for other providers (not yet implemented)
            if (
                st.session_state.translation_clicked
                and st.session_state.translation_clicked != "google_gemini"
            ):
                clicked_cost = next(
                    c
                    for c in cost_data
                    if c["provider_key"] == st.session_state.translation_clicked
                )
                st.info(
                    t(
                        "not_implemented_info",
                        provider=clicked_cost["provider"],
                        model=clicked_cost["model"],
                        cost=f"{clicked_cost['total_cost']:.4f}",
                    )
                )

        except FileNotFoundError:
            logger.error("PDF file not found", exc_info=True)
            st.error(t("pdf_not_found"))
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error processing PDF: {error_msg}", exc_info=True)
            st.error(t("error_processing_pdf", error=error_msg))

            # Provide helpful error messages
            if "corrupted" in error_msg.lower() or "invalid" in error_msg.lower():
                st.warning(t("pdf_corrupted"))
            elif "permission" in error_msg.lower():
                st.warning(t("permission_denied"))
            else:
                with st.expander(t("technical_details")):
                    st.exception(e)

else:
    # No file uploaded - reset file tracking
    if "current_file_id" in st.session_state:
        logger.info("File removed, clearing file tracking")
        st.session_state.current_file_id = None

    # Clean empty state
    welcome_cols = st.columns([2, 1])
    with welcome_cols[0]:
        st.markdown(f"### {t('welcome_title')}")
        st.markdown(t("welcome_description"))

    with welcome_cols[1]:
        st.info(f"""
        **{t("welcome_quick_start_title")}**
        1. {t("welcome_quick_start_1")}
        2. {t("welcome_quick_start_2")}
        3. {t("welcome_quick_start_3")}
        4. {t("welcome_quick_start_4")}
        """)

    # Features
    st.markdown(f"### {t('features_title')}")
    feature_cols = st.columns(4)
    with feature_cols[0]:
        st.markdown(
            f"**💰 {t('features_free_estimates_title')}**\n\n{t('features_free_estimates_1')}"
        )
    with feature_cols[1]:
        st.markdown(f"**📊 {t('features_compare_title')}**\n\n{t('features_compare_1')}")
    with feature_cols[2]:
        st.markdown(f"**🚀 {t('features_live_title')}**\n\n{t('features_live_1')}")
    with feature_cols[3]:
        st.markdown(f"**📄 {t('features_pdf_title')}**\n\n{t('features_pdf_1')}")
