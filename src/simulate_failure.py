import matplotlib
import networkx
from topology import graph, graph_modified
from calculate_paths import primary_path, backup_path

failed_graph = graph.copy()

#example: the link between Stord and UiB Høyteklogibygget has failed
failed_u = primary_path[0]
failed_v = primary_path[1]

failed_graph.remove_edge(failed_u, failed_v)
# print("Failed link: ", failed_u, failed_v)


def check_backup_path():
    if backup_path is not None:
        backup_available = True

        for i in range(len(backup_path)-1):
            u = backup_path[i]
            v = backup_path[i+1]

            if not failed_graph.has_edge(u, v):
                backup_available = False
                break

        print("Bakcup available: ", backup_available)
        return backup_available


