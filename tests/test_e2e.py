"""Makes the opt-in real-tools flow visible to ``unittest discover``.

Without ``DJNG_E2E=1`` it is reported as skipped; see ``tests/e2e/run_e2e.py``.
"""

from tests.e2e.run_e2e import RealToolsEndToEndTests

__all__ = ["RealToolsEndToEndTests"]
