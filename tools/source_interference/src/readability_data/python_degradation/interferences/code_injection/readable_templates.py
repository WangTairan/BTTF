from __future__ import annotations

from collections.abc import Callable

NameFactory = Callable[[str], str]
TemplateRenderer = Callable[[NameFactory], tuple[str, ...]]


def _sum_small_sequence(name: NameFactory) -> tuple[str, ...]:
    total, number = name("running_total"), name("current_number")
    return (f"{total} = 0", f"for {number} in range(1, 6):", f"    {total} += {number}")


def _count_down(name: NameFactory) -> tuple[str, ...]:
    remaining = name("remaining_steps")
    return (f"{remaining} = 3", f"while {remaining} > 0:", f"    {remaining} -= 1")


def _count_even_numbers(name: NameFactory) -> tuple[str, ...]:
    count, number = name("even_number_count"), name("candidate_number")
    return (
        f"{count} = 0",
        f"for {number} in range(6):",
        f"    if {number} % 2 == 0:",
        f"        {count} += 1",
    )


def _choose_higher_score(name: NameFactory) -> tuple[str, ...]:
    first, second, higher = (
        name("first_score"),
        name("second_score"),
        name("higher_score"),
    )
    return (
        f"{first} = 72",
        f"{second} = 85",
        f"if {first} > {second}:",
        f"    {higher} = {first}",
        "else:",
        f"    {higher} = {second}",
    )


def _choose_lower_temperature(name: NameFactory) -> tuple[str, ...]:
    morning, evening, lower = (
        name("morning_temperature"),
        name("evening_temperature"),
        name("lower_temperature"),
    )
    return (
        f"{morning} = 18",
        f"{evening} = 14",
        f"{lower} = {morning}",
        f"if {evening} < {lower}:",
        f"    {lower} = {evening}",
    )


def _calculate_average_score(name: NameFactory) -> tuple[str, ...]:
    total, count, average = (
        name("total_score"),
        name("number_of_scores"),
        name("average_score"),
    )
    return (f"{total} = 240", f"{count} = 3", f"{average} = {total} / {count}")


def _calculate_small_factorial(name: NameFactory) -> tuple[str, ...]:
    factorial, factor = name("factorial"), name("current_factor")
    return (
        f"{factorial} = 1",
        f"for {factor} in range(2, 5):",
        f"    {factorial} *= {factor}",
    )


def _toggle_feature_state(name: NameFactory) -> tuple[str, ...]:
    enabled, count = name("feature_enabled"), name("toggle_count")
    return (
        f"{enabled} = False",
        f"for {count} in range(3):",
        f"    {enabled} = not {enabled}",
    )


def _advance_fibonacci_sequence(name: NameFactory) -> tuple[str, ...]:
    previous, current, step, following = (
        name("previous_number"),
        name("current_number"),
        name("sequence_step"),
        name("next_number"),
    )
    return (
        f"{previous} = 0",
        f"{current} = 1",
        f"for {step} in range(4):",
        f"    {following} = {previous} + {current}",
        f"    {previous} = {current}",
        f"    {current} = {following}",
    )


def _measure_travel_distance(name: NameFactory) -> tuple[str, ...]:
    start, end, distance = (
        name("starting_position"),
        name("ending_position"),
        name("travel_distance"),
    )
    return (
        f"{start} = 2",
        f"{end} = 9",
        f"{distance} = {end} - {start}",
        f"if {distance} < 0:",
        f"    {distance} = -{distance}",
    )


READABLE_TEMPLATES: tuple[TemplateRenderer, ...] = (
    _sum_small_sequence,
    _count_down,
    _count_even_numbers,
    _choose_higher_score,
    _choose_lower_temperature,
    _calculate_average_score,
    _calculate_small_factorial,
    _toggle_feature_state,
    _advance_fibonacci_sequence,
    _measure_travel_distance,
)
