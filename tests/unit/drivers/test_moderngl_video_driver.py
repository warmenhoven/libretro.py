"""
Unit tests for :class:`.ModernGlVideoDriver`'s version knobs.

None of these create an OpenGL context;
they only exercise the negotiation in :meth:`.ModernGlVideoDriver.set_context`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from libretro.api.video import HardwareContext, retro_hw_render_callback
from libretro.drivers.video.driver import UnsupportedContextError

if TYPE_CHECKING:
    from libretro.drivers.video.opengl.moderngl import ModernGlVideoDriver
else:
    pytest.importorskip("moderngl")
    ModernGlVideoDriver = pytest.importorskip(
        "libretro.drivers.video.opengl.moderngl"
    ).ModernGlVideoDriver


def _core_request(major: int, minor: int) -> retro_hw_render_callback:
    return retro_hw_render_callback(
        context_type=HardwareContext.OPENGL_CORE,
        version_major=major,
        version_minor=minor,
    )


def test_no_cap_accepts_any_core_version() -> None:
    driver = ModernGlVideoDriver()
    driver.set_context(_core_request(4, 6))
    assert driver.max_gl_version is None


@pytest.mark.parametrize("cap", [(3, 3), (4, 0), (4, 6)])
def test_cap_at_or_above_the_request_accepts_it(cap: tuple[int, int]) -> None:
    driver = ModernGlVideoDriver(max_gl_version=cap)
    driver.set_context(_core_request(3, 3))
    assert driver.max_gl_version == cap


@pytest.mark.parametrize("cap", [(3, 2), (2, 1)])
def test_cap_below_the_request_refuses_it(cap: tuple[int, int]) -> None:
    driver = ModernGlVideoDriver(max_gl_version=cap)
    with pytest.raises(UnsupportedContextError, match="3.3"):
        driver.set_context(_core_request(3, 3))


def test_cap_compares_minor_versions_within_a_major() -> None:
    driver = ModernGlVideoDriver(max_gl_version=(4, 1))
    driver.set_context(_core_request(4, 1))
    with pytest.raises(UnsupportedContextError):
        driver.set_context(_core_request(4, 3))


@pytest.mark.parametrize("context_type", [HardwareContext.NONE, HardwareContext.OPENGL])
def test_cap_ignores_context_types_without_a_version(context_type: HardwareContext) -> None:
    driver = ModernGlVideoDriver(max_gl_version=(3, 2))
    driver.set_context(
        retro_hw_render_callback(context_type=context_type, version_major=4, version_minor=6)
    )


def test_forced_version_does_not_refuse_the_request() -> None:
    driver = ModernGlVideoDriver(gl_version=(4, 1))
    driver.set_context(_core_request(4, 3))
    assert driver.gl_version == (4, 1)


def test_no_context_before_reinit() -> None:
    assert ModernGlVideoDriver().context is None


@pytest.mark.parametrize("bad", [(3,), (3, 3, 3), 33, "3.3", (3.0, 3)])
def test_malformed_versions_are_rejected(bad: object) -> None:
    with pytest.raises(TypeError):
        ModernGlVideoDriver(max_gl_version=bad)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        ModernGlVideoDriver(gl_version=bad)  # type: ignore[arg-type]


@pytest.mark.parametrize("bad", [(-1, 0), (3, -2)])
def test_negative_versions_are_rejected(bad: tuple[int, int]) -> None:
    with pytest.raises(ValueError, match="non-negative"):
        ModernGlVideoDriver(max_gl_version=bad)
    with pytest.raises(ValueError, match="non-negative"):
        ModernGlVideoDriver(gl_version=bad)
