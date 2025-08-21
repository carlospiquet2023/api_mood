# MANUAL TÉCNICO - Sistema Automatizador de Diplomas com QR Code

**Desenvolvido por:** Carlos Antonio de Oliveira Piquet  
**Email:** carlospiquet.projetos@gmail.com  
**Contato:** +55 21 977434614  
**Especialista em sistemas educacionais e automação**

## 📚 **1. VISÃO GERAL DO SISTEMA**ANUAL TÉCNICO - Sistema Automatizador de Diplomas com QR Code

## � **1. VISÃO GERAL DO SISTEMA**

### **Propósito**
Sistema automatizado para validação de estudantes via Moodle e geração de diplomas com QR codes de verificação. Elimina o processo manual de busca de dados acadêmicos e garante autenticidade dos documentos.

### **Arquitetura**
```
Frontend Web → Backend Flask → Plugin Moodle → Base de Dados Moodle
     ↓               ↓              ↓
  Upload PDFs → Extração Nomes → Validação Estudantes
     ↓               ↓              ↓
  QR Generation → PDF Processing → Download Final
```

### **Componentes Principais**
- **Backend Flask**: API REST, processamento de arquivos, integração Moodle
- **Plugin Moodle**: Webservices customizados para consulta de dados acadêmicos
- **Frontend Web**: Interface responsiva para upload e monitoramento
- **QR Generator**: Criação de códigos únicos de verificação

---

## 📦 **2. REQUISITOS E INSTALAÇÃO**

### **2.1 Pré-requisitos**
- Python 3.8+ 
- Moodle 4.0+ (com webservices habilitados)
- Windows/Linux/macOS
- 2GB RAM mínimo, 5GB espaço disco

### **2.2 Instalação do Backend**
```powershell
# 1. Clonar/baixar projeto
cd "C:\Users\pique\OneDrive\Área de Trabalho\moodle_2025"

# 2. Criar ambiente virtual
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
# source venv/bin/activate   # Linux/macOS

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar ambiente
copy .env.example .env
# Editar .env com configurações específicas
```

### **2.3 Dependências Críticas**
```pip-requirements
Flask==2.3.3               # Framework web
qrcode[pil]==7.4.2         # Geração QR codes
Pillow==10.0.0             # Processamento imagens
requests==2.31.0           # HTTP client para Moodle
python-dotenv==1.0.0       # Variáveis ambiente
cryptography==41.0.4       # Segurança/tokens
pypdf2==3.0.1              # Manipulação PDF
reportlab==4.0.4           # Criação PDF
python-magic-bin==0.4.14   # Detecção tipos arquivo
```

---

## 🔌 **3. INTEGRAÇÃO COM MOODLE**

### **3.1 Método A: Web Services Nativos (RECOMENDADO)**

#### **Passo 1: Habilitar Web Services**
```
Moodle Admin → Site administration → Advanced features
✅ Enable web services = Yes
```

#### **Passo 2: Criar Serviço Customizado**
```
Plugins → Web services → External services → Add
- Nome: "Sistema Diplomas"
- Short name: "diploma_system"
- Enabled: Yes
- Authorised users only: Yes
```

#### **Passo 3: Adicionar Funções Core**
```
Functions → Add functions:
✅ core_user_get_users_by_field
✅ core_course_get_enrolled_users  
✅ core_completion_get_activities_completion_status
✅ core_grades_get_grades
```

#### **Passo 4: Criar Usuário de Serviço**
```
Users → Accounts → Add a new user
- Username: diploma_service
- Password: [senha_forte]
- Email: diploma@instituicao.edu
- System role: Manager (ou role customizada)
```

#### **Passo 5: Gerar Token**
```
Plugins → Web services → Manage tokens → Add
- User: diploma_service
- Service: Sistema Diplomas
- Valid until: [data_futura]
- IP restriction: [opcional]
```

#### **Passo 6: Configurar Capacidades**
```sql
-- Permissões mínimas necessárias:
moodle/user:viewdetails
moodle/course:view
moodle/grade:view
webservice/rest:use
```

### **3.2 Método B: Plugin Customizado (AVANÇADO)**

#### **Instalação do Plugin**
```bash
# 1. Copiar plugin
cp -r moodle-plugin/diploma_data /caminho/moodle/local/

# 2. Instalar via Moodle
# Admin → Site administration → Notifications → Upgrade Moodle database
```

#### **Estrutura do Plugin**
```
local/diploma_data/
├── version.php           # Metadados e versão
├── db/services.php       # Definição webservices
└── classes/external.php  # Implementação APIs
```

#### **APIs Disponíveis**
```php
// Buscar dados completos do estudante
local_diploma_data_get_user_diploma_details($userid, $courseid)

// Pesquisar estudantes por nome/email  
local_diploma_data_search_users($search_term)

// Verificar conclusão de curso
local_diploma_data_verify_course_completion($userid, $courseid)

// Validar QR code de diploma
local_diploma_data_verify_diploma_qr($qr_data)
```

---

## ⚙️ **4. CONFIGURAÇÃO DO SISTEMA**

### **4.1 Arquivo .env (Configuração Principal)**
```env
# === CONFIGURAÇÕES MOODLE (OBRIGATÓRIO) ===
MOODLE_URL=https://moodle.instituicao.edu
MOODLE_TOKEN=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
MOODLE_SERVICE=diploma_system

# === CONFIGURAÇÕES APLICAÇÃO ===
FLASK_ENV=production
SECRET_KEY=sua_chave_secreta_super_segura_aqui
MAX_CONTENT_LENGTH=52428800  # 50MB
SESSION_PERMANENT_LIFETIME=3600  # 1 hora

# === PROCESSAMENTO ARQUIVOS ===
UPLOAD_FOLDER=uploads
OUTPUT_FOLDER=output
TEMP_FOLDER=temp
MAX_FILE_SIZE=50MB
ALLOWED_EXTENSIONS=pdf,zip

# === QR CODE CONFIGURAÇÕES ===
QR_CODE_SIZE=200
QR_CODE_BORDER=4
QR_CODE_VERSION=1
QR_CODE_ERROR_CORRECTION=M

# === LOGGING ===
LOG_LEVEL=INFO
LOG_FILE=logs/diploma_system.log
LOG_MAX_BYTES=10485760  # 10MB
LOG_BACKUP_COUNT=5

# === SEGURANÇA ===
VERIFICATION_SALT=salt_para_hash_verificacao
TOKEN_EXPIRY_HOURS=24
CSRF_ENABLED=true
```

### **4.2 Estrutura de Diretórios**
```
moodle_2025/
├── backend/
│   ├── app.py                 # Aplicação principal Flask
│   ├── config/
│   │   ├── settings.py        # Configurações centralizadas
│   │   └── __init__.py
│   ├── services/
│   │   ├── moodle_client.py   # Cliente Moodle (completo)
│   │   ├── moodle_client_simple.py  # Cliente básico
│   │   ├── pdf_processor.py   # Processamento PDF
│   │   ├── qr_generator.py    # Geração QR codes
│   │   └── __init__.py
│   ├── utils/
│   │   ├── logger.py          # Sistema logging
│   │   ├── validators.py      # Validações
│   │   ├── session_manager.py # Gestão sessões
│   │   └── __init__.py
│   ├── static/
│   │   └── index.html         # Interface web
│   ├── logs/                  # Logs aplicação
│   ├── uploads/               # Upload temporário
│   ├── output/                # Diplomas processados
│   └── temp/                  # Arquivos temporários
├── moodle-plugin/
│   └── diploma_data/          # Plugin Moodle
├── docs/                      # Documentação
├── tests/                     # Testes automatizados
├── requirements.txt           # Dependências Python
├── .env.example              # Modelo configuração
└── INSTRUCOES.md             # Este manual
```

---

## 🚀 **5. EXECUÇÃO E OPERAÇÃO**

### **5.1 Inicialização**
```powershell
# 1. Ativar ambiente virtual
cd "C:\Users\pique\OneDrive\Área de Trabalho\moodle_2025"
.\venv\Scripts\Activate.ps1

# 2. Verificar configurações
python -c "from backend.config.settings import Config; print('Config OK')"

# 3. Testar conexão Moodle
cd backend
python -c "
from services.moodle_client_simple import MoodleClient
client = MoodleClient()
print('Conexão Moodle:', 'OK' if client.test_connection() else 'FALHOU')
"

# 4. Iniciar aplicação
python app.py
```

### **5.2 Verificação de Saúde**
```bash
# Sistema rodando em: http://localhost:5000

# Endpoints de monitoramento:
GET /health              # Status geral
GET /api/moodle/test     # Teste conexão Moodle
GET /api/system/stats    # Estatísticas uso
```

### **5.3 Fluxo de Operação**

#### **A. Upload e Processamento**
1. **Acesso**: `http://localhost:5000`
2. **Upload**: PDF individual ou ZIP com múltiplos PDFs
3. **Extração**: Sistema extrai nomes dos arquivos/conteúdo
4. **Validação**: Busca estudantes no Moodle via API
5. **Correspondência**: Match manual se necessário
6. **Processamento**: Geração QR codes e inserção nos PDFs
7. **Download**: Arquivo ZIP com diplomas processados

#### **B. Verificação de Diploma**
1. **QR Code**: Contém JSON com dados do diploma
2. **Verificação**: URL pública para validar autenticidade
3. **Consulta**: Sistema verifica dados no Moodle
4. **Resposta**: Status de validade e informações acadêmicas

---

## � **6. ESTRUTURA DE DADOS**

### **6.1 Formato QR Code**
```json
{
  "student_id": 12345,
  "course_id": 67890,
  "completion_date": "2025-01-15",
  "verification_code": "abc123def456",
  "timestamp": 1705334400,
  "institution": "Instituição Educacional"
}
```

### **6.2 Resposta API Moodle**
```json
{
  "status": "success",
  "user": {
    "id": 12345,
    "username": "joao.silva",
    "firstname": "João",
    "lastname": "Silva",
    "fullname": "João Silva",
    "email": "joao.silva@email.com"
  },
  "courses": [
    {
      "id": 67890,
      "fullname": "Curso de Especialização",
      "shortname": "ESPECIALIZAÇÃO2025",
      "completion": {
        "completed": true,
        "timecompleted": 1705334400,
        "grade": 85.5
      }
    }
  ],
  "timestamp": 1705334400
}
```

### **6.3 Estrutura de Logs**
```
2025-01-15 14:30:25 | diploma_system | INFO | Sessão iniciada: sess_abc123
2025-01-15 14:30:26 | moodle_client | INFO | Conectado ao Moodle: https://moodle.edu
2025-01-15 14:30:30 | pdf_processor | INFO | Processando: diploma_joao_silva.pdf
2025-01-15 14:30:32 | qr_generator | INFO | QR gerado: qr_abc123def456.png
2025-01-15 14:30:35 | diploma_system | INFO | Diploma processado com sucesso
```

---

## 🛠️ **7. SOLUÇÃO DE PROBLEMAS**

### **7.1 Problemas de Conexão Moodle**

#### **Erro: "Conexão falhou"**
```bash
# Diagnóstico:
curl -X POST "https://moodle.edu/webservice/rest/server.php" \
  -d "wstoken=SEU_TOKEN" \
  -d "wsfunction=core_webservice_get_site_info" \
  -d "moodlewsrestformat=json"

# Verificações:
1. URL Moodle correto no .env
2. Token válido e não expirado
3. Web services habilitados
4. Firewall/proxy não bloqueando
```

#### **Erro: "Token inválido"**
```
1. Verificar token no .env
2. Confirmar usuário tem permissões
3. Verificar expiração do token
4. Recriar token se necessário
```

### **7.2 Problemas de Processamento**

#### **Erro: "Estudante não encontrado"**
```python
# Verificar formato dos nomes:
# ✅ Correto: "João Silva"
# ❌ Incorreto: "joao_silva", "JOÃO SILVA"

# Debug manual:
from backend.services.moodle_client_simple import MoodleClient
client = MoodleClient()
result = client.search_users("João Silva")
print(result)
```

#### **Erro: "Falha no upload"**
```
1. Verificar tamanho arquivo < 50MB
2. Confirmar formato PDF válido
3. Verificar permissões pasta uploads/
4. Confirmar espaço em disco
```

### **7.3 Problemas de Performance**

#### **Processamento lento**
```python
# Otimizações:
1. Reduzir tamanho QR codes (config)
2. Processar PDFs em lotes menores
3. Aumentar timeout requests Moodle
4. Verificar logs para gargalos
```

#### **Consumo memória alto**
```python
# Configurar no .env:
MAX_CONTENT_LENGTH=20971520  # 20MB em vez de 50MB
QR_CODE_SIZE=150             # Menor que 200
```

---

## 📊 **8. MONITORAMENTO E MANUTENÇÃO**

### **8.1 Logs do Sistema**
```bash
# Localização: backend/logs/diploma_system.log

# Monitoramento em tempo real:
tail -f backend/logs/diploma_system.log

# Análise de erros:
grep "ERROR" backend/logs/diploma_system.log

# Estatísticas de uso:
grep "Diploma processado" backend/logs/diploma_system.log | wc -l
```

### **8.2 Métricas de Performance**
```python
# Endpoint: GET /api/system/stats
{
  "uptime": "2 days, 5 hours",
  "processed_diplomas": 1247,
  "active_sessions": 5,
  "moodle_status": "connected",
  "disk_usage": "2.3GB",
  "memory_usage": "145MB"
}
```

### **8.3 Backup e Recuperação**
```bash
# Backup configurações:
cp .env .env.backup.$(date +%Y%m%d)

# Backup logs importantes:
tar -czf logs_backup_$(date +%Y%m%d).tar.gz backend/logs/

# Backup output (diplomas processados):
tar -czf diplomas_backup_$(date +%Y%m%d).tar.gz backend/output/
```

---

## 🔐 **9. SEGURANÇA**

### **9.1 Boas Práticas**
```env
# .env (produção):
FLASK_ENV=production
SECRET_KEY=chave_aleatoria_256_bits
CSRF_ENABLED=true
TOKEN_EXPIRY_HOURS=8  # Menor tempo
LOG_LEVEL=WARNING     # Menos verbose
```

### **9.2 Permissões Moodle**
```
Usuário diploma_service:
✅ moodle/user:viewdetails (somente leitura)
✅ moodle/course:view (somente leitura)
✅ webservice/rest:use (acesso API)
❌ moodle/user:update (não necessário)
❌ moodle/course:create (não necessário)
```

### **9.3 Validação de Arquivos**
```python
# Validações implementadas:
1. Extensão arquivo (PDF, ZIP)
2. Tamanho máximo (50MB)
3. Tipo MIME real
4. Integridade PDF
5. Sanitização nomes
```

---

## 📞 **10. SUPORTE E CONTATO**

### **10.1 Diagnóstico Rápido**
```bash
# Verificar se sistema está funcionando:
cd backend && python -c "
import sys
sys.path.insert(0, '.')
try:
    from app import app
    from services.moodle_client_simple import MoodleClient
    client = MoodleClient()
    print('✅ Sistema: OK')
    print('✅ Moodle:', 'OK' if client.test_connection() else '❌ FALHOU')
except Exception as e:
    print('❌ Erro:', str(e))
"
```

### **10.2 Informações para Suporte**
```
1. Versão Python: python --version
2. Sistema operacional: Windows/Linux/macOS
3. URL Moodle (sem token)
4. Logs relevantes: backend/logs/diploma_system.log
5. Arquivo .env (sem credenciais)
6. Descrição detalhada do problema
```

---

## ✅ **CHECKLIST DE IMPLANTAÇÃO**

### **Pré-produção**
- [ ] Python 3.8+ instalado
- [ ] Dependências instaladas (`pip install -r requirements.txt`)
- [ ] Arquivo .env configurado
- [ ] Conexão Moodle testada
- [ ] Permissões de usuário verificadas
- [ ] Upload de teste realizado

### **Produção**
- [ ] FLASK_ENV=production
- [ ] SECRET_KEY única e segura
- [ ] Logs configurados corretamente
- [ ] Backup automatizado
- [ ] Monitoramento ativo
- [ ] Documentação entregue à equipe

### **Pós-implantação**
- [ ] Treinamento usuários
- [ ] Testes de stress realizados
- [ ] Procedimentos de backup testados
- [ ] Plano de manutenção definido
- [ ] Contatos de suporte documentados

---

**🎓 SISTEMA DESENVOLVIDO POR CARLOS ANTONIO DE OLIVEIRA PIQUET 🎓**

*Email: carlospiquet.projetos@gmail.com | Contato: +55 21 977434614*  
*Especialista em sistemas educacionais e automação*

*Versão do Manual: 1.0 | Data: Agosto 2025*
