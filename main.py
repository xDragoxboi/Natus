# Disclaimer : default values/events/factors are to be used for fun, this is strictly tuned for my needs in my project.
"""
Provides a population simulation engine including classes for managing
population dynamics and random events.
"""
import random
import math

class RandomEventType:
    """
    Represents a type of random event that can affect population dynamics.

    Attributes:
        name (str): The name of the random event type.
        occurrence_probability (float): The probability of this event occurring each week, if no other event is active.
        min_duration_weeks (int): The minimum duration of the event in weeks.
        max_duration_weeks (int): The maximum duration of the event in weeks.
        birth_factor_impact (float): Multiplier for the birth rate during the event.
        death_factor_impact (float): Multiplier for the death rate during the event.
        k_factor_impact (float): Multiplier for the carrying capacity during the event.
    """
    def __init__(self, name: str,
                 occurrence_probability: float,
                 min_duration_weeks: int, max_duration_weeks: int,
                 birth_factor_impact: float = 1.0,
                 death_factor_impact: float = 1.0,
                 k_factor_impact: float = 1.0):
        """
        Initializes a new RandomEventType.

        Args:
            name: The name of the event type.
            occurrence_probability: The probability (0.0 to 1.0) of this event occurring in a given week
                                      if no other event is active.
            min_duration_weeks: The minimum possible duration of the event in weeks.
            max_duration_weeks: The maximum possible duration of the event in weeks.
            birth_factor_impact: A multiplier affecting the birth rate while the event is active.
                                   Defaults to 1.0 (no impact).
            death_factor_impact: A multiplier affecting the death rate while the event is active.
                                   Defaults to 1.0 (no impact).
            k_factor_impact: A multiplier affecting the carrying capacity (K) while the event is active.
                               Defaults to 1.0 (no impact).

        Raises:
            ValueError: If occurrence_probability is not between 0.0 and 1.0, or if
                        min_duration_weeks is not positive, or if max_duration_weeks is less than min_duration_weeks.
        """
        if not (0.0 <= occurrence_probability <= 1.0):
            raise ValueError("Occurrence probability must be between 0.0 and 1.0.")
        if not (min_duration_weeks > 0 and max_duration_weeks >= min_duration_weeks):
            raise ValueError("Min/max duration weeks must be positive and max >= min.")

        self.name = name
        self.occurrence_probability = occurrence_probability
        self.min_duration_weeks = min_duration_weeks
        self.max_duration_weeks = max_duration_weeks
        self.birth_factor_impact = birth_factor_impact
        self.death_factor_impact = death_factor_impact
        self.k_factor_impact = k_factor_impact

    def __repr__(self):
        return (f"RandomEventType(name='{self.name}', "
                f"prob={self.occurrence_probability:.4f}, "
                f"duration=[{self.min_duration_weeks}-{self.max_duration_weeks}] weeks, "
                f"impacts(b:{self.birth_factor_impact}, d:{self.death_factor_impact}, k:{self.k_factor_impact}))")

class PopulationSimulator:
    """
    Simulates population changes over time based on various factors and events.

    This class models population dynamics using a logistic growth model modified
    by density-dependent birth and death rates, stochasticity, environmental factors,
    and random events.

    Attributes:
        P_current (float): The current population size.
        base_K (float): The base carrying capacity of the environment.
        b_base (float): The base per capita birth rate.
        d_base (float): The base per capita death rate.
        birth_density_exponent (float): Exponent controlling the density dependence of the birth rate.
        death_density_exponent (float): Exponent controlling the density dependence of the death rate.
        S_factor (float): Stochasticity factor, introducing random fluctuations.
        week_count (int): The number of weeks elapsed in the simulation.
        random_event_history (list): A log of random events that have occurred.
    """
    def __init__(self,
                 initial_population: float,
                 base_carrying_capacity: float,
                 base_birth_rate_per_capita: float = 0.007,
                 base_death_rate_per_capita: float = 0.002,
                 birth_density_exponent: float = 0.7,
                 death_density_exponent: float = 3.0,
                 stochasticity_factor: float = 0.0025,
                 possible_random_events: list[RandomEventType] = None,
                 thresholds: list[tuple[float, str, str]] = None):
        """
        Initializes the population simulator.

        Args:
            initial_population: The starting population size.
            base_carrying_capacity: The baseline carrying capacity (K) of the environment.
            base_birth_rate_per_capita: The per capita birth rate under ideal conditions (low density).
                                         Defaults to 0.007.
            base_death_rate_per_capita: The per capita death rate under ideal conditions (low density).
                                         Defaults to 0.002.
            birth_density_exponent: Exponent affecting how birth rate changes with density relative to K.
                                     Higher values mean birth rate drops more sharply as population approaches K.
                                     Defaults to 0.7.
            death_density_exponent: Exponent affecting how death rate changes with density relative to K.
                                     Higher values mean death rate climbs more sharply as population approaches/exceeds K.
                                     Defaults to 3.0.
            stochasticity_factor: A factor determining the magnitude of random Gaussian noise added to
                                   population changes each week. Defaults to 0.0025.
            possible_random_events: A list of `RandomEventType` objects that can occur during the simulation.
                                      Defaults to None (no random events).
            thresholds: A list of tuples, where each tuple defines a population threshold and associated
                        event names for when the population crosses this threshold (rising or falling).
                        Format: (population_value, "event_name_on_rise", "event_name_on_fall").
                        Defaults to None.

        Raises:
            ValueError: If base_carrying_capacity is not positive.
        """
        self.P_current = float(max(0.0, initial_population))
        if not base_carrying_capacity > 0:
            raise ValueError("Base Carrying Capacity (base_carrying_capacity) must be positive.")
        self.base_K = float(base_carrying_capacity)

        self.b_base = base_birth_rate_per_capita
        self.d_base = base_death_rate_per_capita
        self.birth_density_exponent = birth_density_exponent
        self.death_density_exponent = death_density_exponent
        self.S_factor = stochasticity_factor

        self._E_birth_factor = 1.0
        self._E_death_factor = 1.0
        self._E_k_factor = 1.0

        self._thresholds = []
        if thresholds:
            self.set_thresholds(thresholds)

        self.week_count = 0
        self._possible_random_events = possible_random_events if possible_random_events is not None else []
        self._active_random_event_details = None
        self.random_event_history = []

    def _calculate_weekly_change(self) -> float:
        calc_pop = max(0.0, self.P_current)
        if calc_pop == 0: return 0.0

        combined_birth_factor, combined_death_factor, combined_k_factor = self._get_combined_factors()
        current_K = self.base_K * combined_k_factor
        if current_K <= 0: current_K = 1.0

        base_birth_density_term = 1.0 - (calc_pop / current_K)
        density_birth_modifier = 0.0
        if base_birth_density_term > 0:
            density_birth_modifier = base_birth_density_term ** self.birth_density_exponent
        density_birth_modifier = max(0.0, density_birth_modifier)

        b_eff = self.b_base * density_birth_modifier * combined_birth_factor
        b_eff = max(0.0, b_eff)

        death_pressure_ratio = calc_pop / current_K
        density_death_modifier = (1.0 + death_pressure_ratio**self.death_density_exponent)
        d_eff = self.d_base * density_death_modifier * combined_death_factor
        d_eff = max(0.0, d_eff)

        num_births = calc_pop * b_eff
        num_deaths = calc_pop * d_eff
        delta_P_det = num_births - num_deaths

        delta_P_stoch = 0.0
        if self.S_factor > 0 and calc_pop > 0:
            std_dev = self.S_factor * calc_pop
            if std_dev > 0:
                 noise = random.normalvariate(0, std_dev)
                 delta_P_stoch = noise
        
        return delta_P_det + delta_P_stoch

    def set_thresholds(self, thresholds_list: list[tuple[float, str, str]]):
        """
        Sets or updates population thresholds that trigger named events.

        Each threshold is defined by a population value and two event names: one for when
        the population rises past the threshold, and one for when it falls below it.
        Thresholds are sorted by population value.

        Args:
            thresholds_list: A list of tuples. Each tuple should be in the format
                             (population_value: float, event_name_on_rise: str, event_name_on_fall: str).
                             Invalid entries will be skipped with a warning.
        """
        self._thresholds = []
        for t_val, t_name_rise, t_name_fall in thresholds_list:
            if not (isinstance(t_val, (int, float)) and isinstance(t_name_rise, str) and isinstance(t_name_fall, str)):
                print(f"Warning: Invalid threshold format for value {t_val}. Skipping.")
                continue
            self._thresholds.append((float(t_val), t_name_rise, t_name_fall))
        self._thresholds.sort(key=lambda x: x[0])

    def set_environmental_factors(self, birth_factor: float = None, death_factor: float = None, k_factor: float = None):
        """
        Sets manual environmental multipliers for birth rate, death rate, and carrying capacity.

        These factors are applied on top of any active random event impacts.
        If a factor is not provided (None), its current value remains unchanged.

        Args:
            birth_factor: Multiplier for the birth rate. E.g., 1.1 for a 10% increase.
            death_factor: Multiplier for the death rate. E.g., 0.9 for a 10% decrease.
            k_factor: Multiplier for the carrying capacity. E.g., 1.2 for a 20% increase.
        """
        if birth_factor is not None: self._E_birth_factor = float(birth_factor)
        if death_factor is not None: self._E_death_factor = float(death_factor)
        if k_factor is not None: self._E_k_factor = float(k_factor)

    def _check_for_random_event(self):
        if self._active_random_event_details:
            event_obj, weeks_left = self._active_random_event_details
            weeks_left -= 1
            if weeks_left <= 0:
                self._active_random_event_details = None
            else:
                self._active_random_event_details = (event_obj, weeks_left)
        
        if not self._active_random_event_details and self._possible_random_events:
            for event_type in self._possible_random_events:
                if random.random() < event_type.occurrence_probability:
                    duration = random.randint(event_type.min_duration_weeks, event_type.max_duration_weeks)
                    self._active_random_event_details = (event_type, duration)
                    self.random_event_history.append({
                        'name': event_type.name,
                        'start_week': self.week_count,
                        'end_week': self.week_count + duration,
                        'impacts': {
                            'birth': event_type.birth_factor_impact,
                            'death': event_type.death_factor_impact,
                            'k': event_type.k_factor_impact
                        }
                    })
                    break

    def _get_combined_factors(self) -> tuple[float, float, float]:
        birth_factor = self._E_birth_factor
        death_factor = self._E_death_factor
        k_factor = self._E_k_factor

        if self._active_random_event_details:
            event_obj, _ = self._active_random_event_details
            birth_factor *= event_obj.birth_factor_impact
            death_factor *= event_obj.death_factor_impact
            k_factor *= event_obj.k_factor_impact
        return birth_factor, death_factor, k_factor

    def advance_one_week(self) -> tuple[float, list[str]]:
        """
        Advances the simulation by one week.

        This method calculates the population change based on current conditions,
        updates the population, checks for random events, and identifies any
        triggered threshold events.

        Returns:
            A tuple containing:
                - P_current (float): The new population after the week's changes.
                - triggered_events (list[str]): A list of names of any threshold events
                                                triggered during this week.
        """
        self.week_count += 1
        P_previous = self.P_current
        self._check_for_random_event()
        
        delta_P_total = self._calculate_weekly_change()

        P_new = P_previous + delta_P_total
        self.P_current = max(0.0, P_new)

        triggered_events = []
        for value, name_rising, name_falling in self._thresholds:
            if P_previous < value <= self.P_current :
                triggered_events.append(name_rising)
            elif P_previous >= value > self.P_current:
                triggered_events.append(name_falling)
        
        return self.P_current, triggered_events

    def get_population(self) -> float:
        """Returns the current population size."""
        return self.P_current

    def get_week_count(self) -> int:
        """Returns the number of weeks elapsed in the simulation."""
        return self.week_count

    def get_current_carrying_capacity(self) -> float:
        """
        Calculates and returns the current effective carrying capacity.

        This considers the base carrying capacity and any active environmental
        or random event multipliers for K.

        Returns:
            The current effective carrying capacity.
        """
        _, _, combined_k_factor = self._get_combined_factors()
        return self.base_K * combined_k_factor

    def get_active_random_event(self) -> tuple[str, int] | None:
        """
        Gets details of the currently active random event, if any.

        Returns:
            A tuple (event_name: str, weeks_left: int) if an event is active.
            None otherwise.
        """
        if self._active_random_event_details:
            event_obj, weeks_left = self._active_random_event_details
            return event_obj.name, weeks_left
        return None

    def get_simulation_parameters(self) -> dict:
        """
        Retrieves a dictionary of the current simulation state and parameters.

        This is useful for logging, debugging, or displaying the simulation status.

        Returns:
            A dictionary containing key simulation parameters, including current population,
            carrying capacities (base and effective), birth/death rates, factor impacts,
            active random event details, and week count.
        """
        eff_birth, eff_death, eff_k = self._get_combined_factors()
        active_event_name, active_event_weeks = self.get_active_random_event() or (None, 0)
        return {
            "current_population": self.P_current,
            "base_carrying_capacity": self.base_K,
            "effective_carrying_capacity": self.base_K * eff_k,
            "base_birth_rate": self.b_base,
            "base_death_rate": self.d_base,
            "birth_density_exponent": self.birth_density_exponent,
            "death_density_exponent": self.death_density_exponent,
            "stochasticity_factor": self.S_factor,
            "manual_birth_factor": self._E_birth_factor,
            "manual_death_factor": self._E_death_factor,
            "manual_k_factor": self._E_k_factor,
            "active_combined_birth_factor": eff_birth,
            "active_combined_death_factor": eff_death,
            "active_combined_k_factor": eff_k,
            "active_random_event_name": active_event_name,
            "active_random_event_weeks_remaining": active_event_weeks,
            "week_count": self.week_count
                   }
