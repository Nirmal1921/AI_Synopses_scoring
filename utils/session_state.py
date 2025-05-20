import base64
import json
import pickle
import uuid
import re

import streamlit as st
from streamlit.runtime.scriptrunner import ScriptRunner, ScriptRunnerImpl, RerunData
from streamlit.runtime.scriptrunner.script_run_context import (
    get_script_run_ctx,
    add_script_run_ctx,
)


class SessionState:
    """
    A class to help persist state variables between reruns.
    Adapted from https://gist.github.com/okld/0aba4869ba6fdc8d49132e6974e2e662
    """

    def __init__(self, **kwargs):
        """
        A new SessionState object.
        Parameters
        ----------
        **kwargs : any
            Default values for the session state.
        Example
        -------
        >>> session_state = SessionState(user_name='', favorite_color='black')
        >>> session_state.user_name = 'Mary'
        >>> session_state.favorite_color
        'black'
        """
        for key, val in kwargs.items():
            setattr(self, key, val)

    def clear(self):
        """
        Clears session state.
        Example
        -------
        >>> session_state = SessionState(user_name='', favorite_color='black')
        >>> session_state.clear()
        >>> session_state.user_name
        ''
        >>> session_state.favorite_color
        'black'
        """
        for key in list(self.__dict__.keys()):
            setattr(self, key, "")

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, state):
        self.__dict__.update(state)


def get_session_state(**kwargs):
    """
    Gets a SessionState object for the current session.
    Creates a new object if necessary.
    Parameters
    ----------
    **kwargs : any
        Default values you want to add to the session state, if it doesn't exist yet.
    Returns
    -------
    SessionState
        The session state for this session.
    """
    ctx = get_script_run_ctx()
    session_id = ctx.session_id
    session_info = ctx.session_info

    if session_info is None:
        raise RuntimeError(
            "Could not get session info for this Streamlit app. "
            "Are you using Streamlit 0.64.0 or later? "
        )

    # Create SessionState key in session_info if it doesn't exist
    if not hasattr(session_info, "session_state"):
        session_info.session_state = {}

    # Create SessionState object for this session_id if it doesn't exist
    if session_id not in session_info.session_state:
        session_info.session_state[session_id] = SessionState(**kwargs)

    return session_info.session_state[session_id]


def set_page_config():
    """
    Helper function to set the page configuration.
    """
    st.set_page_config(
        page_title="Synopsis Scorer",
        page_icon="📝",
        layout="wide",
        initial_sidebar_state="expanded",
    )