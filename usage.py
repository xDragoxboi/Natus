"""
Example usage of the PopulationSimulator and RandomEventType classes from main.py.
This script demonstrates how to initialize the simulator, define random events,
set thresholds, adjust environmental factors, run the simulation, and retrieve information.
"""

import random
from main import PopulationSimulator, RandomEventType

def run_simulation_example():
    """
    Runs a demonstration of the population simulator.
    """
    print("--- Population Simulation Example ---")

    # 1. Example Initialization of RandomEventType
    print("\n--- 1. Defining Random Event Types ---")
    good_harvest = RandomEventType(
        name="Good Harvest",
        occurrence_probability=0.1, # 10% chance per week if no other event is active
        min_duration_weeks=4,
        max_duration_weeks=8,
        birth_factor_impact=1.5,  # 50% increase in birth rate
        death_factor_impact=0.9,  # 10% decrease in death rate
        k_factor_impact=1.2       # 20% increase in carrying capacity
    )
    print(f"Created: {good_harvest}")

    plague = RandomEventType(
        name="Plague",
        occurrence_probability=0.05, # 5% chance per week
        min_duration_weeks=10,
        max_duration_weeks=20,
        birth_factor_impact=0.8,  # 20% decrease in birth rate
        death_factor_impact=2.0,  # 100% increase in death rate (doubles)
        k_factor_impact=0.7       # 30% decrease in carrying capacity
    )
    print(f"Created: {plague}")

    mild_winter = RandomEventType(
        name="Mild Winter",
        occurrence_probability=0.15,
        min_duration_weeks=6,
        max_duration_weeks=12,
        death_factor_impact=0.85, # 15% decrease in death rate
        k_factor_impact=1.05      # 5% increase in K
    )
    print(f"Created: {mild_winter}")

    possible_events = [good_harvest, plague, mild_winter]
    print(f"Possible events list: {possible_events}")

    # 2. Example Initialization of PopulationSimulator
    print("\n--- 2. Initializing Population Simulator ---")
    initial_pop = 1000.0
    base_k = 2000.0
    base_birth_rate = 0.01  # 1% per capita per week
    base_death_rate = 0.005 # 0.5% per capita per week

    simulator = PopulationSimulator(
        initial_population=initial_pop,
        base_carrying_capacity=base_k,
        base_birth_rate_per_capita=base_birth_rate,
        base_death_rate_per_capita=base_death_rate,
        birth_density_exponent=0.7,
        death_density_exponent=3.0,
        stochasticity_factor=0.005, # Slightly higher stochasticity for more visible random walks
        possible_random_events=possible_events
    )
    print(f"Simulator initialized with P={simulator.get_population()}, K_base={simulator.base_K}")

    # 3. Demonstrate Setting Thresholds
    print("\n--- 3. Setting Population Thresholds ---")
    thresholds = [
        (1500.0, "Population Boom Reached (1500)", "Population Decline below 1500"),
        (2500.0, "Major Population Surge (2500)", "Population Drop below 2500"),
        (500.0, "Population Low (500)", "Population Recovering above 500")
    ]
    simulator.set_thresholds(thresholds)
    print(f"Thresholds set: {simulator._thresholds}") # Accessing internal for demo, normally not done

    # 4. Demonstrate Setting Environmental Factors
    print("\n--- 4. Setting Initial Environmental Factors ---")
    # Example: Start with a slight boost to carrying capacity
    simulator.set_environmental_factors(k_factor=1.1)
    print(f"Initial manual environmental factors: Birth={simulator._E_birth_factor}, Death={simulator._E_death_factor}, K={simulator._E_k_factor}")
    print(f"Effective K after manual adjustment: {simulator.get_current_carrying_capacity():.2f}")

    # 5. Simulate Weekly Advancement
    print("\n--- 5. Simulating Weekly Advancement ---")
    num_weeks_to_simulate = 100
    print(f"Simulating for {num_weeks_to_simulate} weeks...")

    for week in range(1, num_weeks_to_simulate + 1):
        current_population_before_advance = simulator.get_population()
        population_after_advance, triggered_threshold_events = simulator.advance_one_week()

        print_interval = 10 # Print detailed info every 10 weeks
        if week % print_interval == 0 or week == 1 or triggered_threshold_events or simulator.get_active_random_event():
            print(f"\n--- Week {simulator.get_week_count()} ---")
            print(f"Population: {current_population_before_advance:.2f} -> {population_after_advance:.2f}")
            print(f"Effective Carrying Capacity: {simulator.get_current_carrying_capacity():.2f}")

            active_event = simulator.get_active_random_event()
            if active_event:
                print(f"Active Random Event: {active_event[0]} (Weeks remaining: {active_event[1]})")
            else:
                print("No active random event.")

            if triggered_threshold_events:
                print(f"Triggered Threshold Events: {', '.join(triggered_threshold_events)}")

        # Example of changing environmental factors mid-simulation
        if simulator.get_week_count() == 25:
            print("\n*** Mid-simulation change: Applying a manual reduction in birth rate at week 25 ***")
            simulator.set_environmental_factors(birth_factor=0.9) # 10% reduction
            print(f"New manual birth factor: {simulator._E_birth_factor}")
        
        if simulator.get_week_count() == 50:
            print("\n*** Mid-simulation change: Removing manual factors at week 50 (resetting to 1.0) ***")
            simulator.set_environmental_factors(birth_factor=1.0, death_factor=1.0, k_factor=1.0)
            print(f"Manual factors reset. K_eff: {simulator.get_current_carrying_capacity():.2f}")


        if population_after_advance == 0:
            print(f"\nPopulation reached 0 at week {simulator.get_week_count()}. Simulation ended.")
            break
    
    print(f"\n--- Simulation Ended after {simulator.get_week_count()} weeks ---")

    # 6. Demonstrate Getter Methods (beyond what's used in the loop)
    print("\n--- 6. Demonstrating Getter Methods (Post-Simulation) ---")
    print(f"Final Population: {simulator.get_population():.2f}")
    print(f"Total Weeks Simulated: {simulator.get_week_count()}")
    
    active_event_final = simulator.get_active_random_event()
    if active_event_final:
        print(f"Final Active Random Event: {active_event_final[0]} (Weeks remaining: {active_event_final[1]})")
    else:
        print("No random event active at the end.")

    print("\n--- Full Simulation Parameters at End ---")
    final_params = simulator.get_simulation_parameters()
    for key, value in final_params.items():
        if isinstance(value, float):
            print(f"{key}: {value:.4f}")
        else:
            print(f"{key}: {value}")

    print("\n--- Random Event History ---")
    if simulator.random_event_history:
        for i, event_record in enumerate(simulator.random_event_history):
            print(f"Event {i+1}: {event_record['name']} (Weeks {event_record['start_week']}-{event_record['end_week']}) "
                  f"Impacts: B={event_record['impacts']['birth']:.2f}, D={event_record['impacts']['death']:.2f}, K={event_record['impacts']['k']:.2f}")
    else:
        print("No random events occurred during the simulation.")

    print("\n--- Example Completed ---")

if __name__ == "__main__":
    # Set a seed for reproducibility of the random aspects in this example run
    random.seed(42)
    run_simulation_example()
