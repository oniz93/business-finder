import time
from joblib import Parallel, delayed, parallel_backend

def cpu_intensive_task(i):
    print(f"Starting task {i}")
    # A simple CPU-intensive task
    result = sum(j * j for j in range(10000))
    print(f"Finished task {i}")
    return result

if __name__ == "__main__":
    n_tasks = 48  # More tasks than cores to ensure all cores are used
    print(f"Starting {n_tasks} CPU-intensive tasks...")
    
    start_time = time.time()
    
    # Use parallel_backend to ensure all cores are used
    with parallel_backend('loky', n_jobs=-1):
        results = Parallel()(delayed(cpu_intensive_task)(i) for i in range(n_tasks))
        
    end_time = time.time()
    
    print(f"All tasks completed in {end_time - start_time:.2f} seconds.")
    print(f"Number of results: {len(results)}")
