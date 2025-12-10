# benchmark.py
import time
import random
import models
import solvers
import game_logic as gl
import settings
import threading

def run_benchmark_gui(num_runs, node_limit, log_callback, on_finish):
    # Run benchmark in a separate thread to avoid blocking the UI
    def task():
        log_callback(f"{'='*60}\n")
        log_callback(f"BENCHMARK STARTED\n")
        log_callback(f"Games: {num_runs} | Node Limit: {node_limit}\n")
        log_callback(f"{'='*60}\n")

        results = {
            "DFS": {"wins": 0, "total_time": 0, "total_steps": 0, "timeouts": 0},
            "A*":  {"wins": 0, "total_time": 0, "total_steps": 0, "timeouts": 0}
        }

        for seed in range(num_runs):
            log_callback(f"Game {seed+1}/{num_runs}...")
            
            # --- Run DFS ---
            random.seed(seed)
            deck = models.create_deck()
            p, s, w, f = deck[:28], deck[28:], ["**"], []
            
            t0 = time.time()
            sol_dfs = solvers.find_solution_dfs(p, s, w, f) 
            t1 = time.time()
            
            if sol_dfs:
                results["DFS"]["wins"] += 1
                results["DFS"]["total_steps"] += len(sol_dfs)
                results["DFS"]["total_time"] += (t1 - t0)
            else:
                results["DFS"]["timeouts"] += 1
                results["DFS"]["total_time"] += (t1 - t0)

            # --- Run A* ---
            random.seed(seed)
            deck = models.create_deck()
            p, s, w, f = deck[:28], deck[28:], ["**"], []

            t0 = time.time()
            sol_astar = solvers.find_solution_astar(p, s, w, f)
            t1 = time.time()

            if sol_astar:
                results["A*"]["wins"] += 1
                results["A*"]["total_steps"] += len(sol_astar)
                results["A*"]["total_time"] += (t1 - t0)
            else:
                results["A*"]["timeouts"] += 1
                results["A*"]["total_time"] += (t1 - t0)
            
            # Print brief status for this run
            dfs_status = "Win" if sol_dfs else "Fail"
            astar_status = "Win" if sol_astar else "Fail"
            log_callback(f" [DFS: {dfs_status}, A*: {astar_status}]\n")

        # --- Final Report ---
        log_callback(f"\n{'='*60}\n")
        log_callback(f"{'METRIC':<15} | {'DFS':<15} | {'A* (Heuristic)':<15}\n")
        log_callback(f"{'-'*60}\n")

        for algo in ["DFS", "A*"]:
            wins = results[algo]["wins"]
            avg_time = results[algo]["total_time"] / num_runs
            avg_steps = results[algo]["total_steps"] / wins if wins > 0 else 0
            
            results[algo]["avg_time"] = avg_time
            results[algo]["avg_steps"] = avg_steps

        # Formatting Strings
        row_wins = f"{results['DFS']['wins']}/{num_runs} ({results['DFS']['wins']/num_runs*100:.1f}%)"
        row_wins_a = f"{results['A*']['wins']}/{num_runs} ({results['A*']['wins']/num_runs*100:.1f}%)"
        
        log_callback(f"{'Win Rate':<15} | {row_wins:<15} | {row_wins_a:<15}\n")
        log_callback(f"{'Avg Time':<15} | {results['DFS']['avg_time']:.4f} s        | {results['A*']['avg_time']:.4f} s\n")
        log_callback(f"{'Avg Steps':<15} | {results['DFS']['avg_steps']:.1f}           | {results['A*']['avg_steps']:.1f}\n")
        log_callback(f"{'='*60}\n")
        log_callback("DONE.")
        
        if on_finish:
            on_finish()

    # Start the thread
    threading.Thread(target=task, daemon=True).start()