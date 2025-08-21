# Sistema Automatizador de Diplomas com QR Code

Sistema profissional para automatização de diplomas com validação via QR Code integrado ao Moodle.

**Desenvolvido por:** Carlos Antonio de Oliv## 📄 Documentação Legal

Este projeto possui documentação legal completa e robusta:

### 🔒 Licença e Proteção
- **[LICENSE.md](./LICENSE.md)** - Licença proprietária com proteção de propriedade intelectual
- **[PRIVACY_POLICY.md](./PRIVACY_POLICY.md)** - Política de privacidade conforme LGPD/GDPR
- **[TERMS_OF_USE.md](./TERMS_OF_USE.md)** - Termos de uso e condições gerais

### ⚖️ Proteções Implementadas
- ✅ **Direitos Autorais** protegidos por lei
- ✅ **Anti-Plágio** com marcas d'água digitais
- ✅ **LGPD/GDPR** compliance total
- ✅ **ISO 27001/27701** conformidade
- ✅ **Penalidades** por uso não autorizado
- ✅ **Monitoramento** de violações 24/7

### 🚨 Aviso Legal
**Este software é propriedade exclusiva de Carlos Antonio de Oliveira Piquet.**  
Qualquer uso não autorizado, apropriação ou distribuição sem permissão constitui violação de direitos autorais e está sujeito a penalidades legais conforme descrito na licença.

## 🤝 Contribuições

Para contribuir com o projeto:
1. Leia os [Termos de Uso](./TERMS_OF_USE.md)
2. Entre em contato para autorização prévia
3. Assine acordo de confidencialidade se necessário
4. Fork autorizado do projeto
5. Implemente melhorias com documentação
6. Submeta Pull Request para revisão

**Nota:** Contribuições serão creditadas, mas os direitos autorais permanecem com o autor original.

## 📞 Suporte e Licenciamento

### 💬 Suporte Técnico
- **Email:** carlospiquet.projetos@gmail.com
- **WhatsApp:** +55 21 977434614
- **Documentação:** Veja arquivos INSTRUCOES.md e TROUBLESHOOTING.md
- **Issues:** GitHub Issues para bugs confirmados

### 💼 Licenciamento Comercial
Para uso comercial, integração em produtos proprietários ou licenças especiais:
- **Contato direto:** carlospiquet.projetos@gmail.com
- **Licenças disponíveis:** Educacional, Comercial, Enterprise
- **Suporte:** Desde básico até dedicado 24/7
- **Customizações:** Desenvolvimento sob demanda

## 🏆 Créditos e Reconhecimentos

**Autor Original e Proprietário:**  
Carlos Antonio de Oliveira Piquet
- Especialista em Sistemas Educacionais
- Desenvolvedor Full Stack
- Expert em Integração Moodle
- Consultor em Proteção de Dados

**Localização:** Rio de Janeiro, RJ - Brasil  
**Ano:** 2025mail:** carlospiquet.projetos@gmail.com  
**Contato:** +55 21 977434614  
**Especialista em sistemas educacionais e automação**

## 🚀 Funcionalidades

- **Upload em massa**: Processamento de arquivos PDF e ZIP
- **Extração inteligente**: Reconhecimento automático de nomes de estudantes
- **Integração Moodle**: Busca de dados via API Web Services ou conexão direta
- **QR Code**: Geração e inserção automática com dados verificáveis
- **Interface responsiva**: Design moderno com drag-and-drop
- **Verificação online**: Sistema de validação de autenticidade
- **Logs detalhados**: Monitoramento completo de operações

## 📋 Pré-requisitos

- Python 3.8+
- Moodle 3.9+ com Web Services habilitados
- MySQL/PostgreSQL (para conexão direta opcional)

## 🛠️ Instalação

### 1. Clonar o repositório
```bash
git clone <url-do-repositorio>
cd moodle_2025
```

### 2. Criar ambiente virtual
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

### 3. Instalar dependências
```bash
pip install -r requirements.txt
```

### 4. Configurar ambiente
```bash
copy .env.example .env
# Editar .env com suas configurações
```

### 5. Configurar Moodle

#### Opção A: Web Services (Recomendado)
1. Acesse **Administração do site > Plugins > Web services > Visão geral**
2. Habilite Web services
3. Crie um usuário de serviço com capacidades apropriadas
4. Gere um token de acesso
5. Configure o token no arquivo `.env`

#### Opção B: Plugin Moodle (Avançado)
1. Copie a pasta `moodle-plugin/diploma_data` para `[moodle]/local/`
2. Acesse **Administração do site > Notificações** para instalar
3. Configure permissões para o papel apropriado

## 🚀 Execução

### Desenvolvimento
```bash
cd backend
python app.py
```

### Produção
```bash
# Use um servidor WSGI como Gunicorn
pip install gunicorn
gunicorn --bind 0.0.0.0:5000 app:app
```

O sistema estará disponível em: `http://localhost:5000`

## 📖 Como Usar

### 1. Upload de Arquivos
- Acesse a interface web
- Faça upload de arquivos PDF individuais ou ZIP com múltiplos PDFs
- O sistema extrairá automaticamente os nomes dos estudantes

### 2. Processamento
- Selecione a posição do QR Code no documento
- Clique em "Processar Diplomas"
- Acompanhe o progresso em tempo real

### 3. Download
- Baixe os diplomas processados com QR Codes inseridos
- Cada QR Code contém dados verificáveis do estudante e curso

### 4. Verificação
- Use a URL de verificação para validar diplomas
- Escaneie o QR Code para verificação instantânea

## 🔧 Configuração Avançada

### Conexão Direta com Banco
Para melhor performance, configure conexão direta:

```env
MOODLE_DB_HOST=localhost
MOODLE_DB_NAME=moodle
MOODLE_DB_USER=usuario
MOODLE_DB_PASSWORD=senha
```

### Personalização de QR Code
```env
QR_CODE_SIZE=10          # Tamanho do QR Code
QR_CODE_BORDER=4         # Borda em pixels
QR_CODE_ERROR_CORRECTION=M  # L, M, Q, H
```

### Logging
```env
LOG_LEVEL=INFO           # DEBUG, INFO, WARNING, ERROR
LOG_FILE=logs/sistema.log
```

## 🏗️ Arquitetura

```
moodle_2025/
├── backend/
│   ├── app.py                 # Aplicação Flask principal
│   ├── config/
│   │   └── settings.py        # Configurações
│   ├── services/
│   │   ├── pdf_processor.py   # Processamento de PDF
│   │   ├── qr_generator.py    # Geração de QR Code
│   │   └── moodle_client.py   # Cliente Moodle
│   ├── utils/
│   │   ├── logger.py          # Sistema de logs
│   │   ├── validators.py      # Validações
│   │   └── session_manager.py # Gerenciamento de sessões
│   └── static/
│       └── index.html         # Interface web
├── moodle-plugin/
│   └── diploma_data/          # Plugin Moodle opcional
├── logs/                      # Logs do sistema
├── uploads/                   # Uploads temporários
└── output/                    # Arquivos processados
```

## 📝 API Endpoints

- `GET /` - Interface principal
- `POST /upload` - Upload de arquivos
- `POST /process-files` - Processamento de diplomas
- `GET /verify/<qr_data>` - Verificação de diploma
- `GET /health` - Status do sistema

## 🔒 Segurança

- Validação rigorosa de arquivos
- Sanitização de nomes de estudantes
- Tokens de acesso seguros
- Logs de auditoria
- Limpeza automática de arquivos temporários

## 🐛 Solução de Problemas

### Erro de conexão com Moodle
1. Verifique se Web services estão habilitados
2. Confirme se o token está correto
3. Teste conectividade de rede

### PDFs não processados
1. Verifique se os PDFs não estão corrompidos
2. Confirme se os nomes estão em formato legível
3. Veja os logs para detalhes do erro

### QR Code não gera
1. Verifique se os dados do estudante foram encontrados
2. Confirme configurações do Moodle
3. Teste com um usuário conhecido

## 📊 Monitoramento

O sistema gera logs detalhados em:
- `logs/diploma_system.log` - Log principal
- Console - Saída em tempo real durante desenvolvimento

Níveis de log:
- **DEBUG**: Informações detalhadas
- **INFO**: Operações normais
- **WARNING**: Situações de atenção
- **ERROR**: Erros que impedem operação

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para detalhes.

## 📞 Suporte

Para suporte técnico:
- Crie uma issue no repositório
- Verifique a documentação
- Consulte os logs do sistema

---

**Desenvolvido com ❤️ para automatização educacional**
