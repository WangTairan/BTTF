from __future__ import annotations

from collections.abc import Callable

NameFactory = Callable[[str], str]
TemplateRenderer = Callable[[NameFactory, int], str]


def _xor_cancellation(name: NameFactory, mask: int) -> str:
    value = name("opaqueValue")
    return (
        f"\n{{int {value}=0x{mask:X};{value}=(({value}^0x{mask:X})|0)&-1;"
        f"if((({value}&1)==1)){{{value}^={value};}}}}\n"
    )


def _subtraction_cancellation(name: NameFactory, mask: int) -> str:
    value = name("opaqueValue")
    return (
        f"\n{{int {value}=0x{mask:X}-0x{mask:X};"
        f"{value}=({value}==0)?({value}|0):({value}&0);}}\n"
    )


def _bounded_opaque_loop(name: NameFactory, mask: int) -> str:
    value = name("opaqueValue")
    index = name("opaqueIndex")
    return (
        f"\n{{int {value}=0,{index}=0;while({index}<2){{"
        f"{value}^=({index}<<1)^0x{mask & 0xF:X};{index}++;}}{value}^={value};}}\n"
    )


def _shift_and_clear(name: NameFactory, mask: int) -> str:
    value = name("opaqueValue")
    return (
        f"\n{{int {value}=0x{mask:X};{value}=({value}<<1)^({value}>>>1);{value}&=0;}}\n"
    )


def _opaque_boolean(name: NameFactory, mask: int) -> str:
    flag = name("opaqueFlag")
    return f"\n{{boolean {flag}=((0x{mask:X}^0x{mask:X})!=0);{flag}=!(!{flag});}}\n"


def _nested_false_branch(name: NameFactory, mask: int) -> str:
    value = name("opaqueValue")
    return (
        f"\n{{int {value}=0x{mask:X}^0x{mask:X};if({value}!=0){{"
        f"if((({value}|1)&1)==0){{{value}++;}}else{{{value}--;}}}}}}\n"
    )


def _opaque_switch(name: NameFactory, mask: int) -> str:
    state = name("opaqueState")
    return (
        f"\n{{int {state}=(0x{mask:X}^0x{mask:X});switch({state}){{"
        f"case 0:{state}|=0;break;default:{state}&=0;}}}}\n"
    )


def _single_cycle_do_while(name: NameFactory, mask: int) -> str:
    value = name("opaqueValue")
    guard = name("opaqueGuard")
    return (
        f"\n{{int {value}=0x{mask:X};boolean {guard}=true;do{{"
        f"{value}^=0x{mask:X};{guard}=false;}}while({guard});}}\n"
    )


def _opaque_ternary_chain(name: NameFactory, mask: int) -> str:
    value = name("opaqueValue")
    return (
        f"\n{{int {value}=0x{mask:X};{value}=(({value}&0)==0)?"
        f"((({value}^{value})==0)?0:1):2;}}\n"
    )


def _redundant_bit_mix(name: NameFactory, mask: int) -> str:
    left = name("opaqueLeft")
    right = name("opaqueRight")
    return (
        f"\n{{int {left}=0x{mask:X},{right}=~{left};"
        f"{left}=({left}&{right})|({left}^{left});{right}^={right};}}\n"
    )


LOW_READABILITY_TEMPLATES: tuple[TemplateRenderer, ...] = (
    _xor_cancellation,
    _subtraction_cancellation,
    _bounded_opaque_loop,
    _shift_and_clear,
    _opaque_boolean,
    _nested_false_branch,
    _opaque_switch,
    _single_cycle_do_while,
    _opaque_ternary_chain,
    _redundant_bit_mix,
)
