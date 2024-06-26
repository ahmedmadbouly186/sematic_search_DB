import numpy as np
from kmeans_lower_layer import VecDBKmeans
from LSH_upper_layer import VecDB
import time
from dataclasses import dataclass
from typing import List
import gc
from memory_profiler import memory_usage
import concurrent.futures
import os
AVG_OVERX_ROWS = 10


@dataclass
class Result:
    run_time: float
    top_k: int
    db_ids: List[int]
    actual_ids: List[int]


results = []


def run_queries(db, np_rows, top_k, num_runs):
    global results
    results = []
    rng = np.random.default_rng(100)

    for _ in range(num_runs):
        
        
        query = rng.random((1, 70))

        tic = time.time()
        db_ids = db.retrive(query, top_k)
        toc = time.time()
        run_time = toc - tic

        tic = time.time()
        actual_ids = (
            np.argsort(
                np_rows.dot(query.T).T
                / (np.linalg.norm(np_rows, axis=1) * np.linalg.norm(query)),
                axis=1,
            )
            .squeeze()
            .tolist()[::-1]
        )
        toc = time.time()
        np_run_time = toc - tic
        results.append(Result(run_time, top_k, db_ids, actual_ids))
    # return results


def memory_usage_run_queries(args):
    global results
    # This part is added to calcauate the RAM usage
    mem_before = max(memory_usage())
    mem = memory_usage(proc=(run_queries, args, {}), interval=1e-3)
    return results, max(mem) - mem_before


def eval(results: List[Result]):
    # scores are negative. So getting 0 is the best score.
    scores = []
    run_time = []
    for res in results:
        run_time.append(res.run_time)
        # case for retireving number not equal to top_k, socre will be the lowest
        if len(set(res.db_ids)) != res.top_k or len(res.db_ids) != res.top_k:
            scores.append(-1 * len(res.actual_ids) * res.top_k)
            continue
        score = 0
        for id in res.db_ids:
            try:
                ind = res.actual_ids.index(id)
                if ind > res.top_k * 3:
                    score -= ind
            except:
                score -= len(res.actual_ids)
        scores.append(score)

    return sum(scores) / len(scores), sum(run_time) / len(run_time)

def insert_level_2(db,index):
    # Assuming db is an instance of your database class
    db.insert_level_2(index)

if __name__ == "__main__":
    # create temp folder if not exists
    if not os.path.exists("temp"):
        os.makedirs("temp")
    threads = []
    record_num = 100000
    for i in range(1):
        rng = np.random.default_rng(50)
        db = VecDB(file_path="saved_db_10k.csv",new_db=True)
        records_np = rng.random((record_num, 70), dtype=np.float32)
        records_dict = [{"id": i, "embed": list(row)} for i, row in enumerate(records_np)]
        # _len = len(records_np)
        tic = time.time()
        db.insert_records(records_dict)
        # db.insert_records([], dic=False, rows_list=records_np)
        # db.insert_level_1(records_np)
        # db.insert_level_2(0)
        # db.insert_level_2(1)
        # db.insert_level_2(2)
        # db.insert_level_2(3)
        # db.insert_level_2(4)
        # db.insert_level_2(5)
        # db.insert_level_2(6)
        # db.insert_level_2(7)
        # num_threads = 4
        # with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        #     # Submit the tasks to the executor
        #     futures = [executor.submit(insert_level_2, db,i) for i in range(8)]

        #     # Wait for all tasks to complete
        #     concurrent.futures.wait(futures)

        toc = time.time()
        run_time = toc - tic
        print("insirtion time", run_time)
        run_queries(db, records_np, 5, 5)
        res, mem = memory_usage_run_queries((db, records_np, 5, 3))
        print(f"Record Number: {record_num} | Error from Exact Match: {eval(res)[0]} | Search Time: {eval(res)[1]} seconds | Memory Usage: {mem:.2f} MB")
        res, mem = memory_usage_run_queries((db, records_np, 5, 1))
        print(f"Record Number: {record_num} | Error from Exact Match: {eval(res)[0]} | Search Time: {eval(res)[1]} seconds | Memory Usage: {mem:.2f} MB")
        res, mem = memory_usage_run_queries((db, records_np, 5, 1))
        print(f"Record Number: {record_num} | Error from Exact Match: {eval(res)[0]} | Search Time: {eval(res)[1]} seconds | Memory Usage: {mem:.2f} MB")
