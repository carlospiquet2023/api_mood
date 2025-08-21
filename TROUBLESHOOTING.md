# 🔧 GUIA RÁPIDO DE SOLUÇÃO DE PROBLEMAS

**Desenvolvido por:** Carlos Antonio de Oliveira Piquet  
**Email:** carlospiquet.projetos@gmail.com  
**Contato:** +55 21 977434614  
**Especialista em sistemas educacionais e automação**

## ⚡ **DIAGNÓSTICO EXPRESSO (30 segundos)**

```powershell
# Teste completo do sistema
cd backend && python -c "
import sys; sys.path.insert(0, '.')
try:
    from services.moodle_client_simple import MoodleClient
    client = MoodleClient()
    print('✅ SISTEMA: Funcionando')
    print('✅ MOODLE:', 'Conectado' if client.test_connection() else '❌ ERRO')
except Exception as e:
    print('❌ ERRO CRÍTICO:', str(e))
"
```

## 🚨 **PROBLEMAS MAIS COMUNS**

### **1. "No module named 'magic'" (Windows)**
```powershell
# Solução:
pip install python-magic-bin
# OU
pip uninstall python-magic && pip install python-magic-bin
```

### **2. "Conexão com Moodle falhou"**
```env
# Verificar .env:
MOODLE_URL=https://moodle.instituicao.edu  # SEM barra final
MOODLE_TOKEN=abc123def456...              # Token completo
```

### **3. "Token inválido"**
```
Moodle Admin → Web services → Manage tokens
- Verificar expiração
- Confirmar usuário ativo
- Testar permissões
```

### **4. "Estudante não encontrado"**
```
✅ Nome correto: "João Silva"
❌ Nome incorreto: "joao_silva", "JOÃO SILVA"

# Teste manual:
python -c "
from backend.services.moodle_client_simple import MoodleClient
print(MoodleClient().search_users('João Silva'))
"
```

### **5. "Erro de upload"**
```
Verificar:
- Arquivo < 50MB
- Formato PDF válido
- Permissões pasta uploads/
- Espaço em disco
```

## 🛠️ **COMANDOS DE DIAGNÓSTICO**

### **Teste Conexão Moodle**
```bash
curl -X POST "https://seu-moodle.com/webservice/rest/server.php" \
  -d "wstoken=SEU_TOKEN" \
  -d "wsfunction=core_webservice_get_site_info" \
  -d "moodlewsrestformat=json"
```

### **Verificar Logs**
```bash
# Logs em tempo real
tail -f backend/logs/diploma_system.log

# Últimos erros
grep "ERROR" backend/logs/diploma_system.log | tail -10

# Estatísticas
grep "processado com sucesso" backend/logs/diploma_system.log | wc -l
```

### **Limpar Cache/Temp**
```bash
# Limpar uploads antigos
find uploads/ -name "*.pdf" -mtime +1 -delete

# Limpar temp
rm -rf temp/*

# Reiniciar sessão
rm -rf flask_session/
```

## 📋 **INFORMAÇÕES PARA SUPORTE**

Quando solicitar ajuda, forneça:

1. **Versão Python**: `python --version`
2. **Sistema**: Windows/Linux/macOS  
3. **URL Moodle**: (sem token)
4. **Erro completo**: Copy/paste da mensagem
5. **Logs**: Últimas 20 linhas do log
6. **Arquivo .env**: (sem credenciais)

## 🎯 **HEALTH CHECK COMPLETO**

```python
# Salvar como: test_sistema.py
import sys
sys.path.insert(0, 'backend')

def health_check():
    print("=== HEALTH CHECK SISTEMA DIPLOMAS ===")
    
    # 1. Imports
    try:
        from services.moodle_client_simple import MoodleClient
        from services.qr_generator import QRGenerator
        from services.pdf_processor import PDFProcessor
        print("✅ Imports: OK")
    except Exception as e:
        print(f"❌ Imports: {e}")
        return
    
    # 2. Configurações
    try:
        from config.settings import Config
        print(f"✅ Config: URL={Config.MOODLE_URL[:30]}...")
    except Exception as e:
        print(f"❌ Config: {e}")
        return
    
    # 3. Moodle
    try:
        client = MoodleClient()
        status = client.test_connection()
        print(f"✅ Moodle: {'Conectado' if status else 'Desconectado'}")
    except Exception as e:
        print(f"❌ Moodle: {e}")
    
    # 4. Serviços
    try:
        qr = QRGenerator()
        pdf = PDFProcessor()
        print("✅ Serviços: OK")
    except Exception as e:
        print(f"❌ Serviços: {e}")
    
    # 5. Arquivos
    import os
    dirs = ['uploads', 'output', 'temp', 'logs']
    for d in dirs:
        path = f"backend/{d}"
        if os.path.exists(path):
            print(f"✅ Diretório {d}: OK")
        else:
            print(f"❌ Diretório {d}: Não existe")
    
    print("=== HEALTH CHECK CONCLUÍDO ===")

if __name__ == "__main__":
    health_check()
```

## 📞 **CONTATO EMERGENCIAL**

Para problemas críticos em produção:

1. **Parar sistema**: `Ctrl+C` no terminal
2. **Verificar logs**: `backend/logs/diploma_system.log`
3. **Testar health**: `python test_sistema.py`
4. **Reportar problema**: Com logs e contexto completo

---

**⚡ LEMBRE-SE: 90% dos problemas são resolvidos verificando .env e logs! ⚡**

**Sistema desenvolvido por Carlos Antonio de Oliveira Piquet**  
*Email: carlospiquet.projetos@gmail.com | Contato: +55 21 977434614*
