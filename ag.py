import random
import numpy as np
import matplotlib.pyplot as plt

from typing import Final
from directed_graph import get_topologic_order, get_total_bounding_box_cost, get_critical_path_cost, get_large_constant, has_shared_position, problema_complexo

"""
Representation of a directed graph
"""

MALHA_LARGURA = 5
MALHA_ALTURA = 5

VERTICES = ['A', 'B', 'C', 'D']

# Tree representation in adjacency list
GRAPH = {
    'A': ['B', 'C'],
    'B': ['C', 'D'],
    'C': ['D'],
    'D': []
}

CFU_COUNT = {'A': 0, 'B': 1, 'C': 3, 'D': 0}
VERTICES_FIXOS = {'A': (2, 0), 'D': (2, MALHA_ALTURA - 1)}

COMPLEXO = False
VERBOSE: Final[bool] = not COMPLEXO

# A posição do vértice será uma tupla (x,y) e cada individuo tem a mesma quantidade de posições de vértices
TAM_CROMO: Final[int] = len(VERTICES)
TAM_POP: Final[int] = TAM_CROMO * 2 if not COMPLEXO else 150
N_GERACOES: Final[int] = 30 if not COMPLEXO else 2000
GERACOES_PARADA: Final[int] = 15 if not COMPLEXO else 100
TAXA_MUTACAO: Final[float] = 0.5

pop = [[(0, 0)] * TAM_CROMO for _ in range(TAM_POP)]
nova_pop = [[(0, 0)] * TAM_CROMO for _ in range(TAM_POP)]
pais = [[(0, 0)] * TAM_CROMO for _ in range(2)]
filhos = [[(0, 0)] * TAM_CROMO for _ in range(2)]
nota_pop = np.zeros((TAM_POP, 3))


def init_pop():
    global pop
    pop = [individuo_aleatorio() for _ in range(TAM_POP)]
    

def avalia_pop():
    global nota_pop
    soma_apt = 0

    topologic_order = get_topologic_order(VERTICES, GRAPH)
    large_constant = get_large_constant(GRAPH, MALHA_LARGURA, MALHA_ALTURA)

    for index_individuo in range(TAM_POP):
        apt = 0
        individuo = pop[index_individuo]

        # penalidade
        if has_shared_position(individuo, VERTICES, CFU_COUNT):
            apt = float('inf')
        else:
            positions = dict(zip(VERTICES, individuo))

            critical_path_cost = get_critical_path_cost(positions, GRAPH, CFU_COUNT, topologic_order)
            total_bounding_box_cost = get_total_bounding_box_cost(positions, GRAPH)

            total_cost = critical_path_cost * large_constant + total_bounding_box_cost
            apt = total_cost

        nota_pop[index_individuo][0] = index_individuo
        nota_pop[index_individuo][1] = apt
        nota_pop[index_individuo][2] = -1

        # descarta apts que sofreram penalidade
        if apt < float('inf'):
            soma_apt = soma_apt + apt

    minsum = 0
    nota_pop = nota_pop[nota_pop[:, 1].argsort()]
    
    for index_individuo in range(TAM_POP):
        if (soma_apt > 0) and (nota_pop[index_individuo][1] > 0):
            nota_pop[index_individuo][2] = ((1 / nota_pop[index_individuo][1]) / soma_apt) * 100
        else:
            nota_pop[index_individuo][2] = 0
        minsum = minsum + nota_pop[index_individuo][2]
    
    for i in range(TAM_POP):
        if(minsum > 0):
            nota_pop[i][2] = nota_pop[i][2] / minsum
        else:
            nota_pop[i][2] = 0


def seleciona_pais():
    global pais
    r_pai1 = random.random()
    r_pai2 = random.random()
 
    acum = 0
    for i in range(TAM_POP):
        acum = acum + nota_pop[i][2]
        if acum >= r_pai1:
            pais[0] = list(pop[int(nota_pop[i][0])])
            break
    else:
        pais[0] = list(pop[int(nota_pop[0][0])])
 
    acum = 0
    for i in range(TAM_POP):
        acum = acum + nota_pop[i][2]
        if acum >= r_pai2:
            pais[1] = list(pop[int(nota_pop[i][0])])
            break
    else:
        pais[1] = list(pop[int(nota_pop[0][0])])


def cruza_pais():
    global filhos

    r_cruza = random.random()
    if(r_cruza < 0.80):
        corte = random.randint(0, TAM_CROMO - 1)   
        filhos[0][:corte] = pais[0][:corte]
        filhos[0][corte:] = pais[1][corte:]
        filhos[1][corte:] = pais[0][corte:]
        filhos[1][:corte] = pais[1][:corte]
    else:
        filhos[0] = pais[0]
        filhos[1] = pais[1]


def muta_filhos():
    global filhos

    for i in range(TAM_CROMO):
        r_muta = random.random()
        if(r_muta < TAXA_MUTACAO):
            filhos[0][i] = posicao_aleatoria(VERTICES[i])

    for i in range(TAM_CROMO):
        r_muta = random.random()
        if(r_muta < TAXA_MUTACAO):
            filhos[1][i] = posicao_aleatoria(VERTICES[i])


def elitismo(qtde):
    global nova_pop
    for i in range(qtde):
        nova_pop[i] = pop[int(nota_pop[i][0])].copy()


def imprime_pop():
    for index, individuo in enumerate(pop):
        print(f"individuo ({index}): {individuo}")


def imprime_nota_pop():
    acum = 0 
    for i in range(TAM_POP):
        acum = acum + nota_pop[i][2]
        print('Individuo: ', nota_pop[i][0], '- Nota: ', nota_pop[i][1], '- (%): ', nota_pop[i][2], ' - Acum: ', acum)


def imprime_melhor():
    melhor = pop[int(nota_pop[0][0])]
    positions = dict(zip(VERTICES, melhor))
    topologic_order = get_topologic_order(VERTICES, GRAPH)
    caminho_critico = get_critical_path_cost(positions, GRAPH, CFU_COUNT, topologic_order)
    bbox_total = get_total_bounding_box_cost(positions, GRAPH)
    print(f'>> Melhor: {melhor} - Nota: {nota_pop[0][1]}'
          f' (caminho crítico: {caminho_critico}, bounding box: {bbox_total})'
          f' - (%): {nota_pop[0][2]}')


def posicao_aleatoria(vertex):
    if vertex in VERTICES_FIXOS:
        return VERTICES_FIXOS[vertex]

    width = max(1, CFU_COUNT[vertex])
    x = random.randint(0, MALHA_LARGURA - width)
    y = random.randint(1, MALHA_ALTURA - 2)
    return (x, y)


def individuo_aleatorio():
    while True:
        individual = [posicao_aleatoria(vertex) for vertex in VERTICES]
        if not has_shared_position(individual, VERTICES, CFU_COUNT):
            return individual


def plota_melhor(individuo):
    positions = dict(zip(VERTICES, individuo))
    malha_grande = max(MALHA_LARGURA, MALHA_ALTURA) > 50
    fig, ax = plt.subplots(figsize=(10, 10))
 
    for vertex, (x, y) in positions.items():
        width = max(1, CFU_COUNT[vertex])
        ax.add_patch(plt.Rectangle((x, y), width, 1, alpha=0.4))
        ax.text(x + width / 2, y + 0.5, vertex, ha='center', va='center',
                fontsize=4 if malha_grande else 10)

    cmap = plt.get_cmap('tab10')
    total_bbox = 0
    net_index = 0

    for source, destinations in GRAPH.items():
        if not destinations:
            continue

        cor = cmap(net_index % 10)
        net_index += 1

        net = [source] + destinations
        min_x = min(positions[v][0] for v in net)
        max_x = max(positions[v][0] for v in net)
        min_y = min(positions[v][1] for v in net)
        max_y = max(positions[v][1] for v in net)

        bbox_cost = (max_x - min_x) + (max_y - min_y)
        total_bbox += bbox_cost

        if not malha_grande:
            pad = net_index * 0.07
            ax.add_patch(plt.Rectangle((min_x + pad, min_y + pad),
                                       max_x - min_x + 1 - 2 * pad,
                                       max_y - min_y + 1 - 2 * pad,
                                       fill=False, ls='--', edgecolor=cor,
                                       lw=1.5))
            ax.plot([], [], color=cor, ls='--', lw=1.5,
                    label=f'{source}→{{{",".join(destinations)}}}: {bbox_cost}')

        for dest in destinations:
            sx, sy = positions[source]
            dx, dy = positions[dest]
            ax.annotate('', xy=(dx + 0.5, dy + 0.5), xytext=(sx + 0.5, sy + 0.5),
                        arrowprops=dict(arrowstyle='->', color=cor,
                                        lw=0.4 if malha_grande else 1.5,
                                        alpha=0.5 if malha_grande else 1.0))

    topologic_order = get_topologic_order(VERTICES, GRAPH)
    large_constant = get_large_constant(GRAPH, MALHA_LARGURA, MALHA_ALTURA)
    caminho_critico = get_critical_path_cost(positions, GRAPH, CFU_COUNT, topologic_order)
    fitness = caminho_critico * large_constant + total_bbox

    ax.set_title(f'fitness: {fitness:.0f} = caminho crítico {caminho_critico}'
                 f' × {large_constant:.0f} + bounding box {total_bbox}')
    if not malha_grande:
        ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1.0), fontsize=9,
                  title='bounding box por net')
    ax.set_xlim(0, MALHA_LARGURA)
    ax.set_ylim(0, MALHA_ALTURA)
    ax.invert_yaxis()

    ax.set_xticks(range(MALHA_LARGURA + 1))
    ax.set_yticks(range(MALHA_ALTURA + 1))

    if malha_grande:
        ax.tick_params(axis='x', labelsize=3, labelrotation=90)
        ax.tick_params(axis='y', labelsize=3)

    ax.grid(True)
    plt.savefig('melhor.png', bbox_inches='tight', dpi=300 if malha_grande else 150)
    plt.close()


if(__name__ == '__main__'):
    if COMPLEXO:
        problema = problema_complexo()
        MALHA_LARGURA = problema['malha_largura']
        MALHA_ALTURA = problema['malha_altura']
        VERTICES = problema['vertices']
        GRAPH = problema['graph']
        CFU_COUNT = problema['cfu_count']
        VERTICES_FIXOS = problema['vertices_fixos']
        TAM_CROMO = len(VERTICES)
        pop = [[(0, 0)] * TAM_CROMO for _ in range(TAM_POP)]
        nova_pop = [[(0, 0)] * TAM_CROMO for _ in range(TAM_POP)]
        pais = [[(0, 0)] * TAM_CROMO for _ in range(2)]
        filhos = [[(0, 0)] * TAM_CROMO for _ in range(2)]
        nota_pop = np.zeros((TAM_POP, 3))

    init_pop()
    if VERBOSE:
        imprime_pop()

    melhor_fitness = float('inf')
    geracoes_estagnadas = 0
    for i in range(N_GERACOES):
        print('GERAÇÃO: ', i)
        avalia_pop()

        if VERBOSE:
            imprime_nota_pop()
        else:
            print('  melhor fitness:', nota_pop[0][1])

        #criterio de parada
        if (nota_pop[0][1] < melhor_fitness):
            melhor_fitness = nota_pop[0][1]
            geracoes_estagnadas = 0
        else:
            geracoes_estagnadas += 1
            if geracoes_estagnadas == GERACOES_PARADA:
                break

        # preserva n melhores
        n_melhores = 2
        elitismo(n_melhores)

        while(n_melhores < TAM_POP):
            seleciona_pais()
            cruza_pais()
            muta_filhos()

            nova_pop[n_melhores] = filhos[0].copy()
            nova_pop[n_melhores+1] = filhos[1].copy()
            
            n_melhores = n_melhores + 2

        pop = nova_pop.copy()
        nova_pop = [[(0, 0)] * TAM_CROMO for _ in range(TAM_POP)]

    imprime_melhor()
    plota_melhor(pop[int(nota_pop[0][0])])