import networkx as nx

# Create indoor map as a graph
G = nx.Graph()

G.add_edges_from([
    ("Entrance", "Hall"),
    ("Hall", "Lab"),
    ("Hall", "Office"),
    ("Lab", "Exit"),
    ("Office", "Exit")
])

# Find shortest path
path = nx.shortest_path(G, source="Entrance", target="Lab")

print("Shortest path:", " -> ".join(path))
