"""
UI Components - reusable Streamlit components extracted from app.py.
"""

import streamlit as st
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path

from translations import get_translation, LANGUAGES, DEFAULT_LANGUAGE
from utils.logger_config import get_logger

logger = get_logger(__name__)


class UIComponents:
    """Reusable UI components for the application."""

    @staticmethod
    def render_header(language: str = DEFAULT_LANGUAGE):
        """Render page header and title."""
        t = lambda key, **kwargs: get_translation(key, language, **kwargs)

        page_title = t("page_title")
        page_icon = t("page_icon")

        st.set_page_config(
            page_title=page_title,
            page_icon=page_icon,
            layout="wide",
            initial_sidebar_state="expanded",
        )

        st.title(f"{page_icon} {page_title}")
        st.markdown(t("upload_prompt"))

    @staticmethod
    def render_sidebar(language: str) -> str:
        """Render sidebar with settings and language selector."""
        t = lambda key, **kwargs: get_translation(key, language, **kwargs)

        with st.sidebar:
            st.header(f"⚙️ {t('sidebar_settings')}")

            # Language selector
            selected_language = st.selectbox(
                t("select_language"),
                options=list(LANGUAGES.keys()),
                format_func=lambda x: LANGUAGES[x],
                index=list(LANGUAGES.keys()).index(language),
                key="language_selector",
            )

            st.divider()
            st.info(t("sidebar_info"))
            st.caption(t("token_counting_note"))

            return selected_language

    @staticmethod
    def render_pdf_uploader(language: str = DEFAULT_LANGUAGE) -> Optional[Any]:
        """Render PDF file uploader."""
        t = lambda key, **kwargs: get_translation(key, language, **kwargs)

        return st.file_uploader(t("choose_pdf_file"), type=["pdf"], help=t("upload_help"))

    @staticmethod
    def render_pdf_stats(metadata: Dict[str, Any], language: str = DEFAULT_LANGUAGE):
        """Render PDF processing statistics."""
        t = lambda key, **kwargs: get_translation(key, language, **kwargs)

        st.success(t("pdf_processed"))
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(label=t("pages"), value=metadata["page_count"])
        with col2:
            st.metric(label=t("characters"), value=f"{metadata['char_count']:,}")
        with col3:
            st.metric(label=t("words"), value=f"{metadata['word_count']:,}")

    @staticmethod
    def render_token_counts(
        token_counts: Dict[str, Dict[str, Any]], language: str = DEFAULT_LANGUAGE
    ):
        """Render token count metrics."""
        t = lambda key, **kwargs: get_translation(key, language, **kwargs)

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

    @staticmethod
    def render_cost_comparison(
        cost_data: List[Dict[str, Any]],
        implemented_providers: List[str],
        language: str = DEFAULT_LANGUAGE,
    ) -> Optional[str]:
        """Render cost comparison table and return selected provider."""
        t = lambda key, **kwargs: get_translation(key, language, **kwargs)

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

        import pandas as pd

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

        selected_provider = None
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
                    selected_provider = cost["provider_key"]

        return selected_provider

    @staticmethod
    def render_translation_controls(
        google_api_key: str,
        source_lang: str,
        target_lang: str,
        cost_data: Dict[str, Any],
        language: str = DEFAULT_LANGUAGE,
    ) -> Dict[str, Any]:
        """Render translation start controls and return configuration."""
        t = lambda key, **kwargs: get_translation(key, language, **kwargs)

        if not google_api_key:
            st.error(f"❌ {t('api_key_missing')}")
            st.info(t("api_key_info"))
            return {"can_start": False}

        # Show API key status (masked for security)
        api_key_preview = f"****...{google_api_key[-4:]}" if len(google_api_key) > 4 else "****"
        st.caption(t("using_api_key", api_key=api_key_preview))

        # Show cost info
        info_cols = st.columns([3, 1])
        with info_cols[0]:
            info_text = t(
                "estimated_cost_info",
                cost=f"{cost_data['total_cost']:.4f}",
                provider=cost_data["provider"],
                model=cost_data["model"],
            )
            st.info(info_text)
        with info_cols[1]:
            if st.button(t("start_translation_button"), type="primary", use_container_width=True):
                return {"can_start": True, "source_lang": source_lang, "target_lang": target_lang}

        return {"can_start": False}

    @staticmethod
    def render_welcome_screen(language: str = DEFAULT_LANGUAGE):
        """Render welcome screen when no file is uploaded."""
        t = lambda key, **kwargs: get_translation(key, language, **kwargs)

        st.markdown(f"# {t('welcome_title')}")
        st.markdown(f"**{t('welcome_description')}**")

        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown(f"### {t('welcome_features_title')}")
            st.markdown(f"""
            **{t("features_free_estimates_title")}**
            - {t("features_free_estimates_1")}
            - {t("features_free_estimates_2")}
            - {t("features_free_estimates_3")}
            
            **{t("features_compare_title")}**
            - {t("features_compare_1")}
            - {t("features_compare_2")}
            - {t("features_compare_3")}
            """)

        with col2:
            st.markdown(f"### {t('welcome_quick_start_title')}")
            st.markdown(f"""
            1. {t("welcome_quick_start_1")}
            2. {t("welcome_quick_start_2")}
            3. {t("welcome_quick_start_3")}
            4. {t("welcome_quick_start_4")}
            """)

            st.markdown(f"**{t('sidebar_tip')}**")

    @staticmethod
    def render_progress_section(
        file_id: str, paragraph_count: int, resume_from_index: int, language: str = DEFAULT_LANGUAGE
    ) -> None:
        """Render translation progress section."""
        t = lambda key, **kwargs: get_translation(key, language, **kwargs)

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

        # Progress bar
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

        return {
            "progress_bar_placeholder": progress_bar_placeholder,
            "progress_text_placeholder": progress_text_placeholder,
            "start_time_placeholder": start_time_placeholder,
            "end_time_placeholder": end_time_placeholder,
            "duration_placeholder": duration_placeholder,
            "paragraphs_placeholder": paragraphs_placeholder,
            "eta_placeholder": eta_placeholder,
        }
