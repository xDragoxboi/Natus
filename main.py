# Disclaimer : default values/events/factors are to be used for fun, this is strictly tuned for my needs in my project.

import random
import math

class RandomEventType:
    def __init__(self, name: str,
                 occurrence_probability: float,
                 min_duration_weeks: int, max_duration_weeks: int,
                 birth_factor_impact: float = 1.0,
                 death_factor_impact: float = 1.0,
                 k_factor_impact: float = 1.0):
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
        self._thresholds = []
        for t_val, t_name_rise, t_name_fall in thresholds_list:
            if not (isinstance(t_val, (int, float)) and isinstance(t_name_rise, str) and isinstance(t_name_fall, str)):
                print(f"Warning: Invalid threshold format for value {t_val}. Skipping.")
                continue
            self._thresholds.append((float(t_val), t_name_rise, t_name_fall))
        self._thresholds.sort(key=lambda x: x[0])

    def set_environmental_factors(self, birth_factor: float = None, death_factor: float = None, k_factor: float = None):
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
        return self.P_current

    def get_week_count(self) -> int:
        return self.week_count

    def get_current_carrying_capacity(self) -> float:
        _, _, combined_k_factor = self._get_combined_factors()
        return self.base_K * combined_k_factor

    def get_active_random_event(self) -> tuple[str, int] | None:
        if self._active_random_event_details:
            event_obj, weeks_left = self._active_random_event_details
            return event_obj.name, weeks_left
        return None

    def get_simulation_parameters(self) -> dict:
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
