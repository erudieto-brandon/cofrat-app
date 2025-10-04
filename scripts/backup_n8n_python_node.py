import re
import json

# Texto completo extraído do PDF (presume-se que vem no primeiro item)
texto_completo = items[0]['json']['text']

# Divide em linhas
linhas = texto_completo.split('\n')

agendamentos_finalizados = []
data_atual = ""
especialidade_atual = ""

# Padrões regex
regex_hora = re.compile(r'^\d{2}:\d{2}')
regex_data = re.compile(r'\d{2}/\d{2}/\d{4}')
# Aceita formatos com parênteses ou um bloco de 10/11 dígitos (fallback)
regex_telefone = re.compile(r'\(?\d{2}\)?\s*\d{4,5}-?\d{4}|\b\d{10,11}\b')
# prontuário: número (3+ dígitos) no final da linha
regex_record = re.compile(r'(\d{3,})\s*$')

# Detectores de cabeçalho/página (usados para ignorar datas de header)
HEADER_INDICATORS = ("Página", "Page", "SIMAH", "Agendamentos de Consultas", "COFRAT")

# Padrão que localiza nomes em MAIÚSCULAS (2-4 palavras)
name_pattern = re.compile(r'([A-ZÁÀÂÃÉÊÍÓÔÕÚÜÇ]{2,}(?:\s+[A-ZÁÀÂÃÉÊÍÓÔÕÚÜÇ]{2,}){1,3})')

# Prefixos a serem ignorados (removi "Data" e "Hora" daqui)
lixo_prefixos = ("Página", "SIMAH", "Agendamentos de Consultas", "COFRAT", "Sub - Total")

# DEBUG -> troque para True se quiser ver prints nos logs do node
DEBUG = True

# --- Controle de ignorar datas que são header (muito útil pro caso que você reportou) ---
IGNORE_HEADER_DATE = True
HEADER_CONTEXT_LINES = 3  # quantas linhas antes considerar para detectar header

def is_near_header(idx):
    """Retorna True se a linha idx estiver perto de algo que pareça cabeçalho de página."""
    for k in range(0, HEADER_CONTEXT_LINES):
        j = idx - k
        if j < 0:
            break
        ln = linhas[j]
        if any(ind in ln for ind in HEADER_INDICATORS):
            return True
    return False

def extrair_campos_linha_agendamento(linhas_agendamento):
    """
    Extrai os campos de um agendamento baseado na estrutura do bloco coletado.
    bloco esperado já contém as linhas iniciais: "Data: ..." e "Especialidade: ..." (se houver).
    """
    registro = {
        "date": "",
        "specialty": "",
        "time": "",
        "doctor": "",
        "insurance": "",
        "event": "",
        "patient": "",
        "patient_phone": "",
        "record": ""
    }
    
    for i, linha in enumerate(linhas_agendamento):
        if not linha:
            continue
        linha = linha.strip()
        
        # Captura Data / Especialidade caso estejam no bloco (útil quando foram injetadas)
        if linha.lower().startswith("data:"):
            registro["date"] = linha.split(":", 1)[1].strip()
            continue
        if linha.lower().startswith("especialidade:"):
            registro["specialty"] = linha.split(":", 1)[1].strip()
            continue
        
        # Se a linha começa com horário, interpreta o resto do bloco relativo a esse agendamento
        if regex_hora.match(linha):
            registro["time"] = linha[:5]  # HH:MM
            resto_linha = linha[5:].strip()
            # remove separadores iniciais (se houver)
            if resto_linha.startswith("-") or resto_linha.startswith(":"):
                resto_linha = resto_linha[1:].strip()
            # inicialmente tenta pegar o médico na mesma linha
            registro["doctor"] = resto_linha
            
            # Examina as próximas linhas do bloco para paciente / convênio / evento / telefones / prontuário
            tail = linhas_agendamento[i+1:i+10]  # olha até 9 linhas seguintes (ajustável)
            patient = ""
            phone = ""
            insurance = ""
            event = ""
            record = ""
            
            for t in tail:
                tln = t.strip()
                if not tln:
                    continue
                
                # procura telefone na linha
                mtel = regex_telefone.search(tln)
                if mtel:
                    found_phone = mtel.group()
                    before = tln[:mtel.start()].strip()
                    after = tln[mtel.end():].strip()
                    # Decidir se 'before' é paciente ou convênio
                    if before and not re.search(r'\d', before):
                        # Provavelmente paciente
                        if not patient:
                            patient = before
                        else:
                            if not insurance:
                                insurance = before
                    else:
                        # fallback: se tiver texto antes, usa como convênio
                        if before and not insurance:
                            insurance = before
                        elif after and not insurance:
                            insurance = after
                    phone = found_phone
                    continue
                
                low = tln.lower()
                # linhas rotuladas
                if low.startswith("paciente") or low.startswith("paciente:"):
                    parts = tln.split(":", 1)
                    candidate = parts[1].strip() if len(parts) > 1 else ""
                    if candidate:
                        patient = candidate
                        continue
                if any(k in low for k in ("convênio", "convenio", "plano", "seguradora", "empresa")):
                    parts = tln.split(":", 1)
                    insurance = parts[1].strip() if len(parts) > 1 else tln
                    continue
                
                # procura prontuário no final da linha
                mrec = regex_record.search(tln)
                if mrec:
                    record = mrec.group(1)
                    event_candidate = tln[:mrec.start()].strip()
                    # separa event/doctor se ambos estiverem presentes juntos
                    if event_candidate:
                        event = event_candidate
                    continue
                
                # heurísticas simples: primeira linha "limpa" (sem dígitos) costuma ser o paciente
                if not patient and not re.search(r'\d', tln):
                    # mas evita pegar linhas como "Data :" ou que contenham a palavra Data
                    if "data" not in tln.lower() and not tln.endswith(":"):
                        patient = tln
                        continue
                
                # se já temos paciente, usa a próxima linha como convênio se não parece evento
                if patient and not insurance and len(tln) < 80:
                    # evita confundir um possível nome de profissional com convênio por enquanto
                    insurance = tln
                    continue
                
                if not event:
                    event = tln
                    continue
            
            # Ajustes finais:
            # 1) se event contém um nome em MAIÚSCULAS (ex.: "CONSULTARICARDO SUSSUMU NAKAYA"),
            #    extrai esse nome como doctor e limpa o event
            if event:
                mname = name_pattern.search(event)
                if mname and not registro["doctor"]:
                    found_name = mname.group(1).strip()
                    registro["doctor"] = found_name
                    # remove a ocorrência encontrada do event (se possível)
                    event = event.replace(found_name, "").strip(" -:,.")
            
            # 2) se ainda não temos doctor, procura nas linhas tail um nome que combine com name_pattern
            if not registro["doctor"]:
                for t in tail:
                    tln = t.strip()
                    if not tln:
                        continue
                    m = name_pattern.search(tln)
                    if m:
                        candidate = m.group(1).strip()
                        # evita confundir com paciente
                        if candidate != patient:
                            registro["doctor"] = candidate
                            # caso esse nome tenha sido capturado como patient por engano, remove de patient
                            if patient and candidate in patient:
                                patient = patient.replace(candidate, "").strip(" -:,")
                            break
            
            registro["patient"] = patient
            registro["patient_phone"] = phone
            registro["insurance"] = insurance
            registro["event"] = event
            registro["record"] = record
            
            # Para cada horário só processamos a primeira ocorrência (como antes)
            break
    
    return registro

# Processamento principal
i = 0
while i < len(linhas):
    linha = linhas[i].strip()
    
    # Ignora linhas vazias
    if not linha:
        i += 1
        continue
    
    # Ignora linhas com prefixos de lixo (exclui Data/Hora para não descartar cabeçalhos úteis)
    if any(linha.startswith(prefixo) for prefixo in lixo_prefixos):
        i += 1
        continue
    
    # Detecta nova seção de data/especialidade (mais permissivo)
    # Se encontrar uma data, verifica se ela está perto de um header — se estiver, ignora
    if regex_data.search(linha):
        match_data = regex_data.search(linha)
        if match_data:
            # Detecta se a data está dentro do header (ex.: próxima a "Página", "SIMAH", etc.)
            if IGNORE_HEADER_DATE and is_near_header(i):
                if DEBUG:
                    print(f"Ignorando data de cabeçalho na linha {i}: {match_data.group()}")
                i += 1
                continue
            data_atual = match_data.group()
        
        # Procura especialidade na mesma linha ou nas próximas
        if "Especialidade" in linha:
            # exemplo: "Data: 01/01/2025 Especialidade: Cardiologia"
            try:
                especialidade_atual = linha.split("Especialidade:",1)[1].strip()
            except:
                especialidade_atual = linha.split("Especialidade",1)[1].strip()
        else:
            # Procura especialidade nas próximas 3 linhas (ou heurística)
            found_spec = False
            for j in range(i+1, min(i+4, len(linhas))):
                l2 = linhas[j].strip()
                if not l2:
                    continue
                if "Especialidade" in l2:
                    especialidade_atual = l2.split("Especialidade:",1)[1].strip() if ":" in l2 else l2
                    found_spec = True
                    break
                # heurística: linha curta, sem hora/telefone/dígitos -> pode ser especialidade,
                # MAS evita pegar linhas que contenham 'Data' ou terminem com ':' (como "Data :")
                if (not regex_hora.match(l2) and not regex_telefone.search(l2) 
                    and len(l2) < 60 and not re.search(r'\d', l2)
                    and "data" not in l2.lower() and not l2.endswith(":")):
                    especialidade_atual = l2
                    found_spec = True
                    break
            if not found_spec:
                # se não encontrou, preserva a especialidade anterior (não sobrescreve por linhas estranhas)
                pass
        
        if DEBUG:
            print(f"Nova seção - Data: {data_atual}, Especialidade: {especialidade_atual}")
        
        i += 1
        continue
    
    # Detecta início de agendamento (linha com horário)
    if regex_hora.match(linha):
        # Coleta o bloco do agendamento (insere Data/Especialidade atuais para o parser)
        bloco_agendamento = [f"Data: {data_atual}", f"Especialidade: {especialidade_atual}", linha]
        
        # Adiciona as próximas linhas até encontrar outro horário, "Sub - Total" ou linha de lixo
        j = i + 1
        linhas_coletadas = 0
        max_linhas = 12  # Limita para evitar coletar dados de outros agendamentos
        
        while j < len(linhas) and linhas_coletadas < max_linhas:
            proxima_linha = linhas[j].strip()
            
            # Para se encontrar outro horário, "Sub - Total", ou nova seção de data
            if (regex_hora.match(proxima_linha) or 
                "Sub - Total" in proxima_linha or
                regex_data.search(proxima_linha)):
                break
            
            # Ignora linhas de lixo
            if any(proxima_linha.startswith(prefixo) for prefixo in lixo_prefixos):
                j += 1
                continue
            
            # Adiciona linha não vazia
            if proxima_linha:
                bloco_agendamento.append(proxima_linha)
                linhas_coletadas += 1
            
            j += 1
        
        # Processa o bloco coletado
        agendamento = extrair_campos_linha_agendamento(bloco_agendamento)
        
        # Preenche date/specialty com o contexto caso o parser não tenha encontrado
        if not agendamento["date"]:
            agendamento["date"] = data_atual
        if not agendamento["specialty"]:
            agendamento["specialty"] = especialidade_atual
        
        # Só adiciona se tem dados mínimos
        if agendamento["time"] and (agendamento["doctor"] or agendamento["patient"]):
            agendamentos_finalizados.append(agendamento)
            
            if DEBUG:
                print(f"Agendamento: {agendamento['date']} {agendamento['time']} - {agendamento['doctor']} - {agendamento['patient']} ({agendamento['patient_phone']})")
        
        i = j - 1  # Ajusta para continuar da posição correta
    
    i += 1

if DEBUG:
    print(f"Total de agendamentos processados: {len(agendamentos_finalizados)}")

# Retorna no formato esperado pelo n8n
return [{"json": agendamento} for agendamento in agendamentos_finalizados]
