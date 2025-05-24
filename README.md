## Disclaimer: This README.md is AI work.


# Natus - Population Simulation Engine

## Introduction
Natus is a Python-based population simulation engine. It allows users to model population dynamics over time, incorporating factors like birth rates, death rates, carrying capacity, random events, and environmental modifiers. This engine can be used for simulations in games, ecological studies, or educational purposes.

## Features
*   Configurable base parameters (initial population, carrying capacity, birth/death rates).
*   Density-dependent birth and death rates.
*   Stochasticity factor for random population fluctuations.
*   Customizable random events that can impact birth/death rates and carrying capacity.
*   Environmental factor modifiers for birth/death rates and carrying capacity.
*   Population thresholds to trigger custom events or notifications.
*   Detailed simulation state tracking.

## Classes

### `RandomEventType`
Defines a template for random occurrences that can affect the simulation.

**Parameters:**
*   `name` (str): Name of the event.
*   `occurrence_probability` (float): Probability (0.0 to 1.0) of this event type being triggered in a week if no other event is active.
*   `min_duration_weeks` (int): Minimum duration of the event in weeks.
*   `max_duration_weeks` (int): Maximum duration of the event in weeks.
*   `birth_factor_impact` (float): Multiplier for the birth rate during the event. Defaults to 1.0.
*   `death_factor_impact` (float): Multiplier for the death rate during the event. Defaults to 1.0.
*   `k_factor_impact` (float): Multiplier for the carrying capacity during the event. Defaults to 1.0.

### `PopulationSimulator`
The main class that runs the population simulation.

**Core Initialization Parameters:**
*   `initial_population` (float): The starting population.
*   `base_carrying_capacity` (float): The baseline carrying capacity (K) of the environment.
*   `base_birth_rate_per_capita` (float): The per capita weekly birth rate under ideal conditions (e.g., low population density).
*   `base_death_rate_per_capita` (float): The per capita weekly death rate under ideal conditions.

**Other Important Parameters:**
*   `birth_density_exponent` (float): Controls how sharply the birth rate decreases as the population approaches carrying capacity.
*   `death_density_exponent` (float): Controls how sharply the death rate increases as the population approaches or exceeds carrying capacity.
*   `stochasticity_factor` (float): Introduces random Gaussian noise to the weekly population change.
*   `possible_random_events` (list[`RandomEventType`]): A list of `RandomEventType` objects that can occur during the simulation.
*   `thresholds` (list[tuple[float, str, str]]): Defines population levels that trigger named events when crossed (either rising or falling).

## Mathematical Model (Simplified Overview)
The simulation is based on a modified logistic growth model, processed in discrete weekly steps.

*   **Birth Rate:** The effective birth rate (`b_eff`) is calculated by: `b_base * (1 - P/K)^birth_density_exponent * combined_birth_factor`. It decreases as population (P) approaches carrying capacity (K).
*   **Death Rate:** The effective death rate (`d_eff`) is calculated by: `d_base * (1 + (P/K)^death_density_exponent) * combined_death_factor`. It increases as population exceeds or significantly pressures carrying capacity.
*   **Population Change:** The deterministic change in population for a week is `P * (b_eff - d_eff)`. A stochastic element, scaled by `stochasticity_factor`, is added to this for randomness.
*   **Factors:** The `combined_birth_factor`, `combined_death_factor`, and `combined_k_factor` are products of manually set environmental factors and active random event impacts.

## Usage

### Basic Example
```python
from main import PopulationSimulator, RandomEventType

# Basic setup
sim = PopulationSimulator(initial_population=1000, base_carrying_capacity=5000)

# Run for a few weeks
for week in range(10):
    population, events = sim.advance_one_week()
    print(f"Week: {sim.get_week_count()}, Population: {population:.0f}, Events: {events}")
```

### Detailed Examples
For more detailed examples, including setup of random events, thresholds, environmental factors, and inspecting simulation parameters, please see the `usage.py` file included in this repository.

## Warhammer 2 Orc Poem
WAAAGH! by da green tide, we come to smash!
Stompin' da stunties, hear da bones crash!
Big 'uns and choppas, filled wif pure might,
Paintin' da whole world green, day and through night!
Gork an' Mork watchin', grinnin' wif glee,
Dis here's da best fight, for all Orcs, y'see!
So grab yer best chopper, let out a great roar,
Time for da WAAAGH!, and then WAAAGH! some more!

## Contributing
We welcome contributions to improve and expand this collection of math operators. If you have new functions or find improvements to existing ones, please follow these steps:

1.  Fork the repository.
2.  Create a new branch.
3.  Make your changes, including clear comments and tests (if applicable).
4.  Submit a pull request for review.

## License
This project is licensed under the MIT License - see the LICENSE file for details.
