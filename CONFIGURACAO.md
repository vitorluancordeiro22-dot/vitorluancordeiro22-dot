# Perfil de Vitor Luan

Este pacote contém o README, o retrato animado e os painéis de contribuições.
O desenho em caracteres foi gerado a partir da fotografia fornecida, preservando
a silhueta e as asas. O visual de terminal foi inspirado no perfil
https://github.com/AVIVASHISHTA29/AVIVASHISHTA29; os scripts deste pacote são próprios.

## Publicação

1. Criar um repositório público chamado `vitorluancordeiro22-dot` na conta de mesmo nome.
2. Inicializar com um README e colocar os arquivos deste pacote na raiz.
3. Acompanhar `Actions → Atualizar perfil`. A primeira execução substitui os
   avisos de espera pelas estatísticas públicas reais.

Os avisos iniciais são intencionais: nenhuma estatística foi inventada.
O retrato é fixo. Somente os painéis de contribuições se atualizam diariamente.
A sequência máxima é calculada sobre o período do calendário retornado pelo GitHub.
Se a coleta falhar, o workflow falha e preserva os últimos arquivos publicados.

## Recriar o retrato

```sh
python -m pip install -r scripts/requirements.txt
python scripts/make_portrait.py
```

## Atualizar os números manualmente

```sh
python scripts/update_profile.py
```

Também é possível executar o workflow manualmente pelo botão `Run workflow`.
Não são necessárias chaves de serviços de IA.
