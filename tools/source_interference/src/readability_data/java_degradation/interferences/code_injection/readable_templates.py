from __future__ import annotations

from collections.abc import Callable

NameFactory = Callable[[str], str]
TemplateRenderer = Callable[[NameFactory], str]


def _sum_small_sequence(name: NameFactory) -> str:
    running_total = name("runningTotal")
    current_number = name("currentNumber")
    return f"""
{{
  int {running_total} = 0;
  for (int {current_number} = 1; {current_number} <= 5; {current_number}++) {{
    {running_total} += {current_number};
  }}
}}
"""


def _count_down(name: NameFactory) -> str:
    remaining_steps = name("remainingSteps")
    return f"""
{{
  int {remaining_steps} = 3;
  while ({remaining_steps} > 0) {{
    {remaining_steps}--;
  }}
}}
"""


def _count_even_numbers(name: NameFactory) -> str:
    even_number_count = name("evenNumberCount")
    candidate_number = name("candidateNumber")
    return f"""
{{
  int {even_number_count} = 0;
  for (int {candidate_number} = 0; {candidate_number} < 6; {candidate_number}++) {{
    if ({candidate_number} % 2 == 0) {{
      {even_number_count}++;
    }}
  }}
}}
"""


def _choose_higher_score(name: NameFactory) -> str:
    first_score = name("firstScore")
    second_score = name("secondScore")
    higher_score = name("higherScore")
    return f"""
{{
  int {first_score} = 72;
  int {second_score} = 85;
  int {higher_score};
  if ({first_score} > {second_score}) {{
    {higher_score} = {first_score};
  }} else {{
    {higher_score} = {second_score};
  }}
}}
"""


def _choose_lower_temperature(name: NameFactory) -> str:
    morning_temperature = name("morningTemperature")
    evening_temperature = name("eveningTemperature")
    lower_temperature = name("lowerTemperature")
    return f"""
{{
  int {morning_temperature} = 18;
  int {evening_temperature} = 14;
  int {lower_temperature} = {morning_temperature};
  if ({evening_temperature} < {lower_temperature}) {{
    {lower_temperature} = {evening_temperature};
  }}
}}
"""


def _calculate_average_score(name: NameFactory) -> str:
    total_score = name("totalScore")
    number_of_scores = name("numberOfScores")
    average_score = name("averageScore")
    return f"""
{{
  int {total_score} = 240;
  int {number_of_scores} = 3;
  int {average_score} = {total_score} / {number_of_scores};
}}
"""


def _calculate_small_factorial(name: NameFactory) -> str:
    factorial = name("factorial")
    current_factor = name("currentFactor")
    return f"""
{{
  int {factorial} = 1;
  for (int {current_factor} = 2; {current_factor} <= 4; {current_factor}++) {{
    {factorial} *= {current_factor};
  }}
}}
"""


def _toggle_feature_state(name: NameFactory) -> str:
    feature_enabled = name("featureEnabled")
    toggle_count = name("toggleCount")
    return f"""
{{
  boolean {feature_enabled} = false;
  for (int {toggle_count} = 0; {toggle_count} < 3; {toggle_count}++) {{
    {feature_enabled} = !{feature_enabled};
  }}
}}
"""


def _advance_fibonacci_sequence(name: NameFactory) -> str:
    previous_number = name("previousNumber")
    current_number = name("currentNumber")
    sequence_step = name("sequenceStep")
    next_number = name("nextNumber")
    return f"""
{{
  int {previous_number} = 0;
  int {current_number} = 1;
  for (int {sequence_step} = 0; {sequence_step} < 4; {sequence_step}++) {{
    int {next_number} = {previous_number} + {current_number};
    {previous_number} = {current_number};
    {current_number} = {next_number};
  }}
}}
"""


def _measure_travel_distance(name: NameFactory) -> str:
    starting_position = name("startingPosition")
    ending_position = name("endingPosition")
    travel_distance = name("travelDistance")
    return f"""
{{
  int {starting_position} = 2;
  int {ending_position} = 9;
  int {travel_distance} = {ending_position} - {starting_position};
  if ({travel_distance} < 0) {{
    {travel_distance} = -{travel_distance};
  }}
}}
"""


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
