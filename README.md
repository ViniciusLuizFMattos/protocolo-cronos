# Protocolo Cronos: O Bunker Submerso

Jogo educativo de **Escape Room 2D Top-Down** feito em **Python + Pygame**, desenvolvido para o
**Projeto 2: Escape Room – Jogo Digital de Análise Combinatória** (Ensino Médio / 1º semestre de graduação).

Os gráficos e o áudio são **100% procedurais**: o jogo não depende de nenhuma imagem, som ou fonte externa.

**▶ Jogue no navegador (PC ou celular):** https://viniciusluizfmattos.github.io/protocolo-cronos/

## Narrativa

Você acorda na **Estação Submarina Acheron-4**, a 3.000 metros de profundidade, após um colapso estrutural.
Antes de morrer, a equipe anterior trancou cada setor com **protocolos criptográficos baseados em Análise
Combinatória** para conter um organismo abissal. Resolva os terminais, abra as portas hidráulicas e chegue à
cápsula de fuga antes que o tempo ou o sistema de contenção se esgotem. No fim, escolha: **fugir na cápsula**
ou **sobrecarregar o reator**.

## Regras do jogo

| Fase | Sala | Nível | Conteúdo | Acertos necessários | Banco |
|------|------|-------|----------|:------------------:|:-----:|
| 1 | Câmara de Eclusa | Fácil | Princípio Fundamental da Contagem | 1 | 10 |
| 2 | Laboratório Genético | Básico | Permutação Simples e com Repetição | 2 | 10 |
| 3 | Central de Sonar | Intermediário | Arranjo Simples | 2 | 10 |
| 4 | Câmara do Reator | Avançado | Combinação Simples | 3 | 10 |
| 5 | Sala da Cápsula | Difícil | Restrições e Integração de Conceitos | 4 | 10 |

**Total para vencer: 12 acertos (1 + 2 + 2 + 3 + 4).**

- **Sorteio sem repetição:** as questões de cada fase são sorteadas aleatoriamente do banco da fase e não se repetem
  na partida enquanto houver questões inéditas.
- **Acerto:** soma 1 acerto na fase e no placar global (X/12); o terminal fica verde. Ao atingir a meta da fase,
  a porta hidráulica se abre e o jogador avança.
- **Erro:** os acertos já conquistados **não** são perdidos. O terminal sobrecarrega (tremor de tela e flash vermelho),
  conta **+1 falha crítica**, desconta **20 s** do tempo e **sorteia imediatamente uma nova questão inédita do mesmo
  nível**, impedindo o chute na mesma pergunta. A resolução da questão errada é exibida para estudo.
- **Derrota:** o tempo global (**12 minutos**) acaba **ou** o jogador acumula **5 falhas críticas**.
- **Vitória:** concluir as 5 fases (12 acertos) e escolher um dos dois finais (Fugir na cápsula / Sobrecarregar o reator).
- **Nova partida:** as telas de Vitória e Derrota têm o botão **Iniciar Nova Partida** (ou tecla `Enter`/`R`), que
  reinicia estados, cronômetro e embaralha novamente os bancos.

## Controles

| Tecla | Ação |
|-------|------|
| `W A S D` ou setas | Mover o mergulhador |
| `E` | Acessar o terminal próximo (`[E] Acessar Terminal`) |
| `N` | Abrir/fechar o **bloco de notas** (também funciona dentro do terminal) |
| `Enter` | Enviar resposta / continuar |
| `Esc` | Sair do terminal (a questão do terminal é mantida); fora do terminal, pausa |
| `P` | Pausar / continuar (o cronômetro para). No pause, `Q` volta ao menu |
| `M` | Liga/desliga o som (também pelo botão de alto-falante no canto superior direito) |
| `T` | Liga/desliga os controles de toque na tela (útil para testar no PC) |

O **bloco de notas** é uma mini-calculadora: digite uma expressão como `8!/(3!*5!)` e pressione `Enter` (ou toque em
`=`) para ver o resultado. Aceita `+ - * / ^ ( )` e fatorial (`!`).

### No celular / tablet

O jogo roda no navegador do celular (versão web, abaixo). Os controles de toque aparecem automaticamente:

- **Joystick virtual** (canto inferior esquerdo) para andar;
- Botão **E** para acessar o terminal e botão **N** para o bloco de notas;
- **Teclado numérico na tela** dentro do terminal e **teclado de calculadora** no bloco de notas;
- Botões de **pausa** e **som** no topo da tela.

Use o celular **na horizontal** para a tela ficar maior.

## Instalação e execução

Requer Python 3.9+.

```bash
pip install pygame
python main.py
```

Para rodar os testes automáticos (validam as 50 respostas por cálculo independente, a alcançabilidade dos mapas e o
fluxo completo do jogo, sem abrir janela):

```bash
python test_headless.py
```

## Versão web (navegador e celular)

O mesmo `main.py` roda no navegador via [pygbag](https://pypi.org/project/pygbag/) (Python + Pygame compilados para
WebAssembly). Para testar localmente:

```bash
pip install pygbag
pygbag .
```

Depois abra `http://localhost:8000` no navegador (no celular, use o IP do PC na mesma rede Wi-Fi).

### Publicar no GitHub Pages (link para jogar no celular)

O repositório já inclui o workflow `.github/workflows/pages.yml`, que gera a versão web a cada `push` na branch `main`.

1. Suba o repositório para o GitHub.
2. Em **Settings → Pages**, em *Source*, escolha **GitHub Actions**.
3. Após o próximo `push`, o jogo fica disponível em `https://<seu-usuario>.github.io/<nome-do-repositorio>/`.

Na primeira abertura o navegador baixa o Python (alguns segundos) e pede um toque na tela para liberar o áudio.

## Estrutura do repositório

```
protocolo-cronos/
├── main.py                       # jogo completo (POO): estados, mapas, física, iluminação, áudio, HUD, toque
├── questoes.py                   # BANCO_QUESTOES: 50 questões (id, enunciado, resposta, resolucao)
├── test_headless.py              # testes automáticos
├── .github/workflows/pages.yml   # build web (pygbag) + publicação no GitHub Pages
└── README.md
```

### Arquitetura (`main.py`)

| Classe | Responsabilidade |
|--------|------------------|
| `Jogo` | Máquina de estados (menu, intro de fase, jogando, escolha final, vitória, derrota), regras e laço principal |
| `Fase` | Mapa, objetos sólidos (`pygame.Rect`), render estático do cenário |
| `Jogador` | Movimento WASD/setas, animação de caminhada e colisão por eixo |
| `Terminal` / `Porta` | Consoles (vermelho = pendente, verde = concluído) e porta hidráulica animada |
| `Iluminacao` | Camada de escuridão com lanterna acompanhando o personagem |
| `Desafio` | Interface do terminal: enunciado com *word wrap*, resposta, feedback e resolução |
| `BlocoNotas` | Rascunho com calculadora segura (parser próprio, sem `eval`) |
| `Baralho` | Sorteio sem repetição por fase |
| `Som` | Síntese de efeitos e trilha de sonar em memória (`math` + `array` + `pygame.mixer`), com `try/except` |

## Formato das questões

```python
{
    "id": "F4-01",
    "enunciado": "Válvulas do Reator: de 8 válvulas disponíveis, 3 devem ser abertas ...",
    "resposta": "56",
    "resolucao": "C(8,3) = 8! / (3! · 5!) = (8 × 7 × 6) / (3 × 2 × 1) = 336 / 6 = 56.",
}
```

Para adicionar questões, basta incluir novos itens na lista da fase em `BANCO_QUESTOES`.

## Licença

Projeto acadêmico. Use e adapte livremente para fins educacionais.
