import random
from collections import deque

def get_topologic_order(vertices, graph):

    # Grau de entrada (in-degree): número de arestas que CHEGAM no vértice
    in_degree = {vertex: 0 for vertex in vertices}
    for adjacent_list in graph.values():
        for adjacent_vertex in adjacent_list:
            in_degree[adjacent_vertex] += 1
 
    queue = deque([vertex for vertex in vertices if in_degree[vertex] == 0])
    topologic_order = []
 
    while queue:
        first_out_vertex = queue.popleft()
        topologic_order.append(first_out_vertex)
 
        for vertex in graph[first_out_vertex]:
            in_degree[vertex] -= 1
            if in_degree[vertex] == 0:
                queue.append(vertex)
 
    if len(topologic_order) != len(vertices):
        raise ValueError("graph contains a cycle!")
 
    return topologic_order


def get_large_constant(graph, grid_width, grid_height):
    number_of_nets = sum(1 for destinations in graph.values() if destinations)
    return number_of_nets * (grid_width + grid_height) + 1
 
 
def get_occupied_cells(individual, vertices, cfu_count):
    occupied_cells = []
    for vertex, (column, row) in zip(vertices, individual):
        width = max(1, cfu_count[vertex])
        for offset in range(width):
            occupied_cells.append((column + offset, row))
    return occupied_cells


def has_shared_position(individual, vertices, cfu_count):
    occupied_cells = get_occupied_cells(individual, vertices, cfu_count)
    return len(set(occupied_cells)) != len(occupied_cells)
 
 
def get_edge_cost(source, destination, positions, cfu_count):
    source_column, source_row = positions[source]
    destination_column, destination_row = positions[destination]

    # a saída de uma cadeia de CFUs é a última célula; a entrada do destino é a primeira
    source_exit_column = source_column + max(1, cfu_count[source]) - 1

    # manhattan distance
    wire_length = abs(source_exit_column - destination_column) + abs(source_row - destination_row)
    return wire_length + cfu_count[source]
 
 
def get_critical_path_cost(positions, graph, cfu_count, topologic_order):
    longest_distance = {vertex: 0 for vertex in topologic_order}
 
    for source in topologic_order:
        for destination in graph[source]:
            candidate = longest_distance[source] + get_edge_cost(source, destination, positions, cfu_count)
            if candidate > longest_distance[destination]:
                longest_distance[destination] = candidate
 
    # (graph[vertex] == []) é o mesmo que (not graph[vertex]), verifica se o vertice é output.
    return max(longest_distance[vertex] for vertex in topologic_order if not graph[vertex])
 
 
def get_total_bounding_box_cost(positions, graph):
    total_bounding_box_cost = 0
    for source, destinations in graph.items():
        if not destinations:
            continue

        net = [source] + destinations

        columns = [positions[vertex][0] for vertex in net]
        rows = [positions[vertex][1] for vertex in net]

        total_bounding_box_cost += (max(columns) - min(columns)) + (max(rows) - min(rows))
    return total_bounding_box_cost


def gera_dag(seed, n_in, n_out, n_camadas, tam_camada, malha_largura, malha_altura, max_fan_in=4):
    """Gera um DAG em camadas: toda aresta sai de uma camada e chega numa
    camada mais à frente, logo ciclos são impossíveis. Cada vértice recebe
    de 1 a max_fan_in pais de camadas anteriores.
    Retorna (vertices, graph, cfu_count, vertices_fixos)."""
    rng = random.Random(seed)

    layers = [[f'IN{i}' for i in range(n_in)]]
    for c in range(n_camadas):
        layers.append([f'U{c}_{j}' for j in range(tam_camada)])
    layers.append([f'OUT{i}' for i in range(n_out)])

    vertices = [v for camada in layers for v in camada]
    graph = {v: [] for v in vertices}
    fan_in = {v: 0 for v in vertices}

    # passo 1: sorteia os pais (entradas) de cada vértice fora da camada 0
    for li in range(1, len(layers)):
        for v in layers[li]:
            k = rng.randint(1, max_fan_in)
            pais = set()
            while len(pais) < k:
                # 70% dos pais vêm da camada imediatamente anterior;
                # 30% de qualquer camada anterior (aresta que "pula" camada)
                if rng.random() < 0.7:
                    camada_pai = layers[li - 1]
                else:
                    camada_pai = rng.choice(layers[:li])
                pais.add(rng.choice(camada_pai))
            for p in pais:
                graph[p].append(v)
            fan_in[v] = len(pais)

    # passo 2: garante >= 1 filho para todo vértice fora da última camada,
    # senão ele viraria uma saída extra (subgrafo desconexo)
    for li in range(len(layers) - 1):
        for v in layers[li]:
            if not graph[v]:
                for lj in range(li + 1, len(layers)):
                    candidatos = [u for u in layers[lj] if fan_in[u] < max_fan_in]
                    if candidatos:
                        alvo = rng.choice(candidatos)
                        graph[v].append(alvo)
                        fan_in[alvo] += 1
                        break
                else:
                    raise RuntimeError('sem capacidade de fan-in nas camadas à frente')

    # I/O não tem CFU; vértices internos têm cadeias de 1 a 10 células
    cfu_count = {}
    for li, camada in enumerate(layers):
        for v in camada:
            cfu_count[v] = 0 if li == 0 or li == len(layers) - 1 else rng.randint(1, 10)

    # entradas espalhadas no topo, saídas na base (fixas)
    vertices_fixos = {}
    for i, v in enumerate(layers[0]):
        vertices_fixos[v] = (int((i + 0.5) * malha_largura / n_in), 0)
    for i, v in enumerate(layers[-1]):
        vertices_fixos[v] = (int((i + 0.5) * malha_largura / n_out), malha_altura - 1)

    return vertices, graph, cfu_count, vertices_fixos


def problema_complexo(seed=7, malha_largura=100, malha_altura=100,
                      n_in=8, n_out=6, n_camadas=12, tam_camada=10, max_fan_in=4):
    """Problema grande: malha 100x100 com DAG gerada em camadas
    (134 vértices por padrão: 8 entradas + 12x10 internos + 6 saídas,
    fan-in até max_fan_in). Seed fixa -> grafo reproduzível."""
    vertices, graph, cfu_count, vertices_fixos = gera_dag(
        seed, n_in, n_out, n_camadas, tam_camada,
        malha_largura, malha_altura, max_fan_in)
    return {
        'malha_largura': malha_largura,
        'malha_altura': malha_altura,
        'vertices': vertices,
        'graph': graph,
        'cfu_count': cfu_count,
        'vertices_fixos': vertices_fixos
    }

