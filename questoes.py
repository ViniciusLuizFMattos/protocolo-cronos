# -*- coding: utf-8 -*-
"""
Protocolo Cronos: O Bunker Submerso
Banco de questões de Análise Combinatória (50 questões, 10 por fase).

Estrutura:
    BANCO_QUESTOES = { numero_da_fase: [ {id, enunciado, resposta, resolucao}, ... ] }

Notação usada nas resoluções:
    n!        fatorial de n
    A(n,p)    arranjo simples      = n! / (n-p)!
    C(n,p)    combinação simples   = n! / (p! · (n-p)!)
"""

BANCO_QUESTOES = {
    # ------------------------------------------------------------------
    # FASE 1 - Princípio Fundamental da Contagem (nível Fácil)
    # ------------------------------------------------------------------
    1: [
        {
            "id": "F1-01",
            "enunciado": "Painel de Fusíveis: para religar a eclusa é preciso escolher 1 dos 3 cabos de entrada, "
                         "1 dos 4 conectores intermediários e 1 das 2 chaves de saída. "
                         "Quantas configurações de religação são possíveis?",
            "resposta": "24",
            "resolucao": "São três etapas independentes (PFC): 3 × 4 × 2 = 24 configurações.",
        },
        {
            "id": "F1-02",
            "enunciado": "A trava da eclusa usa um código de 3 dígitos, cada um de 0 a 9, e os dígitos podem se repetir. "
                         "Quantos códigos diferentes existem?",
            "resposta": "1000",
            "resolucao": "Cada posição tem 10 opções: 10 × 10 × 10 = 10³ = 1000 códigos.",
        },
        {
            "id": "F1-03",
            "enunciado": "O painel genético do organismo abissal exibe cadeias de 4 bases nitrogenadas, cada uma escolhida "
                         "entre A, C, G e T (com repetição). Quantas cadeias distintas podem aparecer?",
            "resposta": "256",
            "resolucao": "4 opções para cada uma das 4 posições: 4 × 4 × 4 × 4 = 4^4 = 256 cadeias.",
        },
        {
            "id": "F1-04",
            "enunciado": "Rota de evacuação: da Eclusa ao Corredor B há 5 caminhos; do Corredor B à Sala de Máquinas há 3; "
                         "da Sala de Máquinas ao Hangar há 2. Quantas rotas diferentes levam da Eclusa ao Hangar?",
            "resposta": "30",
            "resolucao": "Etapas sucessivas e independentes: 5 × 3 × 2 = 30 rotas.",
        },
        {
            "id": "F1-05",
            "enunciado": "O cofre de ferramentas exige um código de 3 dígitos DISTINTOS, escolhidos de 0 a 9. "
                         "Quantos códigos são possíveis?",
            "resposta": "720",
            "resolucao": "1º dígito: 10 opções; 2º: 9 (não repete); 3º: 8. Logo 10 × 9 × 8 = 720.",
        },
        {
            "id": "F1-06",
            "enunciado": "Os cartões de acesso da tripulação têm 4 dígitos. O primeiro dígito não pode ser zero, "
                         "e os demais podem ser qualquer algarismo (com repetição). Quantos cartões distintos existem?",
            "resposta": "9000",
            "resolucao": "1º dígito: 9 opções (1 a 9); demais: 10 opções cada. 9 × 10 × 10 × 10 = 9000.",
        },
        {
            "id": "F1-07",
            "enunciado": "Os crachás da estação são numerados com todos os números de 3 algarismos (de 100 a 999). "
                         "Quantos crachás existem?",
            "resposta": "900",
            "resolucao": "Centena: 9 opções (1 a 9); dezena: 10; unidade: 10. 9 × 10 × 10 = 900 (também: 999 - 100 + 1).",
        },
        {
            "id": "F1-08",
            "enunciado": "No armário de equipamentos há 6 trajes de mergulho, 4 máscaras e 3 respiradores, todos compatíveis. "
                         "De quantas maneiras é possível montar um kit com 1 traje, 1 máscara e 1 respirador?",
            "resposta": "72",
            "resolucao": "Pelo PFC: 6 × 4 × 3 = 72 kits.",
        },
        {
            "id": "F1-09",
            "enunciado": "A placa do cofre central é formada por 2 letras escolhidas entre A, B, C, D e E (podendo repetir), "
                         "seguidas de 2 dígitos de 0 a 9 (podendo repetir). Quantas placas diferentes existem?",
            "resposta": "2500",
            "resolucao": "Letras: 5 × 5 = 25; dígitos: 10 × 10 = 100. Total: 25 × 100 = 2500 placas.",
        },
        {
            "id": "F1-10",
            "enunciado": "O painel de emergência tem 5 interruptores independentes, e cada um pode estar LIGADO ou DESLIGADO. "
                         "Quantas configurações diferentes o painel pode assumir?",
            "resposta": "32",
            "resolucao": "2 opções por interruptor: 2 × 2 × 2 × 2 × 2 = 2^5 = 32 configurações.",
        },
    ],

    # ------------------------------------------------------------------
    # FASE 2 - Permutação Simples e com Repetição (nível Básico)
    # ------------------------------------------------------------------
    2: [
        {
            "id": "F2-01",
            "enunciado": "Sequenciador Genético: 5 cápsulas de reagente, todas diferentes, serão alinhadas lado a lado "
                         "na bandeja do equipamento. De quantas maneiras podem ser alinhadas?",
            "resposta": "120",
            "resolucao": "Permutação simples de 5 elementos: P(5) = 5! = 5 × 4 × 3 × 2 × 1 = 120.",
        },
        {
            "id": "F2-02",
            "enunciado": "A senha do sequenciador é um anagrama da palavra CRONOS (a letra O aparece duas vezes). "
                         "Quantos anagramas distintos existem?",
            "resposta": "360",
            "resolucao": "6 letras com o O repetido 2 vezes: 6! / 2! = 720 / 2 = 360.",
        },
        {
            "id": "F2-03",
            "enunciado": "O nome da estação, ACHERON, tem 7 letras distintas. Quantos anagramas dessa palavra existem?",
            "resposta": "5040",
            "resolucao": "Permutação simples de 7 letras distintas: 7! = 5040.",
        },
        {
            "id": "F2-04",
            "enunciado": "Válvula de Contenção: o código de abertura é um anagrama da palavra ABISSAL "
                         "(A aparece 2 vezes e S aparece 2 vezes). Quantos códigos diferentes existem?",
            "resposta": "1260",
            "resolucao": "7!/(2!·2!) = 5040 / 4 = 1260 anagramas.",
        },
        {
            "id": "F2-05",
            "enunciado": "Seis válvulas numeradas e diferentes devem ser acionadas uma de cada vez, uma única vez cada, "
                         "para esvaziar a câmara de contenção. Quantas ordens de acionamento são possíveis?",
            "resposta": "720",
            "resolucao": "Permutação simples de 6 válvulas: 6! = 720 ordens.",
        },
        {
            "id": "F2-06",
            "enunciado": "Uma amostra do organismo possui uma sequência de 8 bases: 3 do tipo A, 3 do tipo T e 2 do tipo G. "
                         "Se as bases do mesmo tipo são idênticas, quantas sequências diferentes podem ser formadas?",
            "resposta": "560",
            "resolucao": "8! / (3! · 3! · 2!) = 40320 / (6 · 6 · 2) = 40320 / 72 = 560.",
        },
        {
            "id": "F2-07",
            "enunciado": "O console de pressão aceita como senha qualquer anagrama de PRESSAO (a letra S aparece 2 vezes). "
                         "Quantos anagramas diferentes existem?",
            "resposta": "2520",
            "resolucao": "7 letras com S repetido 2 vezes: 7! / 2! = 5040 / 2 = 2520.",
        },
        {
            "id": "F2-08",
            "enunciado": "A lista de módulos do bunker tem o código SUBMARINO, formado por 9 letras todas diferentes. "
                         "Quantos anagramas dessa palavra existem?",
            "resposta": "362880",
            "resolucao": "Permutação simples de 9 letras distintas: 9! = 362880.",
        },
        {
            "id": "F2-09",
            "enunciado": "O visor do sequenciador mostra números de 6 algarismos formados exatamente pelos dígitos "
                         "1, 1, 2, 2, 2 e 3. Quantos números diferentes podem aparecer?",
            "resposta": "60",
            "resolucao": "6! / (2! · 3!) = 720 / (2 · 6) = 720 / 12 = 60 números.",
        },
        {
            "id": "F2-10",
            "enunciado": "Sete cabos devem ser enfileirados na régua de conexão: 3 vermelhos, 2 azuis e 2 verdes. "
                         "Cabos de mesma cor são idênticos. De quantas formas a fila de cores pode ser montada?",
            "resposta": "210",
            "resolucao": "7! / (3! · 2! · 2!) = 5040 / (6 · 2 · 2) = 5040 / 24 = 210.",
        },
    ],

    # ------------------------------------------------------------------
    # FASE 3 - Arranjo Simples (nível Intermediário)
    # ------------------------------------------------------------------
    3: [
        {
            "id": "F3-01",
            "enunciado": "Radar de Sonar: 8 sinais diferentes foram captados e o radar vai ranquear os 3 mais fortes "
                         "(1º, 2º e 3º lugares). Quantos rankings distintos são possíveis?",
            "resposta": "336",
            "resolucao": "A ordem importa: A(8,3) = 8! / 5! = 8 × 7 × 6 = 336.",
        },
        {
            "id": "F3-02",
            "enunciado": "O console de pressão exige um código de 4 dígitos DISTINTOS escolhidos entre 0 e 9. "
                         "Quantos códigos podem ser formados?",
            "resposta": "5040",
            "resolucao": "A(10,4) = 10! / 6! = 10 × 9 × 8 × 7 = 5040.",
        },
        {
            "id": "F3-03",
            "enunciado": "Das 6 válvulas do circuito de lastro, uma será aberta primeiro e outra, diferente, será fechada em seguida. "
                         "De quantas maneiras podemos escolher a válvula a abrir e a válvula a fechar?",
            "resposta": "30",
            "resolucao": "Papéis diferentes (abrir e fechar são papéis distintos): A(6,2) = 6 × 5 = 30.",
        },
        {
            "id": "F3-04",
            "enunciado": "A senha do sonar usa 3 letras distintas escolhidas entre 7 letras disponíveis (A, B, C, D, E, F, G), "
                         "e a ordem importa. Quantas senhas existem?",
            "resposta": "210",
            "resolucao": "A(7,3) = 7! / 4! = 7 × 6 × 5 = 210.",
        },
        {
            "id": "F3-05",
            "enunciado": "Existem 9 posições de instalação no casco e serão instalados 5 sensores diferentes, "
                         "um em cada posição escolhida. De quantas formas os sensores podem ser distribuídos?",
            "resposta": "15120",
            "resolucao": "A(9,5) = 9! / 4! = 9 × 8 × 7 × 6 × 5 = 15120.",
        },
        {
            "id": "F3-06",
            "enunciado": "Entre 10 membros da equipe de resgate serão escolhidos um comandante, um vice-comandante "
                         "e um tesoureiro de suprimentos (cargos diferentes). Quantas chapas são possíveis?",
            "resposta": "720",
            "resolucao": "Cargos distintos -> ordem importa: A(10,3) = 10 × 9 × 8 = 720.",
        },
        {
            "id": "F3-07",
            "enunciado": "Usando apenas os algarismos 1, 2, 3, 4, 5 e 6, sem repetir, quantos códigos de 3 algarismos "
                         "o radar de sonar consegue exibir?",
            "resposta": "120",
            "resolucao": "A(6,3) = 6! / 3! = 6 × 5 × 4 = 120.",
        },
        {
            "id": "F3-08",
            "enunciado": "Há 12 amostras biológicas catalogadas. O sonar precisa analisar duas delas em sequência: "
                         "primeiro a amostra-alvo e depois a amostra-controle (função diferente). Quantas escolhas existem?",
            "resposta": "132",
            "resolucao": "A(12,2) = 12 × 11 = 132.",
        },
        {
            "id": "F3-09",
            "enunciado": "O painel de luzes do sonar tem 7 cores diferentes. Uma sequência de alerta usa 4 cores distintas, "
                         "acesas uma após a outra. Quantas sequências de alerta podem ser montadas?",
            "resposta": "840",
            "resolucao": "A(7,4) = 7! / 3! = 7 × 6 × 5 × 4 = 840.",
        },
        {
            "id": "F3-10",
            "enunciado": "Há 20 tanques de lastro numerados. Três deles serão designados, nesta ordem, para as funções "
                         "'esvaziar', 'pressurizar' e 'selar'. De quantas formas essa designação pode ser feita?",
            "resposta": "6840",
            "resolucao": "A(20,3) = 20 × 19 × 18 = 6840.",
        },
    ],

    # ------------------------------------------------------------------
    # FASE 4 - Combinação Simples (nível Avançado)
    # ------------------------------------------------------------------
    4: [
        {
            "id": "F4-01",
            "enunciado": "Válvulas do Reator: de 8 válvulas disponíveis, 3 devem ser abertas ao mesmo tempo "
                         "(a ordem de abertura não importa). Quantos grupos de 3 válvulas podem ser escolhidos?",
            "resposta": "56",
            "resolucao": "C(8,3) = 8! / (3! · 5!) = (8 × 7 × 6) / (3 × 2 × 1) = 336 / 6 = 56.",
        },
        {
            "id": "F4-02",
            "enunciado": "Entre 10 técnicos, é preciso formar uma equipe de manutenção de 4 pessoas para o núcleo do reator. "
                         "Quantas equipes diferentes podem ser formadas?",
            "resposta": "210",
            "resolucao": "C(10,4) = 10! / (4! · 6!) = (10 × 9 × 8 × 7) / 24 = 5040 / 24 = 210.",
        },
        {
            "id": "F4-03",
            "enunciado": "No quadro do reator há 12 fusíveis idênticos em aparência. Para o teste de carga, 2 deles serão "
                         "removidos. Quantos pares de fusíveis podem ser escolhidos?",
            "resposta": "66",
            "resolucao": "C(12,2) = 12! / (2! · 10!) = (12 × 11) / 2 = 66.",
        },
        {
            "id": "F4-04",
            "enunciado": "Do estoque de 7 amostras radioativas, 5 serão levadas ao laboratório. "
                         "De quantas maneiras podemos escolher essas 5 amostras?",
            "resposta": "21",
            "resolucao": "C(7,5) = C(7,2) = 7! / (5! · 2!) = (7 × 6) / 2 = 21.",
        },
        {
            "id": "F4-05",
            "enunciado": "Nove sobreviventes se encontram na sala do reator e cada par de pessoas troca um único aperto de mão "
                         "para se cumprimentar. Quantos apertos de mão ocorrem no total?",
            "resposta": "36",
            "resolucao": "Cada aperto corresponde a um par (ordem irrelevante): C(9,2) = (9 × 8) / 2 = 36.",
        },
        {
            "id": "F4-06",
            "enunciado": "O reator possui 15 tubos de refrigeração. Para a inspeção, 3 tubos serão selecionados "
                         "ao mesmo tempo. Quantas seleções diferentes são possíveis?",
            "resposta": "455",
            "resolucao": "C(15,3) = 15! / (3! · 12!) = (15 × 14 × 13) / 6 = 2730 / 6 = 455.",
        },
        {
            "id": "F4-07",
            "enunciado": "Quantos subconjuntos de exatamente 3 válvulas podem ser formados a partir de um painel "
                         "com 6 válvulas distintas?",
            "resposta": "20",
            "resolucao": "C(6,3) = 6! / (3! · 3!) = (6 × 5 × 4) / 6 = 20.",
        },
        {
            "id": "F4-08",
            "enunciado": "Há 9 baterias de reserva e o reator só precisa que 4 delas sejam ligadas em paralelo "
                         "(a ordem é irrelevante). Quantas escolhas de 4 baterias existem?",
            "resposta": "126",
            "resolucao": "C(9,4) = 9! / (4! · 5!) = (9 × 8 × 7 × 6) / 24 = 3024 / 24 = 126.",
        },
        {
            "id": "F4-09",
            "enunciado": "Oito estações de monitoramento do bunker devem ser ligadas duas a duas por um cabo, "
                         "de modo que cada par de estações tenha exatamente um cabo entre elas. Quantos cabos serão necessários?",
            "resposta": "28",
            "resolucao": "Um cabo por par de estações: C(8,2) = 8! / (2! · 6!) = (8 × 7) / 2 = 28.",
        },
        {
            "id": "F4-10",
            "enunciado": "Uma comissão de contenção será formada por 2 cientistas escolhidos entre 5 e 2 técnicos "
                         "escolhidos entre 6. Quantas comissões diferentes podem ser formadas?",
            "resposta": "150",
            "resolucao": "Cientistas: C(5,2) = 10. Técnicos: C(6,2) = 15. Pelo PFC: 10 × 15 = 150 comissões.",
        },
    ],

    # ------------------------------------------------------------------
    # FASE 5 - Restrições e Integração de Conceitos (nível Difícil)
    # ------------------------------------------------------------------
    5: [
        {
            "id": "F5-01",
            "enunciado": "Console da Cápsula: 5 sobreviventes entram em fila na cápsula de fuga, mas dois deles, Ana e Bruno, "
                         "precisam ficar SEMPRE juntos (lado a lado, em qualquer ordem). De quantas formas a fila pode ser formada?",
            "resposta": "48",
            "resolucao": "Trate Ana e Bruno como um bloco: 4 elementos -> 4! = 24 filas. "
                         "Dentro do bloco, 2! = 2 ordens. Total: 24 × 2 = 48.",
        },
        {
            "id": "F5-02",
            "enunciado": "Agora, na mesma cápsula, os 5 sobreviventes entram em fila, mas Ana e Bruno NÃO podem ficar lado a lado. "
                         "Quantas filas são possíveis?",
            "resposta": "72",
            "resolucao": "Total sem restrição: 5! = 120. Filas com Ana e Bruno juntos: 4! × 2! = 48. "
                         "Filas válidas: 120 - 48 = 72.",
        },
        {
            "id": "F5-03",
            "enunciado": "O Computador Central gera códigos PAR de 4 algarismos distintos (de 0 a 9, o primeiro não pode ser zero). "
                         "Quantos códigos desse tipo existem?",
            "resposta": "2296",
            "resolucao": "Termina em 0: 9 × 8 × 7 = 504. "
                         "Termina em 2, 4, 6 ou 8 (4 opções): o 1º dígito não pode ser 0 nem o último (8 opções), "
                         "o 2º tem 8 e o 3º tem 7 -> 4 × 8 × 8 × 7 = 1792. Total: 504 + 1792 = 2296.",
        },
        {
            "id": "F5-04",
            "enunciado": "Painel de Contenção: uma equipe de 4 pessoas será escolhida entre 6 homens e 4 mulheres, "
                         "com a exigência de ter PELO MENOS 1 mulher. Quantas equipes são possíveis?",
            "resposta": "195",
            "resolucao": "Total de equipes: C(10,4) = 210. Equipes sem nenhuma mulher (só homens): C(6,4) = 15. "
                         "Com pelo menos 1 mulher: 210 - 15 = 195.",
        },
        {
            "id": "F5-05",
            "enunciado": "O código final do reator é um anagrama de BUNKER (6 letras distintas) que COMEÇA por vogal. "
                         "Quantos códigos desse tipo existem?",
            "resposta": "240",
            "resolucao": "A 1ª letra é vogal: 2 opções (U ou E). As outras 5 letras ocupam 5 posições: 5! = 120. "
                         "Total: 2 × 120 = 240.",
        },
        {
            "id": "F5-06",
            "enunciado": "Núcleo de Energia: 3 engenheiras e 4 engenheiros formarão uma fila de 7 pessoas diante do núcleo. "
                         "As 3 engenheiras devem ficar JUNTAS. De quantas formas a fila pode ser organizada?",
            "resposta": "720",
            "resolucao": "Bloco das 3 engenheiras + 4 engenheiros = 5 elementos -> 5! = 120. "
                         "Dentro do bloco: 3! = 6. Total: 120 × 6 = 720.",
        },
        {
            "id": "F5-07",
            "enunciado": "Das 6 pessoas a bordo, uma equipe de 3 será enviada ao reator. Duas delas, Carlos e Diana, "
                         "são rivais e NÃO podem ir juntas na mesma equipe. Quantas equipes são possíveis?",
            "resposta": "16",
            "resolucao": "Total de equipes: C(6,3) = 20. Equipes com Carlos e Diana juntos: falta 1 pessoa entre as 4 restantes -> C(4,1) = 4. "
                         "Equipes válidas: 20 - 4 = 16.",
        },
        {
            "id": "F5-08",
            "enunciado": "A senha da cápsula é formada por 3 letras DISTINTAS escolhidas entre A, B, C, D e E, "
                         "seguidas de 2 dígitos DISTINTOS de 0 a 9. Quantas senhas existem?",
            "resposta": "5400",
            "resolucao": "Letras: A(5,3) = 5 × 4 × 3 = 60. Dígitos: A(10,2) = 10 × 9 = 90. Pelo PFC: 60 × 90 = 5400.",
        },
        {
            "id": "F5-09",
            "enunciado": "Entre 7 técnicos, escolhe-se uma equipe de 3 para o reator e, dentre os 4 que sobraram, "
                         "uma equipe de 2 para a cápsula. De quantas maneiras essa divisão pode ser feita?",
            "resposta": "210",
            "resolucao": "Equipe do reator: C(7,3) = 35. Equipe da cápsula (entre os 4 restantes): C(4,2) = 6. "
                         "Pelo PFC: 35 × 6 = 210.",
        },
        {
            "id": "F5-10",
            "enunciado": "O Console da Cápsula só aceita números de 3 algarismos DISTINTOS e MAIORES que 500. "
                         "Quantos números desse tipo existem?",
            "resposta": "360",
            "resolucao": "Centena: 5, 6, 7, 8 ou 9 -> 5 opções. Dezena: 9 opções (qualquer algarismo, menos o da centena). "
                         "Unidade: 8 opções. Total: 5 × 9 × 8 = 360.",
        },
    ],
}
