from typing import List, Dict

def pareto_frontier(rows: List[Dict], x_key: str, y_key: str) -> List[Dict]:
    # Lower x is better (tokens), higher y is better (accuracy)
    # Keep rows where no other row has x <= and y >= with at least one strict inequality
    frontier = []
    for i, r in enumerate(rows):
        dominated = False
        for j, s in enumerate(rows):
            if i == j: 
                continue
            if (s.get(x_key, float('inf')) is not None and r.get(x_key, float('inf')) is not None):
                if (s[x_key] <= r[x_key]) and (s[y_key] >= r[y_key]) and ((s[x_key] < r[x_key]) or (s[y_key] > r[y_key])):
                    dominated = True
                    break
        if not dominated:
            frontier.append(r)
    return frontier
