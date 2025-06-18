# Funcionalidades do Projeto: YouTube Channel Data Processor

## 🚀 Funcionalidades Principais

### ✅ Importação de Canais do YouTube
Permite importar informações detalhadas de um canal do YouTube a partir da URL do canal. Inclui dados como:
- Nome do canal
- ID do canal
- Descrição do canal

### ✅ Armazenamento no MongoDB
Todos os dados coletados (canal, playlists, vídeos e comentários) são armazenados de forma estruturada em um banco de dados MongoDB.

### ✅ Importação de Playlists
Para cada canal, todas as playlists públicas são listadas e importadas com:
- Nome da playlist
- ID da playlist
- Lista de vídeos

### ✅ Importação de Vídeos
Para cada playlist, o sistema busca todos os vídeos públicos com:
- Título
- Descrição
- Duração
- ID do vídeo

### ✅ Importação de Comentários
Para cada vídeo:
- Busca os comentários públicos disponíveis
- Inclui:
  - Nome do autor
  - Texto do comentário
  - Número de likes
  - Data de publicação

### ✅ Suporte a Respostas de Comentários
Além dos comentários principais, o sistema também coleta e exibe:
- Respostas aos comentários
- Autor da resposta
- Texto da resposta
- Número de likes
- Data de publicação

### ✅ Interface Web com Flask
O projeto possui uma interface web simples feita com Flask e Bootstrap, que permite:
- Listar os canais processados
- Visualizar playlists por canal
- Visualizar os vídeos de cada playlist
- Expandir comentários e respostas de cada vídeo de forma interativa

### ✅ Atualização de Dados
Se um canal já tiver sido processado antes, o sistema atualiza as informações existentes (playlists, vídeos e comentários), evitando duplicações.

---

## 🎥 Demonstração

![Demonstração](/assests/projeto.gif)