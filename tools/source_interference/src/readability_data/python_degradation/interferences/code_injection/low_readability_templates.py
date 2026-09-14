from __future__ import annotations

from collections.abc import Callable

NameFactory = Callable[[str], str]
TemplateRenderer = Callable[[NameFactory, int], tuple[str, ...]]


def _xor_cancellation(name: NameFactory, mask: int) -> tuple[str, ...]:
    value = name("opaque_value")
    return (
        f"{value} = {hex(mask)}",
        f"{value} = (({value} ^ {hex(mask)}) | 0) & -1",
        f"if ({value} & 1) == 1:",
        f"    {value} ^= {value}",
    )


def _subtraction_cancellation(name: NameFactory, mask: int) -> tuple[str, ...]:
    value = name("opaque_value")
    return (
        f"{value} = {hex(mask)} - {hex(mask)}",
        f"{value} = ({value} | 0) if {value} == 0 else ({value} & 0)",
    )


def _bounded_opaque_loop(name: NameFactory, mask: int) -> tuple[str, ...]:
    value, index = name("opaque_value"), name("opaque_index")
    return (
        f"{value}, {index} = 0, 0",
        f"while {index} < 2:",
        f"    {value} ^= ({index} << 1) ^ {hex(mask & 0xF)}",
        f"    {index} += 1",
        f"{value} ^= {value}",
    )


def _shift_and_clear(name: NameFactory, mask: int) -> tuple[str, ...]:
    value = name("opaque_value")
    return (
        f"{value} = {hex(mask)}",
        f"{value} = ({value} << 1) ^ ({value} >> 1)",
        f"{value} &= 0",
    )


def _opaque_boolean(name: NameFactory, mask: int) -> tuple[str, ...]:
    flag = name("opaque_flag")
    return (
        f"{flag} = (({hex(mask)} ^ {hex(mask)}) != 0)",
        f"{flag} = not (not {flag})",
    )


def _nested_false_branch(name: NameFactory, mask: int) -> tuple[str, ...]:
    value = name("opaque_value")
    return (
        f"{value} = {hex(mask)} ^ {hex(mask)}",
        f"if {value} != 0:",
        f"    if (({value} | 1) & 1) == 0:",
        f"        {value} += 1",
        "    else:",
        f"        {value} -= 1",
    )


def _opaque_branch(name: NameFactory, mask: int) -> tuple[str, ...]:
    state = name("opaque_state")
    return (
        f"{state} = {hex(mask)} ^ {hex(mask)}",
        f"if {state} == 0:",
        f"    {state} |= 0",
        "else:",
        f"    {state} &= 0",
    )


def _single_cycle_loop(name: NameFactory, mask: int) -> tuple[str, ...]:
    value, guard = name("opaque_value"), name("opaque_guard")
    return (
        f"{value}, {guard} = {hex(mask)}, True",
        f"while {guard}:",
        f"    {value} ^= {hex(mask)}",
        f"    {guard} = False",
    )


def _opaque_ternary_chain(name: NameFactory, mask: int) -> tuple[str, ...]:
    value = name("opaque_value")
    return (
        f"{value} = {hex(mask)}",
        f"{value} = (0 if ({value} ^ {value}) == 0 else 1) if ({value} & 0) == 0 else 2",
    )


def _redundant_bit_mix(name: NameFactory, mask: int) -> tuple[str, ...]:
    left, right = name("opaque_left"), name("opaque_right")
    return (
        f"{left}, {right} = {hex(mask)}, ~{hex(mask)}",
        f"{left} = ({left} & {right}) | ({left} ^ {left})",
        f"{right} ^= {right}",
    )


LOW_READABILITY_TEMPLATES: tuple[TemplateRenderer, ...] = (
    _xor_cancellation,
    _subtraction_cancellation,
    _bounded_opaque_loop,
    _shift_and_clear,
    _opaque_boolean,
    _nested_false_branch,
    _opaque_branch,
    _single_cycle_loop,
    _opaque_ternary_chain,
    _redundant_bit_mix,
)
