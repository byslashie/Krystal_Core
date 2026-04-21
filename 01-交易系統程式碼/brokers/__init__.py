"""Broker adapters and sync jobs.

Design:
- Streamlit (Mac/Windows) reads/writes ONLY Google Sheets.
- Broker sync jobs run on Windows and write into Sheets.
"""
