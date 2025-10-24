"""File upload utilities for OHLCV data.

This module provides Streamlit components for uploading and processing
parquet files containing OHLCV candlestick data that were previously
saved using the tape.models.ohlcv.OHLCV.to_parquet() method.
"""

import pandas as pd
import streamlit as st
from loguru import logger
from streamlit.runtime.uploaded_file_manager import UploadedFile


def upload_ohlcv_parquet(
    accept_multiple_files: bool = True,
    key: str | None = None,
    help_text: str | None = None,
) -> pd.DataFrame | None:
    """Upload one or more parquet files containing OHLCV data.

    Provides a Streamlit file uploader widget that accepts parquet files
    and combines them into a single pandas DataFrame. Handles multiple files
    that may contain split data, automatically concatenating and sorting by time.

    Args:
        accept_multiple_files: Whether to allow multiple file uploads
            Default: True. Set to False if you only want to upload a single file.
        key: Unique key for the Streamlit widget
            If None, Streamlit will auto-generate a key.
        help_text: Custom help text to display below the uploader
            If None, uses default help text.

    Returns:
        pd.DataFrame with columns [time, open, high, low, close, volume]
            - Sorted by time (ascending)
            - Duplicates removed (keeps first occurrence)
            - Index reset
        Returns None if no files are uploaded.

    Examples:
        Basic usage:
        >>> df = upload_ohlcv_parquet()
        >>> if df is not None:
        ...     st.write(f"Loaded {len(df)} candles")
        ...     st.dataframe(df)

        Single file upload only:
        >>> df = upload_ohlcv_parquet(accept_multiple_files=False)

        With custom help text:
        >>> df = upload_ohlcv_parquet(
        ...     help_text="Upload BTC/USDT 1h candles from data/ohlcv directory"
        ... )

        With unique key for multiple uploaders on same page:
        >>> df1 = upload_ohlcv_parquet(key="btc_uploader")
        >>> df2 = upload_ohlcv_parquet(key="eth_uploader")

    Notes:
        - Files should be parquet format created by OHLCV.to_parquet()
        - When multiple files are uploaded, they are automatically:
            1. Concatenated into a single DataFrame
            2. Sorted by time (oldest first)
            3. Deduplicated (removes duplicate timestamps, keeping first)
        - Expected columns: time, open, high, low, close, volume
        - Time column should be datetime type
    """
    default_help = (
        "Upload parquet file(s) containing OHLCV data. "
        "Files can be created using OHLCV.to_parquet() from tape.models.ohlcv."
    )

    uploaded_files = st.file_uploader(
        "Upload OHLCV Parquet File(s)",
        type=["parquet"],
        accept_multiple_files=accept_multiple_files,
        key=key,
        help=help_text or default_help,
    )

    if not uploaded_files:
        return None

    # Handle both single file and multiple files
    if accept_multiple_files:
        files_to_process: list[UploadedFile] = (
            uploaded_files if isinstance(uploaded_files, list) else [uploaded_files]
        )
    else:
        files_to_process = [uploaded_files] if isinstance(uploaded_files, UploadedFile) else []

    logger.info(f"Processing {len(files_to_process)} parquet file(s)")

    dataframes: list[pd.DataFrame] = []

    for file in files_to_process:
        try:
            df = pd.read_parquet(file)
            logger.debug(f"Loaded {file.name}: {len(df)} rows")

            # Validate expected columns
            expected_columns = {"time", "open", "high", "low", "close", "volume"}
            if not expected_columns.issubset(df.columns):
                missing = expected_columns - set(df.columns)
                st.error(f"File {file.name} is missing columns: {missing}")
                logger.error(f"Invalid parquet file {file.name}: missing columns {missing}")
                continue

            dataframes.append(df)

        except Exception as e:
            st.error(f"Error reading {file.name}: {str(e)}")
            logger.exception(f"Failed to read parquet file {file.name}")
            continue

    if not dataframes:
        st.warning("No valid parquet files were loaded")
        return None

    # Combine all dataframes
    if len(dataframes) == 1:
        combined_df = dataframes[0]
        logger.info(f"Loaded single file with {len(combined_df)} rows")
    else:
        combined_df = pd.concat(dataframes, ignore_index=True)
        logger.info(f"Combined {len(dataframes)} files into DataFrame with {len(combined_df)} rows")

    # Sort by time and remove duplicates
    combined_df = combined_df.sort_values("time").drop_duplicates(subset=["time"], keep="first")
    combined_df = combined_df.reset_index(drop=True)

    logger.info(
        f"Final DataFrame: {len(combined_df)} rows "
        f"from {combined_df['time'].min()} to {combined_df['time'].max()}"
    )

    return combined_df


def upload_ohlcv_parquet_with_preview(
    accept_multiple_files: bool = True,
    key: str | None = None,
    show_stats: bool = True,
) -> pd.DataFrame | None:
    """Upload OHLCV parquet files with automatic data preview and statistics.

    Extended version of upload_ohlcv_parquet() that displays useful information
    about the uploaded data including basic statistics and data preview.

    Args:
        accept_multiple_files: Whether to allow multiple file uploads
        key: Unique key for the Streamlit widget
        show_stats: Whether to display statistics about the data

    Returns:
        pd.DataFrame with OHLCV data, or None if no files uploaded

    Examples:
        >>> df = upload_ohlcv_parquet_with_preview()
        >>> # Automatically shows data preview and statistics
        >>> if df is not None:
        ...     # Your analysis code here
        ...     pass
    """
    df = upload_ohlcv_parquet(accept_multiple_files=accept_multiple_files, key=key)

    if df is None:
        return None

    if show_stats:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Candles", f"{len(df):,}")

        with col2:
            time_range = df["time"].max() - df["time"].min()
            st.metric("Time Range", f"{time_range.days} days")

        with col3:
            price_change = (df["close"].iloc[-1] - df["close"].iloc[0]) / df["close"].iloc[0] * 100
            st.metric("Price Change", f"{price_change:.2f}%", delta=f"{price_change:.2f}%")

        # Show time range
        st.caption(
            f"Data range: {df['time'].min().strftime('%Y-%m-%d %H:%M')} "
            f"to {df['time'].max().strftime('%Y-%m-%d %H:%M')}"
        )

        # Data preview
        with st.expander("📊 Data Preview", expanded=False):
            st.dataframe(
                df.head(10),
                use_container_width=True,
                hide_index=True,
            )

            st.subheader("Basic Statistics")
            st.dataframe(
                df[["open", "high", "low", "close", "volume"]].describe(),
                use_container_width=True,
            )

            col1, col2 = st.columns(2)

            with col1:
                st.write("**First Candle:**")
                st.dataframe(df.head(1), use_container_width=True, hide_index=True)

            with col2:
                st.write("**Last Candle:**")
                st.dataframe(df.tail(1), use_container_width=True, hide_index=True)

    st.success(f"✅ Successfully loaded {len(df):,} candles!")
    return df
