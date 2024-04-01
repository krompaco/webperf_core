# -*- coding: utf-8 -*-
from tests.lighthouse_base import run_test as lighthouse_base_run_test
from tests.utils import get_translation

def run_test(global_translation, lang_code, url, strategy='mobile', category='pwa'):
    """
    Analyzes URL with Lighthouse PWA.
    """

    local_translation = get_translation('pwa_lighthouse', lang_code)
    # pylint: disable=duplicate-code
    return lighthouse_base_run_test(
        lang_code,
        url,
        strategy,
        category,
        False,
        global_translation,
        local_translation)
